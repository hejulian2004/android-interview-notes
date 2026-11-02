import test, {after} from 'node:test';
import assert from 'node:assert/strict';
import {readFile, readdir, cp, mkdtemp, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {parseMarkdownSources,compatiblePath} from '../engine/parser.mjs';

const repository=new URL('../../',import.meta.url);
async function filesAt(directory) {
  const result=[];
  async function walk(path) {
    for(const entry of await readdir(new URL(path+'/',repository),{withFileTypes:true})) {
      const name=path+'/'+entry.name;
      if(entry.isDirectory())await walk(name);
      else if(compatiblePath(name)) {
        const content=await readFile(new URL(name,repository),'utf8');
        const sha=createHash('sha1').update(`blob ${Buffer.byteLength(content)}\0`).update(content).digest('hex');
        result.push({path:name,content,sha});
      }
    }
  }
  await walk(directory);return result;
}
const files=(await Promise.all(['docs','questions','supplements'].map(filesAt))).flat();
const snapshot={version:1,revision:'a'.repeat(40),files,fetchedAt:'2026-11-02T00:00:00Z'};
const assembly=await mkdtemp(join(tmpdir(),'study-server-catalog-'));
await cp(new URL('../src/',import.meta.url),assembly,{recursive:true});
await cp(new URL('../engine/',import.meta.url),join(assembly,'engine'),{recursive:true});
after(()=>rm(assembly,{recursive:true,force:true}));
const {parseServerCatalog,loadCatalog,createCatalogFollower}=await import(pathToFileURL(join(assembly,'server-catalog.mjs')));

test('authenticated parser preserves all 491 question IDs, answers and context',()=>{
  const catalog=parseServerCatalog(snapshot);
  assert.equal(catalog.questions.length,491);assert.equal(catalog.documents.length,10);
  // Captured with the published parser at b49530151aac621a1f178425b78510d8900d21af,
  // using the same 491 source records and revision='a'.repeat(40). This constant
  // detects changes to IDs, answers, evidence context, topic labels and source URLs.
  const hash=createHash('sha256').update(JSON.stringify(catalog.questions)).digest('hex');
  assert.equal(hash,'7b3ee8572ae043ad2ac7e39b901e928c1e341e4ba34ed0eb10bec9e924374176');
  assert.deepEqual(parseMarkdownSources(files).questions.map(q=>q.id),catalog.questions.map(q=>q.id));
});
test('catalog reads and refreshes use only the injected same-origin API',async()=>{
  const calls=[];
  const request=async(path,options)=>{calls.push([path,options.method]);return snapshot;};
  assert.equal((await loadCatalog({request})).questions.length,491);
  await loadCatalog({request,force:true});
  assert.deepEqual(calls,[['catalog','GET'],['catalog/refresh','POST']]);
});
test('authentication and upstream failures are never replaced with a public snapshot',async()=>{
  await assert.rejects(loadCatalog({request:async()=>{throw new Error('unauthenticated');}}),/unauthenticated/);
  assert.throws(()=>parseServerCatalog({...snapshot,files:[snapshot.files[0],snapshot.files[0]]}),/无效题库文件/);
  assert.throws(()=>parseServerCatalog({...snapshot,revision:'main'}),/无效题库版本/);
});
test('stale server data is usable immediately and its background check is disclosed',async()=>{
  const statuses=[];
  const catalog=await loadCatalog({request:async()=>({...snapshot,cacheStatus:'stale',refreshing:true}),onStatus:status=>statuses.push(status)});
  assert.equal(catalog.questions.length,491);assert.equal(catalog.refreshing,true);
  assert.equal(statuses.at(-1).phase,'cached');assert.match(statuses.at(-1).message,/缓存.*后台检查/);
  assert.doesNotMatch(statuses.at(-1).message,/已更新|最新/);
  await loadCatalog({request:async()=>({...snapshot,cacheStatus:'stale',refreshing:false,warning:'GitHub 暂不可用，使用服务器成功缓存'}),onStatus:status=>statuses.push(status)});
  assert.equal(statuses.at(-1).phase,'offline');assert.match(statuses.at(-1).message,/成功缓存/);
});
function fakeTimers(){let id=0;const tasks=new Map();return {tasks,schedule:(run,ms)=>{tasks.set(++id,{run,ms});return id;},cancel:key=>tasks.delete(key),async run(){const [key,task]=tasks.entries().next().value;tasks.delete(key);await task.run();}};}
test('background followup uses ordinary GET semantics, stops when complete and is bounded',async()=>{
  const timers=fakeTimers(),seen=[],calls=[];
  const follower=createCatalogFollower({...timers,load:async options=>{calls.push(options);return {revision:'b'.repeat(40),refreshing:false};},onCatalog:value=>seen.push(value)});
  follower.start({revision:'a'.repeat(40),refreshing:true});assert.equal(timers.tasks.size,1);assert.equal([...timers.tasks.values()][0].ms,2000);
  await timers.run();assert.equal(seen.length,1);assert.equal(seen[0].revision,'b'.repeat(40));assert.equal(calls[0].force,false);assert.equal(timers.tasks.size,0);
  const bounded=fakeTimers(),statuses=[];let count=0;
  const pending=createCatalogFollower({...bounded,load:async()=>{count++;return {refreshing:true};},onStatus:value=>statuses.push(value)});
  pending.start({refreshing:true});await bounded.run();await bounded.run();await bounded.run();
  assert.equal(count,3);assert.equal(bounded.tasks.size,0);assert.match(statuses.at(-1).message,/点击.*更新题库/);assert.doesNotMatch(statuses.at(-1).message,/后台检查.*中/);
});
test('cancelled or superseded in-flight followups cannot restore old content',async()=>{
  const timers=fakeTimers(),seen=[];let release;
  const follower=createCatalogFollower({...timers,load:()=>new Promise(resolve=>{release=resolve;}),onCatalog:value=>seen.push(value)});
  follower.start({refreshing:true});const running=timers.run();follower.cancel();release({revision:'b'.repeat(40),refreshing:false});await running;
  assert.deepEqual(seen,[]);assert.equal(timers.tasks.size,0);
  follower.start({refreshing:true});assert.equal(timers.tasks.size,1);follower.start({refreshing:false});assert.equal(timers.tasks.size,0);
});
test('failed followups preserve the current catalog and stop after the retry budget',async()=>{
  const timers=fakeTimers(),seen=[],statuses=[];
  const follower=createCatalogFollower({...timers,load:async()=>{throw new Error('network');},onCatalog:value=>seen.push(value),onStatus:value=>statuses.push(value)});
  follower.start({revision:'a'.repeat(40),refreshing:true});await timers.run();await timers.run();await timers.run();
  assert.deepEqual(seen,[]);assert.equal(timers.tasks.size,0);assert.ok(statuses.some(value=>value.warning?.includes('进度已保留')));
});

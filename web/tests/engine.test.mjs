import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {parseMarkdownSources,loadCatalog,CACHE_KEY,CHECK_INTERVAL,compatiblePath} from '../engine/index.mjs';
const snapshot=JSON.parse(fs.readFileSync(new URL('../engine/snapshot.json',import.meta.url)));
const catalog=parseMarkdownSources(snapshot.files,{revision:snapshot.revision});
function memoryStorage(initial={}) {const map=new Map(Object.entries(initial));return {getItem:k=>map.get(k)??null,setItem:(k,v)=>map.set(k,v),map};}
const response=(body,status=200)=>({ok:status>=200&&status<300,status,json:async()=>body,text:async()=>body});
const NOW=1800000000000;

test('exact real content counts; no TOC repetitions or invented SDK/QUIC questions',()=>{
  assert.equal(catalog.questions.length,371); assert.equal(catalog.documents.length,7);
  const kinds=catalog.questions.reduce((o,q)=>(o[q.kind]=(o[q.kind]||0)+1,o),{});
  assert.deepEqual(kinds,{guide:239,public:116,supplement:16});
  for(const [name,count] of [['android-interview-handbook.md',129],['feedline-android-deep-dive.md',20],['flutter-interview-guide.md',52],['word-crush-android-xml-guide.md',38]]) {
    assert.equal(catalog.questions.filter(q=>q.path===`docs/${name}`).length,count);
  }
  assert.equal(new Set(catalog.questions.map(q=>q.id)).size,371);
  assert.equal(catalog.questions.filter(q=>/sdk-source|quic-source|ai-code/.test(q.path)).length,0);
});
test('answers keep final followups and fact/version/evidence limits',()=>{
  const find=(suffix,number)=>catalog.questions.find(q=>q.path.endsWith(suffix)&&q.number===number);
  const ffi=find('android-interview-handbook.md','N03');
  assert.match(ffi.answerMarkdown,/命令提交与 pending 注册的先后次序/);
  assert.match(ffi.answerMarkdown,/不应扩大为所有 SDK API/);
  assert.match(ffi.contextMarkdown,/通用原理／设计建议/);
  assert.doesNotMatch(ffi.answerMarkdown,/### N04/);
  assert.match(find('flutter-interview-guide.md','Q01').answerMarkdown,/易错/);
  assert.match(find('flutter-interview-guide.md','Q01').contextMarkdown,/5aba1d83405d53bdabd3807c76139489d17d7e6a/);
  assert.match(find('word-crush-android-xml-guide.md','Q38').contextMarkdown,/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/);
  assert.match(find('feedline-android-deep-dive.md','A01').contextMarkdown,/不是可以直接背诵的个人经历/);
  const publicQ=catalog.questions.find(q=>q.number==='Q001');
  assert.match(publicQ.answerMarkdown,/仅帖子日期/);assert.match(publicQ.answerMarkdown,/不是原帖原题/);
  assert.match(publicQ.answerMarkdown,/不是企业标准答案/);
});
test('source links honor explicit anchors and GitHub heading slug',()=>{
  const guide=catalog.questions.filter(q=>q.kind==='guide');
  assert.match(guide.find(q=>q.number==='N01').sourceUrl,/#q-n01$/);
  assert.match(guide.find(q=>q.path.includes('flutter')&&q.number==='Q01').sourceUrl,/#q01$/);
  assert.match(guide.find(q=>q.path.includes('word-crush')&&q.number==='Q01').sourceUrl,/#q01$/);
  assert.match(decodeURIComponent(guide.find(q=>q.number==='A01').sourceUrl),/#a01-为什么项目-readme-写-room-但你说-sqliteopenhelper$/);
});
test('stable IDs survive reorder; fenced code headings and TOC are ignored',()=>{
  const blocks=['### Q01 One\n\nAnswer one and followup.','### Q02 Two\n\nAnswer two and final boundary.'];
  const make=blocks=>parseMarkdownSources([{path:'docs/new-guide.md',content:'# New Guide\n\nPublic boundary.\n\n- [Q01 One](#q01)\n\n```md\n### Q99 Fake\n```\n\n## Topic\n\n'+blocks.join('\n\n')}]);
  const a=make(blocks),b=make([...blocks].reverse());
  assert.equal(a.questions.length,2);assert.deepEqual(a.questions.map(q=>q.id).sort(),b.questions.map(q=>q.id).sort());
  assert.match(b.questions.find(q=>q.number==='Q02').answerMarkdown,/final boundary/);
  assert.ok(compatiblePath('docs/new-guide.md')); assert.ok(!compatiblePath('.env'));assert.ok(!compatiblePath('docs/../secret.md'));
});
test('unchanged main requires one credential-free request and caches timestamp',async()=>{
  const storage=memoryStorage(),calls=[];
  const c=await loadCatalog({snapshot,storage,now:NOW,fetchImpl:async(url,options)=>{calls.push({url,options});return response({sha:snapshot.revision});}});
  assert.equal(c.questions.length,371);assert.equal(c.origin,'github');assert.equal(calls.length,1);
  assert.equal(calls[0].options.credentials,'omit');assert.equal(c.checkedAt,NOW);
  await loadCatalog({snapshot,storage,now:NOW+CHECK_INTERVAL-1,fetchImpl:async()=>{throw new Error('TTL should avoid network');}});
  assert.equal(calls.length,1);
});
test('changed main discovers new Markdown, downloads changed blobs only, removes deleted questions',async()=>{
  const sha='1'.repeat(40),fresh='2'.repeat(40),calls=[];
  const keep=snapshot.files.filter(f=>!f.path.endsWith('flutter-interview-guide.md'));
  const newFile={path:'docs/new-generated-guide.md',sha:fresh,content:'# New\n\nEvidence boundary.\n\n## Section\n\n### Q99 New question\n\nAnswer with a boundary and a followup.'};
  const tree=[...keep.map(f=>({type:'blob',path:f.path,sha:f.sha,size:f.content.length})),{type:'blob',path:newFile.path,sha:fresh,size:200}];
  const storage=memoryStorage();
  const c=await loadCatalog({snapshot,storage,now:NOW,fetchImpl:async(url)=>{
    calls.push(url);if(url.endsWith('/commits/main'))return response({sha});if(url.includes('/git/trees/'))return response({tree,truncated:false});
    assert.ok(url.includes('/'+sha+'/docs/new-generated-guide.md'));return response(newFile.content);
  }});
  assert.equal(c.revision,sha);assert.equal(c.questions.length,320);assert.equal(c.documents.length,7);assert.equal(calls.length,3);
  assert.equal(c.questions.filter(q=>q.path.includes('flutter-interview-guide')).length,0);
  assert.ok(c.questions.some(q=>q.id==='docs/new-generated-guide.md#q99'));
  const ids=new Set(c.questions.map(q=>q.id)); assert.ok(!ids.has('docs/flutter-interview-guide.md#q01')); // UI must report retained orphan progress separately.
});
test('rate limit and partial failed update keep successful cache and allow manual retry',async()=>{
  const storage=memoryStorage({[CACHE_KEY]:JSON.stringify({...snapshot,checkedAt:NOW-CHECK_INTERVAL-1,fetchedAt:'2026-11-01T00:00:00Z'})});
  const phases=[];
  const c=await loadCatalog({snapshot,storage,now:NOW,onStatus:s=>phases.push(s.phase),fetchImpl:async()=>response({},403)});
  assert.equal(c.questions.length,371);assert.equal(c.revision,snapshot.revision);assert.match(c.warning,/HTTP 403/);assert.equal(phases.at(-1),'offline');
  assert.equal(JSON.parse(storage.map.get(CACHE_KEY)).fetchedAt,'2026-11-01T00:00:00Z');
  const retry=await loadCatalog({snapshot,storage,force:true,now:NOW+1,fetchImpl:async()=>response({sha:snapshot.revision})});
  assert.equal(retry.warning,'');assert.equal(retry.origin,'github');
  const partial=await loadCatalog({snapshot,storage,force:true,now:NOW+2,fetchImpl:async(url)=>{
    if(url.endsWith('/commits/main'))return response({sha:'3'.repeat(40)});
    if(url.includes('/git/trees/'))return response({tree:[{type:'blob',path:'docs/future.md',sha:'4'.repeat(40),size:100}],truncated:false});
    throw new Error('simulated network failure');
  }});
  assert.equal(partial.questions.length,371);assert.equal(partial.revision,snapshot.revision);assert.match(partial.warning,/simulated network failure/);
});
test('first offline uses dated bundled snapshot; storage failure still usable',async()=>{
  const storage={getItem(){throw new Error('blocked');},setItem(){throw new Error('quota');}};
  const c=await loadCatalog({snapshot,storage,now:NOW,fetchImpl:async()=>{throw new Error('offline');}});
  assert.equal(c.origin,'snapshot');assert.equal(c.generatedAt,snapshot.generatedAt);assert.ok(c.warning);assert.equal(c.questions.length,371);
});
test('SecurityError when reading global localStorage does not prevent snapshot usage',async()=>{
  Object.defineProperty(globalThis,'localStorage',{configurable:true,get(){throw new Error('SecurityError');}});
  try {const c=await loadCatalog({snapshot,now:NOW,fetchImpl:async()=>{throw new Error('offline');}});assert.equal(c.questions.length,371);}finally{delete globalThis.localStorage;}
});

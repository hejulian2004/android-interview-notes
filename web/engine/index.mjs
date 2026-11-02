/** Legacy read-only loader kept for migration tests; not included in authenticated builds. */
import { parseMarkdownSources, compatiblePath } from './parser.mjs';
export { REPOSITORY, TOPICS, parseMarkdownSources, compatiblePath } from './parser.mjs';
import { REPOSITORY } from './parser.mjs';
export const CACHE_KEY = 'android-study:catalog:v1';
export const CHECK_INTERVAL = 30 * 60 * 1000;
const API = `https://api.github.com/repos/${REPOSITORY}`;
const RAW = `https://raw.githubusercontent.com/${REPOSITORY}`;
const MAX_FILES = 400;
const MAX_FILE_BYTES = 1500000;
const MAX_TOTAL_CHARS = 6000000;
const snapshotUrl = new URL('./snapshot.json', import.meta.url).href;
let snapshotPromise;

function validateSnapshot(value) {
  if(!value||value.version!==1||!Array.isArray(value.files)||!value.files.length||value.files.length>MAX_FILES||!/^([a-f\d]{40}|main)$/.test(value.revision)) throw new Error('无效题库缓存');
  let chars=0;
  for(const file of value.files) { if(!compatiblePath(file.path)||typeof file.content!=='string'||file.content.length>MAX_FILE_BYTES||!/^([a-f\d]{40})$/.test(file.sha)) throw new Error('无效题库文件'); chars+=file.content.length; }
  if(chars>MAX_TOTAL_CHARS) throw new Error('题库超出本地大小限制');
  parseMarkdownSources(value.files,{revision:value.revision});
  return value;
}
async function getJson(url,fetchImpl,timeout=15000) {
  const ctrl=new AbortController(), timer=setTimeout(()=>ctrl.abort(),timeout);
  try { const res=await fetchImpl(url,{signal:ctrl.signal,credentials:'omit',referrerPolicy:'no-referrer',headers:{Accept:'application/vnd.github+json'}}); if(!res.ok) throw new Error(`GitHub 请求失败（HTTP ${res.status}）`); return await res.json(); }
  finally {clearTimeout(timer);}
}
async function getText(url,fetchImpl) {
  const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),20000);
  try { const res=await fetchImpl(url,{signal:ctrl.signal,credentials:'omit',referrerPolicy:'no-referrer'}); if(!res.ok) throw new Error(`GitHub 文档读取失败（HTTP ${res.status}）`); const text=await res.text(); if(text.length>MAX_FILE_BYTES) throw new Error('文档超过大小限制'); return text; }
  finally {clearTimeout(timer);}
}
function readCache(storage) { try {const raw=storage?.getItem(CACHE_KEY); return raw?validateSnapshot(JSON.parse(raw)):null;}catch{return null;} }
function writeCache(storage,value) { try {storage?.setItem(CACHE_KEY,JSON.stringify(value));return true;}catch{return false;} }
async function bundled(fetchImpl) {
  if(!snapshotPromise) snapshotPromise=getJson(snapshotUrl,fetchImpl).then(validateSnapshot).catch(e=>{snapshotPromise=null;throw e;});
  return snapshotPromise;
}
function makeCatalog(base,origin,warning='') { return {...parseMarkdownSources(base.files,{revision:base.revision,fetchedAt:base.fetchedAt,origin}),checkedAt:base.checkedAt||null,generatedAt:base.generatedAt||null,warning}; }

/**
 * On launch check main at most once / 30 min. force bypasses TTL; no timer/cron.
 * Test hooks storage/fetchImpl/snapshot/now also permit restricted browser storage.
 */
function defaultStorage() { try { return globalThis.localStorage; } catch { return null; } }
export async function loadCatalog({force=false,onStatus=()=>{},fetchImpl=globalThis.fetch,storage=defaultStorage(),snapshot=null,now=Date.now()}={}) {
  onStatus({phase:'loading',message:'正在载入复习资料…'});
  let cached=readCache(storage), base=cached||validateSnapshot(snapshot||await bundled(fetchImpl));
  let origin=cached?'cache':'snapshot';
  if(!force&&base.checkedAt&&now-base.checkedAt<CHECK_INTERVAL) {
    const warning=base.lastError||'';
    onStatus({phase:warning?'offline':'cached',message:warning?'更新检查暂不可用，使用上次成功题库':'已使用本地题库（每 30 分钟检查一次更新）',revision:base.revision,fetchedAt:base.fetchedAt,warning});
    return makeCatalog(base,origin,warning);
  }
  onStatus({phase:'checking',message:'正在检查 GitHub main 更新…',revision:base.revision});
  try {
    const commit=await getJson(`${API}/commits/main`,fetchImpl);
    if(!/^[a-f\d]{40}$/.test(commit.sha)) throw new Error('GitHub 返回了无效版本');
    let next;
    if(commit.sha===base.revision) next={...base,checkedAt:now,fetchedAt:new Date(now).toISOString(),lastError:''};
    else {
      const tree=await getJson(`${API}/git/trees/${commit.sha}?recursive=1`,fetchImpl);
      if(tree.truncated||!Array.isArray(tree.tree)) throw new Error('GitHub 文件目录不完整，保留上次成功题库');
      const candidates=tree.tree.filter(f=>f.type==='blob'&&compatiblePath(f.path));
      if(!candidates.length||candidates.length>MAX_FILES||candidates.some(f=>f.size>MAX_FILE_BYTES)) throw new Error('GitHub 题库大小或路径不符合限制');
      const existing=new Map(base.files.map(f=>[f.path,f]));
      const files=new Array(candidates.length); let cursor=0;
      await Promise.all(Array.from({length:Math.min(6,candidates.length)},async()=>{
        while(cursor<candidates.length) {
          const index=cursor++, file=candidates[index], old=existing.get(file.path);
          if(old?.sha===file.sha) files[index]=old;
          else files[index]={path:file.path,sha:file.sha,content:await getText(`${RAW}/${commit.sha}/${file.path.split('/').map(encodeURIComponent).join('/')}`,fetchImpl)};
        }
      }));
      next={version:1,revision:commit.sha,files,checkedAt:now,fetchedAt:new Date(now).toISOString(),generatedAt:base.generatedAt,lastError:''};
      validateSnapshot(next); // Only replace cache after a complete, parseable update.
    }
    const stored=writeCache(storage,next);
    const catalog=makeCatalog(next,'github',stored?'':'浏览器未允许缓存题库；本次资料已更新，关闭页面后可能需重新联网。');
    onStatus({phase:commit.sha===base.revision?'current':'updated',message:commit.sha===base.revision?'已检查 GitHub，题库为最新版本':'已从 GitHub 更新题库',revision:next.revision,fetchedAt:next.fetchedAt,warning:catalog.warning});
    return catalog;
  } catch(error) {
    const warning=error?.name==='AbortError'?'GitHub 检查超时，已保留上次成功题库。':`${error?.message||'GitHub 暂不可用'}；已保留上次成功题库。`;
    const failed={...base,checkedAt:now,lastError:warning}; writeCache(storage,failed);
    onStatus({phase:'offline',message:origin==='snapshot'?'GitHub 暂不可用，使用打包快照':'GitHub 暂不可用，使用上次成功题库',revision:base.revision,fetchedAt:base.fetchedAt,warning});
    return makeCatalog(failed,origin,warning);
  }
}

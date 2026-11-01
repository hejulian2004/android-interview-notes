/** Public GitHub content only. No API token, HTML rendering, or background timer. */
export const REPOSITORY = 'hejulian2004/android-interview-notes';
export const CACHE_KEY = 'android-study:catalog:v1';
export const CHECK_INTERVAL = 30 * 60 * 1000;
export const TOPICS = Object.freeze([
  {id:'android',label:'Android'}, {id:'compose',label:'Compose'},
  {id:'xml',label:'XML / View'}, {id:'flutter',label:'Flutter'},
  {id:'rust',label:'Rust SDK'}, {id:'quic',label:'QUIC / 网络'},
  {id:'agent',label:'Agent'}, {id:'internship',label:'实习'}
]);
const API = `https://api.github.com/repos/${REPOSITORY}`;
const RAW = `https://raw.githubusercontent.com/${REPOSITORY}`;
const READING_GUIDES = /(?:sdk-source-deep-dive|quic-source-deep-dive|ai-code-takeover-workbook)\.md$/i;
const MAX_FILES = 400;
const MAX_FILE_BYTES = 1500000;
const MAX_TOTAL_CHARS = 6000000;
const snapshotUrl = new URL('./snapshot.json', import.meta.url).href;
let snapshotPromise;

export function compatiblePath(path) {
  return typeof path === 'string' && !path.includes('..') && (
    /^docs\/(?:[^/]+\/)*[^/]+\.md$/i.test(path) ||
    /^(?:questions|supplements)\/(?:[^/]+\/)*[QE]\d+[-·][^/]+\.md$/i.test(path)
  );
}
function cleanMarkdown(text) {
  // Preserve inert source anchors so the Markdown renderer can map TOC links.
  // Raw HTML remains untrusted and is never interpreted by this parser.
  return String(text).replace(/^\uFEFF/, '').replace(/\r\n?/g,'\n');
}
function withoutFrontmatter(text) { return text.replace(/^---\n[\s\S]*?\n---\n+/, ''); }
function headings(text) {
  const result=[]; let offset=0, fence=null;
  for(const line of text.split('\n')) {
    const f=line.match(/^ {0,3}(`{3,}|~{3,})/);
    if(f) { if(!fence) fence={char:f[1][0],length:f[1].length}; else if(f[1][0]===fence.char&&f[1].length>=fence.length) fence=null; }
    else if(!fence) { const m=line.match(/^(#{1,6})\s+(.+?)\s*#*$/); if(m) result.push({level:m[1].length,text:m[2],start:offset,end:offset+line.length}); }
    offset += line.length+1;
  }
  return result;
}
function textOnly(markdown) {
  return markdown.replace(/!?(?:\[([^\]]+)\])\([^)]*\)/g,'$1').replace(/<[^>]*>/g,' ').replace(/[`#*_>|]/g,' ').replace(/\s+/g,' ').trim();
}
function topicsFor(path, section='', number='', title='') {
  const hay=`${path} ${section} ${title}`;
  if(/flutter-interview/.test(path)) return ['flutter'];
  if(/word-crush|XML|自定义View|RecyclerView/.test(hay)) return ['xml','android'];
  if(/quic-source/.test(path)) return ['quic','rust'];
  if(/sdk-source/.test(path)) return ['rust'];
  if(/ai-code-takeover/.test(path)) return ['agent','rust','quic','flutter'];
  if(/^I\d/.test(number)||/实习|渠道SDK/.test(section)) return ['internship','android'];
  if(/^G\d/.test(number)) return ['agent'];
  if(/^[PE]\d/.test(number)&&/android-interview-handbook/.test(path)) return ['flutter','agent'];
  if(/^N\d/.test(number)) return /QUIC|传输|断点|SHA-256|ACK|NAT|Noise|AES|Relay|TCP|UDP/.test(title)?['quic','rust']:['rust'];
  if(/feedline|Compose|JetpackCompose/.test(hay)) return ['compose','android'];
  if(/Flutter|Dart/.test(hay)) return ['flutter'];
  if(/Rust|SDK/.test(hay)) return ['rust'];
  if(/QUIC/.test(hay)) return ['quic'];
  if(/Agent|AI|MCP/.test(hay)) return ['agent'];
  return ['android'];
}
function sourceUrl(path, revision='main', anchor='') {
  return `https://github.com/${REPOSITORY}/blob/${encodeURIComponent(revision)}/${path.split('/').map(encodeURIComponent).join('/')}${anchor?'#'+encodeURIComponent(anchor):''}`;
}
function docContext(markdown, hs) {
  const firstH2=hs.find(h=>h.level===2);
  let intro=markdown.slice(0,firstH2?.start??Math.min(markdown.length,5000)).trim();
  // The handbook's labels define what verified code, general principles and unknowns mean.
  const labels=hs.find(h=>h.text==='事实标签');
  if(labels) { const next=hs.find(h=>h.start>labels.start&&h.level<=labels.level); intro+='\n\n'+markdown.slice(labels.start,next?.start??markdown.length).trim(); }
  return intro;
}
function githubHeadingAnchor(text) {
  return text.replace(/[`*_]/g,'').toLowerCase().replace(/[^\p{L}\p{N}\p{M} _-]/gu,'').replace(/ /g,'-');
}
function parseFile(file, revision) {
  const anchors = new Map();
  for (const match of file.content.matchAll(/<a\s+(?:id|name)=["']([^"']+)["']\s*>\s*<\/a>\s*\n###\s+([^\n]+)/g)) anchors.set(match[2].trim(),match[1]);
  const path=file.path, markdown=withoutFrontmatter(cleanMarkdown(file.content));
  const hs=headings(markdown), title=hs.find(h=>h.level===1)?.text??path.split('/').pop().replace(/\.md$/,'');
  const docId=path, contextMarkdown=docContext(markdown,hs), topicIds=topicsFor(path,'','',title);
  const doc={id:docId,path,title,markdown,contextMarkdown,topicId:topicIds[0],topicIds,sourceUrl:sourceUrl(path,revision),kind:'guide'};
  const questions=[];
  if(/^(questions|supplements)\//.test(path)) {
    const match=title.match(/^([QE]\d+)\s*[·.｜:]?\s*(.+)$/);
    if(!match) return {doc:null,questions};
    const number=match[1], topicIds=topicsFor(path,'',number,match[2]);
    const kind=path.startsWith('supplements/')?'supplement':'public';
    const h1=hs.find(h=>h.level===1);
    const content=markdown.slice(h1.end).trim();
    const beforeAnswer=hs.find(h=>h.text==='参考回答提纲');
    const context=beforeAnswer?markdown.slice(h1.end,beforeAnswer.start).trim():'';
    questions.push({id:`${path}#${number.toLowerCase()}`,title:match[2],number,topicId:topicIds[0],topicIds,
      section:path.split('/')[1]?.replace(/^\d+-/,''),answerMarkdown:content,contextMarkdown:context,
      docId,path,sourceUrl:sourceUrl(path,revision),kind,priority:(file.content.match(/^priority:\s*(P[0-2])/m)||[])[1]||'',
      searchText:textOnly(`${title}\n${content}`)});
    return {doc:null,questions};
  }
  if(READING_GUIDES.test(path)) return {doc,questions};
  for(let i=0;i<hs.length;i++) {
    const h=hs[i]; if(h.level!==3) continue;
    const match=h.text.match(/^([A-Z]{1,3}\d{1,4})(?:[.．｜:：·]\s*|\s+)(.+)$/);
    if(!match) continue;
    const next=hs.slice(i+1).find(n=>n.level<=h.level);
    const answerMarkdown=markdown.slice(h.end,next?.start??markdown.length)
      .replace(/(?:\s*<a\s+(?:id|name)=["'][^"']+["']\s*>\s*<\/a>\s*)+$/g,'').trim();
    if(!answerMarkdown||answerMarkdown.length<10) continue;
    const number=match[1], section=hs.slice(0,i).reverse().find(n=>n.level===2)?.text??title;
    const topicIds=topicsFor(path,section,number,match[2]);
    const priority=(match[2].match(/\b(P[0-2])\b/)||[])[1]||'';
    const anchor=anchors.get(h.text)||githubHeadingAnchor(h.text);
    const parentHeading=hs.slice(0,i).reverse().find(n=>n.level===2);
    const firstChild=parentHeading&&hs.find(n=>n.start>parentHeading.start&&n.level<=3);
    const sectionIntro=parentHeading?markdown.slice(parentHeading.end,firstChild?.start??h.start).trim():'';
    const questionContext=sectionIntro?contextMarkdown+'\n\n'+sectionIntro:contextMarkdown;
    questions.push({id:`${path}#${number.toLowerCase()}`,title:match[2].replace(/^P[0-2][：: ]*/,'').trim(),number,
      topicId:topicIds[0],topicIds,section,answerMarkdown,contextMarkdown:questionContext,docId,path,
      sourceUrl:sourceUrl(path,revision,anchor),kind:'guide',priority,
      searchText:textOnly(`${h.text}\n${section}\n${answerMarkdown}`)});
  }
  return {doc,questions};
}

/** Pure parser; files are {path,content,sha?}. No HTML is interpreted by this module. */
export function parseMarkdownSources(files,{revision='main',fetchedAt=null,origin='snapshot'}={}) {
  const entries=Array.isArray(files)?files:Object.values(files);
  const questions=[], documents=[];
  for(const file of entries.filter(f=>compatiblePath(f.path)).sort((a,b)=>a.path.localeCompare(b.path,'en'))) {
    const parsed=parseFile(file,revision);
    questions.push(...parsed.questions); if(parsed.doc) documents.push(parsed.doc);
  }
  if(!questions.length) throw new Error('题库为空或 Markdown 结构不兼容，保留上次成功题库。');
  const ids=new Set();
  for(const q of questions) { if(ids.has(q.id)) throw new Error(`重复题号：${q.id}`); ids.add(q.id); }
  return {questions,documents,topics:TOPICS,revision,fetchedAt,origin,warning:''};
}
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

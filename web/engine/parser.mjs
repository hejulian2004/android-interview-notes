/** Pure Markdown parser shared by the authenticated client. No network or credentials. */
export const REPOSITORY = 'hejulian2004/android-interview-notes';
export const TOPICS = Object.freeze([
  {id:'android',label:'Android'}, {id:'compose',label:'Compose'},
  {id:'xml',label:'XML / View'}, {id:'flutter',label:'Flutter'},
  {id:'rust',label:'Rust SDK'}, {id:'quic',label:'QUIC / 网络'},
  {id:'agent',label:'Agent'}, {id:'internship',label:'实习'}
]);
const READING_GUIDES = /(?:sdk-source-deep-dive|quic-source-deep-dive|ai-code-takeover-workbook)\.md$/i;

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

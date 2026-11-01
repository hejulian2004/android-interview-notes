/** Browser-local progress data. No content, network, or DOM dependency. */
export const PROGRESS_VERSION = 1;
const MASTERIES = new Set(['new','review','mastered']);
export function emptyProgress() {return {version:PROGRESS_VERSION,updatedAt:null,items:Object.create(null)};}
function validDate(value) {return typeof value==='string'&&value.length<60&&!Number.isNaN(Date.parse(value))?value:null;}
export function normalizeProgress(value) {
  if(!value||typeof value!=='object'||Array.isArray(value))throw new Error('进度文件格式不正确');
  if(value.version!==undefined&&value.version!==0&&value.version!==PROGRESS_VERSION)throw new Error('该进度版本暂不支持，请保留原文件');
  const input=value.items||value.progress;
  if(!input||typeof input!=='object'||Array.isArray(input))throw new Error('未找到有效的题目进度');
  if(Object.keys(input).length>10000)throw new Error('进度记录数量超出限制');
  const items=Object.create(null);
  for(const [id,item]of Object.entries(input)) {
    if(!id||id.length>1500||['__proto__','prototype','constructor'].includes(id)||!item||typeof item!=='object'||Array.isArray(item))continue;
    items[id]={mastery:MASTERIES.has(item.mastery)?item.mastery:'new',favorite:item.favorite===true,updatedAt:validDate(item.updatedAt),seenAt:validDate(item.seenAt)};
  }
  return {version:PROGRESS_VERSION,updatedAt:validDate(value.updatedAt),items};
}
/** Restore malformed/unsupported data without discarding the original backup. */
export function restoreProgress(raw) {
  if(raw===null||raw===undefined||raw==='')return {progress:emptyProgress(),recoveryRaw:null,warning:''};
  try {return {progress:normalizeProgress(JSON.parse(raw)),recoveryRaw:null,warning:''};}
  catch(error){return {progress:emptyProgress(),recoveryRaw:String(raw),warning:error.message||'本机进度无法读取'};}
}
/** Merge by stable question ID, preserving newer local records and orphan IDs. */
export function mergeProgress(current,incoming) {
  const next=normalizeProgress(current),source=normalizeProgress(incoming);let count=0;
  for(const [id,item]of Object.entries(source.items)) {
    const old=next.items[id];
    const newer=!old||!old.updatedAt||(item.updatedAt&&Date.parse(item.updatedAt)>=Date.parse(old.updatedAt));
    if(newer){next.items[id]=item;count++;}
  }
  return {progress:next,count};
}

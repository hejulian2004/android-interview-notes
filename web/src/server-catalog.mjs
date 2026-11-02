/** Authenticated same-origin content transport. No GitHub/model requests here. */
import { apiRequest } from './api.mjs';
import { parseMarkdownSources, compatiblePath } from './engine/parser.mjs';

export function parseServerCatalog(snapshot) {
  if (!snapshot || snapshot.version !== 1 || !/^[a-f\d]{40}$/.test(snapshot.revision)
      || !Array.isArray(snapshot.files) || !snapshot.files.length || snapshot.files.length > 600)
    throw new Error('服务器返回了无效题库版本');
  let total = 0;
  const paths = new Set();
  for (const file of snapshot.files) {
    if (!file || !compatiblePath(file.path) || paths.has(file.path)
        || typeof file.content !== 'string' || file.content.length > 1500000
        || !/^[a-f\d]{40}$/.test(file.sha)) throw new Error('服务器返回了无效题库文件');
    paths.add(file.path); total += file.content.length;
  }
  if (total > 6000000) throw new Error('题库超出大小限制');
  return { ...parseMarkdownSources(snapshot.files, {
    revision:snapshot.revision, fetchedAt:snapshot.fetchedAt, origin:'server'
  }), checkedAt:snapshot.checkedAt, generatedAt:snapshot.generatedAt || null,
  cacheStatus:String(snapshot.cacheStatus || ''), refreshing:snapshot.refreshing===true,
  warning:String(snapshot.warning || '') };
}

export async function loadCatalog({force=false,onStatus=()=>{},request=apiRequest}={}) {
  onStatus({phase:'checking',message:force?'服务器正在检查 GitHub 更新…':'正在读取服务器题库…'});
  const snapshot = await request(force?'catalog/refresh':'catalog', {method:force?'POST':'GET', ...(force?{body:{}}:{})});
  const catalog = parseServerCatalog(snapshot);
  onStatus(catalogStatus(catalog));
  return catalog;
}

export function catalogStatus(catalog) {
  const cached=catalog.cacheStatus==='stale'||catalog.refreshing;
  return {phase:catalog.warning?'offline':cached?'cached':'updated',
    message:catalog.warning || `服务器${cached?'缓存':''}题库已载入 · ${catalog.questions.length} 道题${catalog.refreshing?' · 后台检查 GitHub 更新中':catalog.cacheStatus==='stale'?' · 尚未确认最新版本':''}`,
    revision:catalog.revision,fetchedAt:catalog.fetchedAt,warning:catalog.warning};
}

/** A bounded GET-only followup for an already running server refresh. */
export function createCatalogFollower({load=loadCatalog,onCatalog=()=>{},onStatus=()=>{},schedule=setTimeout,cancel=clearTimeout,delays=[2000,4000,8000]}={}) {
  let generation=0,timer=null;
  function stop(){generation++;if(timer!==null)cancel(timer);timer=null;}
  function start(initial){
    stop();if(!initial?.refreshing)return;
    const current=generation;let attempt=0,last=initial;
    function next(){
      if(current!==generation)return;
      if(attempt>=delays.length){onStatus({phase:'cached',message:'服务器缓存题库已载入 · 可点击“更新题库”检查后台结果',fetchedAt:last.fetchedAt,warning:last.warning||''});return;}
      timer=schedule(async()=>{
        timer=null;if(current!==generation)return;
        try{
          const value=await load({force:false,onStatus:()=>{}});
          if(current!==generation)return;
          last=value;onCatalog(value);
          if(value.refreshing)next();
        }catch{
          if(current!==generation)return;
          onStatus({phase:'cached',message:'继续使用已载入的服务器题库 · 暂未取得后台更新结果',fetchedAt:last.fetchedAt,warning:'后台结果读取暂不可用；当前题目和学习进度已保留。'});
          next();
        }
      },delays[attempt++]);
    }
    next();
  }
  return {start,cancel:stop};
}

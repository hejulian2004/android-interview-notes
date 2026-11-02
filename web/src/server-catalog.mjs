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
  warning:String(snapshot.warning || '') };
}

export async function loadCatalog({force=false,onStatus=()=>{},request=apiRequest}={}) {
  onStatus({phase:'checking',message:force?'服务器正在检查 GitHub 更新…':'正在读取服务器题库…'});
  const snapshot = await request(force?'catalog/refresh':'catalog', {method:force?'POST':'GET', ...(force?{body:{}}:{})});
  const catalog = parseServerCatalog(snapshot);
  onStatus({phase:catalog.warning?'offline':'updated',
    message:catalog.warning || `服务器题库已载入 · ${catalog.questions.length} 道题`,
    revision:catalog.revision,fetchedAt:catalog.fetchedAt,warning:catalog.warning});
  return catalog;
}

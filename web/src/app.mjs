import { loadCatalog, TOPICS } from './engine/index.mjs';
import { renderMarkdown } from './markdown.mjs';
import { normalizeProgress, restoreProgress, mergeProgress } from './progress.mjs';

const $ = id => document.getElementById(id);
const PROGRESS_KEY = 'android-study.progress.v1';
const SESSION_KEY = 'android-study.session.v1';
const RECOVERY_KEY = 'android-study.progress.recovery.v1';
const MASTERIES = { new: '未掌握', review: '待复习', mastered: '已掌握' };
const TOPIC_ICONS = { all:'▦', android:'◈', compose:'▥', xml:'⌘', flutter:'◇', rust:'◉', quic:'↗', agent:'✳', internship:'▣' };
const PAGE_SIZE = 24;
let catalog = null;
let loadBusy = false;
let revealed = false;
let page = 0;
let toastTimer;
let searchTimer;
let recoveryRaw = null;
let progress = readProgress();
let ui = readRoute();

function node(tag, attrs = {}, children = []) {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value === null || value === undefined || value === false) continue;
    if (key === 'text') el.textContent = value;
    else if (key === 'class') el.className = value;
    else if (key === 'disabled') el.disabled = !!value;
    else el.setAttribute(key, String(value));
  }
  for (const child of Array.isArray(children) ? children : [children]) {
    if (child !== null && child !== undefined) el.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return el;
}
function markdown(content, sourceUrl) {
  const el = node('div', { class:'markdown-body' });
  el.innerHTML = renderMarkdown(content || '', sourceUrl);
  return el;
}
function notice(message) { $('notice').textContent = message; $('notice').hidden = !message; }
function toast(message) {
  clearTimeout(toastTimer);
  $('toast').textContent = message;
  $('toast').hidden = false;
  toastTimer = setTimeout(() => { $('toast').hidden = true; }, 3300);
}
function showRecoveryButton() {
  if (!recoveryRaw || $('export-recovery')) return;
  const button = node('button',{id:'export-recovery',class:'button secondary',type:'button'},'导出原始记录备份');
  button.addEventListener('click',()=>{
    try {downloadJSON(JSON.parse(recoveryRaw),'安卓复习进度-原始备份.json');}
    catch {
      const url=URL.createObjectURL(new Blob([recoveryRaw],{type:'text/plain;charset=utf-8'}));
      const link=node('a',{href:url,download:'安卓复习进度-原始备份.txt'});
      document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
    }
  });
  document.querySelector('.settings-actions').append(button);
}
function readProgress() {
  let raw;
  try {
    raw = localStorage.getItem(PROGRESS_KEY);
    const restored = restoreProgress(raw);
    if (restored.warning) throw new Error(restored.warning);
    recoveryRaw = localStorage.getItem(RECOVERY_KEY);
    if (recoveryRaw) queueMicrotask(showRecoveryButton);
    return restored.progress;
  } catch {
    recoveryRaw = raw || null;
    if (recoveryRaw) {try {localStorage.setItem(RECOVERY_KEY,recoveryRaw);} catch {}}
    queueMicrotask(() => {
      notice('本机进度无法读取，已启用新的学习记录。你可以在“进度管理”中导出原始记录备份，或导入此前的进度文件。');
      showRecoveryButton();
    });
    return {version:1, updatedAt:null, items:Object.create(null)};
  }
}
function saveProgress() {
  progress.updatedAt = new Date().toISOString();
  try { localStorage.setItem(PROGRESS_KEY, JSON.stringify(progress)); }
  catch { notice('浏览器未能保存进度。当前页面仍可使用，请在离开前导出进度，并检查浏览器存储空间。'); }
}
function itemState(id) { return progress.items[id] || {mastery:'new', favorite:false}; }
function updateItem(id, patch) {
  progress.items[id] = {...itemState(id), ...patch, updatedAt:new Date().toISOString()};
  saveProgress();
  render();
}
function readRoute() {
  let hash = location.hash.slice(1);
  if (!hash) {
    try { hash = JSON.parse(localStorage.getItem(SESSION_KEY) || 'null')?.route || ''; } catch {}
  }
  const [mode, query = ''] = hash.split('?');
  const params = new URLSearchParams(query);
  return {
    mode:['practice','bank','reading'].includes(mode) ? mode : 'practice',
    topic:TOPICS.some(t => t.id === params.get('topic')) ? params.get('topic') : 'all',
    scope:['all','review','favorites','mastered'].includes(params.get('scope')) ? params.get('scope') : 'all',
    query:(params.get('q') || '').slice(0, 500),
    id:params.get('id') || null,
    doc:params.get('doc') || null
  };
}
function routeString(state) {
  const params = new URLSearchParams();
  if (state.topic !== 'all') params.set('topic', state.topic);
  if (state.scope !== 'all' && state.mode !== 'reading') params.set('scope', state.scope);
  if (state.query) params.set('q', state.query);
  if (state.id && state.mode === 'practice') params.set('id', state.id);
  if (state.doc && state.mode === 'reading') params.set('doc', state.doc);
  return state.mode + (params.size ? '?' + params.toString() : '');
}
function rememberRoute() {
  try { localStorage.setItem(SESSION_KEY, JSON.stringify({version:1,route:routeString(ui)})); } catch {}
}
function navigate(patch, {replace = false, scroll = false} = {}) {
  const previousId = ui.id;
  const previousMode = ui.mode;
  ui = {...ui, ...patch};
  if (previousId !== ui.id || previousMode !== ui.mode || patch.topic !== undefined || patch.scope !== undefined || patch.query !== undefined) revealed = false;
  if (patch.topic !== undefined || patch.scope !== undefined || patch.query !== undefined) page = 0;
  const hash = '#' + routeString(ui);
  if (replace) history.replaceState(null, '', hash);
  else if (location.hash !== hash) history.pushState(null, '', hash);
  rememberRoute();
  render();
  if (scroll) $('workspace').scrollIntoView({behavior:'smooth', block:'start'});
}
function searchValue(text) { return String(text || '').toLocaleLowerCase().replace(/\s+/g, ' ').trim(); }
function topicMatches(item) { return ui.topic === 'all' || item.topicId === ui.topic || item.topicIds?.includes(ui.topic); }
function queryMatches(item) {
  const terms = searchValue(ui.query).split(' ').filter(Boolean);
  if (!terms.length) return true;
  const haystack = searchValue([item.searchText, item.title, item.answerMarkdown, item.contextMarkdown, item.markdown, item.section].filter(Boolean).join(' '));
  return terms.every(term => haystack.includes(term));
}
function questionPool(scope = ui.scope) {
  return (catalog?.questions || []).filter(q => {
    if (!topicMatches(q) || !queryMatches(q)) return false;
    const state = itemState(q.id);
    return scope === 'all' || (scope === 'favorites' && state.favorite) || (scope === 'review' && state.mastery === 'review') || (scope === 'mastered' && state.mastery === 'mastered');
  });
}
function docPool() { return (catalog?.documents || []).filter(d => topicMatches(d) && queryMatches(d)); }
function topicLabel(id) { return TOPICS.find(t => t.id === id)?.label || '综合'; }
function sourceLabel(q) { return q.kind === 'public' ? '公开面试题' : q.kind === 'supplement' ? '扩展补充题' : '项目与原始笔记'; }
function safeExternalLink(url, text, attrs = {}) {
  let href = '#';
  try { const u = new URL(url); if (u.protocol === 'https:' || u.protocol === 'http:') href = u.href; } catch {}
  return node('a', {...attrs, href, target:'_blank', rel:'noopener noreferrer'}, text);
}
function renderStats() {
  const questions = catalog.questions;
  const mastered = questions.filter(q => itemState(q.id).mastery === 'mastered').length;
  const review = questions.filter(q => itemState(q.id).mastery === 'review').length;
  const percent = questions.length ? Math.round(mastered / questions.length * 100) : 0;
  $('total-count').textContent = questions.length;
  $('mastered-count').textContent = mastered;
  $('review-count').textContent = review;
  $('sidebar-percent').textContent = percent + '%';
  $('sidebar-progress').value = percent;
  $('sidebar-progress').textContent = percent + '%';
  $('sidebar-progress-note').textContent = `已掌握 ${mastered} / ${questions.length} 题`;
  $('topic-total').textContent = `${TOPICS.length} 个`;
  const ids = new Set(questions.map(q => q.id));
  const orphans = Object.keys(progress.items).filter(id => !ids.has(id));
  $('clean-orphans').hidden = !orphans.length;
  $('orphan-note').textContent = orphans.length ? `有 ${orphans.length} 条记录对应的题目已从当前题库移除，仍保留在导出文件中；它们不计入学习统计。` : '导出文件只包含题目标识、收藏和学习状态，不包含题目答案。';
  $('revision-label').textContent = catalog.revision ? `main · ${catalog.revision.slice(0,7)}` : '';
  const bundled = catalog.origin === 'snapshot';
  $('snapshot-note').textContent = bundled ? `打包快照 ${formatDate(catalog.generatedAt || catalog.fetchedAt)} · 本机进度` : `GitHub 公开笔记 · 进度仅保存在当前浏览器`;
}
function renderTopics() {
  const all = [{id:'all',label:'全部专题'}, ...TOPICS];
  $('topics').replaceChildren(...all.map(topic => {
    const count = catalog.questions.filter(q => topic.id === 'all' || q.topicId === topic.id || q.topicIds?.includes(topic.id)).length;
    return node('button', {class:'topic-button' + (ui.topic === topic.id ? ' active' : ''), type:'button', 'data-topic':topic.id, 'aria-pressed':ui.topic === topic.id}, [
      node('span', {class:'topic-icon','aria-hidden':'true'}, TOPIC_ICONS[topic.id] || '◇'), node('span', {class:'topic-name'}, topic.label), node('span', {class:'topic-count'}, count)
    ]);
  }));
}
function renderScope() {
  $('scope-bar').hidden = ui.mode === 'reading';
  const data = [['all','全部题目'],['review','待复习'],['favorites','我的收藏'],['mastered','已掌握']];
  $('scope-bar').replaceChildren(...data.map(([key,label]) => node('button', {type:'button',class:'scope-button' + (ui.scope === key ? ' active' : ''),'data-scope':key,'aria-pressed':ui.scope === key}, [label,node('span',{},questionPool(key).length)])));
}
function render() {
  if (!catalog) return;
  renderStats(); renderTopics(); renderScope();
  document.querySelectorAll('[data-mode]').forEach(el => { const active = el.dataset.mode === ui.mode; el.classList.toggle('active',active); el.setAttribute('aria-current',active ? 'page' : 'false'); });
  if ($('search-input').value !== ui.query) $('search-input').value = ui.query;
  $('clear-search').hidden = !ui.query;
  $('reset-filters').hidden = ui.topic === 'all' && ui.scope === 'all' && !ui.query;
  const pool = ui.mode === 'reading' ? docPool() : questionPool();
  const label = ui.topic === 'all' ? '全部专题' : topicLabel(ui.topic);
  $('result-caption').textContent = ui.mode === 'reading' ? `${label} · ${pool.length} 篇阅读资料` : `${label} · ${pool.length} 道题${ui.query ? '符合搜索' : ''}`;
  if (!pool.length) {
    $('study-content').replaceChildren(emptyState());
  } else if (ui.mode === 'reading') {
    renderReading(pool);
  } else if (ui.mode === 'bank') {
    renderBank(pool);
  } else {
    renderPractice(pool);
  }
  rememberRoute();
}
function emptyState() {
  const isReview = ui.scope === 'review' && ui.mode !== 'reading';
  return node('div',{class:'empty-state'},[
    node('div',{class:'empty-mark','aria-hidden':'true'},isReview ? '✓' : '⌕'),
    node('h2',{},isReview ? '这里暂时没有待复习的题' : '没有找到匹配的内容'),
    node('p',{},isReview ? '练习后标记“待复习”，下次就能在这里集中回顾。' : '试试更短的关键词，或切换专题和学习状态。'),
    node('button',{type:'button',class:'button secondary','data-action':'reset'},'查看全部题目')
  ]);
}
function favoriteButton(q, compact = false) {
  const favorite = itemState(q.id).favorite;
  return node('button',{type:'button',class:'favorite-button' + (favorite?' active':''),'data-action':'favorite','data-id':q.id,'aria-pressed':favorite,'aria-label':(favorite?'取消收藏：':'收藏：')+q.title},[node('span',{'aria-hidden':'true'},favorite?'★':'☆'),compact ? null : favorite?'已收藏':'收藏']);
}
function questionSource(q) {
  const doc = catalog.documents.find(d => d.id === q.docId);
  return node('div',{class:'question-source'},[q.section || doc?.title || sourceLabel(q),' · ',safeExternalLink(q.sourceUrl,'查看 GitHub 原文 ↗')]);
}
function renderPractice(pool) {
  let index = pool.findIndex(q => q.id === ui.id);
  if (index < 0) { index = 0; ui.id = pool[0].id; revealed = false; history.replaceState(null,'','#'+routeString(ui)); }
  const q = pool[index];
  const state = itemState(q.id);
  const top = node('div',{class:'question-top'},[
    node('div',{class:'question-meta'},[
      node('div',{class:'question-labels'},[node('span',{class:'badge'},topicLabel(q.topicId)),node('span',{class:'question-number'},q.number || ''),node('span',{class:'badge neutral'},sourceLabel(q))]),favoriteButton(q)
    ]),
    node('h2',{class:'question-title',id:'current-question'},q.title),questionSource(q),
    node('p',{class:'source-boundary'},'以原文证据与源码版本为准；通用原理不代表项目已实现。')
  ]);
  if (revealed) {
    const answer = node('div',{class:'answer-section',id:'answer-content'},[
      node('div',{class:'answer-heading'},[node('span',{},'参考回答'),node('button',{type:'button',class:'text-button','data-action':'hide-answer'},'收起答案 ↑')])
    ]);
    if (q.contextMarkdown) answer.append(node('details',{class:'context-details'},[node('summary',{},'查看来源说明、事实边界与版本依据'),markdown(q.contextMarkdown,q.sourceUrl)]));
    answer.append(markdown(q.answerMarkdown,q.sourceUrl));
    top.append(answer);
  } else {
    top.append(node('div',{class:'answer-prompt'},[
      node('div',{class:'prompt-icon','aria-hidden':'true'},'“'),node('h3',{},'先用自己的话，试着回答'),node('p',{},'想一想关键概念、实现过程，以及适用边界。'),
      node('button',{type:'button',class:'button large','data-action':'reveal','aria-expanded':'false','aria-controls':'answer-content'},['查看参考答案',node('span',{class:'arrow','aria-hidden':'true'},'↓')])
    ]));
  }
  const mastery = node('div',{class:'mastery-panel'},[
    node('span',{class:'mastery-label'},revealed?'这一题，你掌握得怎么样？':'看完答案后，记录掌握程度'),
    node('div',{class:'mastery-actions'},Object.entries(MASTERIES).map(([key,label])=>node('button',{type:'button',class:'mastery-button'+(state.mastery===key?' selected':''),'data-action':'mastery','data-mastery':key,'data-id':q.id,disabled:!revealed,'aria-pressed':state.mastery===key},(key==='mastered'?'✓ ':key==='review'?'↻ ':'○ ')+label)))
  ]);
  const card = node('article',{class:'question-card','aria-labelledby':'current-question'},[top,mastery]);
  const controls = node('div',{class:'practice-controls'},[
    node('button',{type:'button',class:'button','data-action':'previous',disabled:index===0},'← 上一题'),
    node('button',{type:'button',class:'random-button','data-action':'random',disabled:pool.length<2},[node('span',{'aria-hidden':'true'},'⤨'),'随机一题']),
    node('button',{type:'button',class:'button','data-action':'next',disabled:index===pool.length-1},'下一题 →')
  ]);
  $('study-content').replaceChildren(card,controls,node('p',{class:'practice-note'},`当前筛选 · 第 ${index+1} / ${pool.length} 题　｜　收藏与掌握状态自动保存在当前浏览器`));
}
function renderBank(pool) {
  const pages = Math.ceil(pool.length/PAGE_SIZE);
  page = Math.max(0,Math.min(page,pages-1));
  const grid = node('div',{class:'bank-grid'},pool.slice(page*PAGE_SIZE,(page+1)*PAGE_SIZE).map(q => {
    const state = itemState(q.id);
    return node('article',{class:'bank-card'},[
      node('div',{class:'bank-card-top'},[node('div',{class:'question-labels'},[node('span',{class:'badge'},topicLabel(q.topicId)),node('span',{class:'question-number'},q.number || '')]),favoriteButton(q,true)]),
      node('h2',{},q.title),node('p',{},q.section || sourceLabel(q)),
      node('div',{class:'bank-card-bottom'},[node('span',{class:'status-tag '+state.mastery},MASTERIES[state.mastery]),node('button',{type:'button',class:'button secondary','data-action':'practice','data-id':q.id},'开始练习 →')])
    ]);
  }));
  const pagination = node('div',{class:'pagination'},[
    node('button',{type:'button',class:'button secondary','data-action':'page-prev',disabled:page===0},'上一页'),node('span',{},`${page+1} / ${pages}`),node('button',{type:'button',class:'button secondary','data-action':'page-next',disabled:page>=pages-1},'下一页')
  ]);
  $('study-content').replaceChildren(grid,pagination);
}
function renderReading(pool) {
  let doc = pool.find(d => d.id === ui.doc) || pool[0];
  ui.doc = doc.id;
  const nav = node('nav',{class:'document-nav','aria-label':'阅读资料'},pool.map(d=>node('button',{type:'button',class:'document-button'+(d.id===doc.id?' active':''),'data-action':'read','data-id':d.id,'aria-current':d.id===doc.id?'page':'false'},[node('span',{},topicLabel(d.topicId)),node('strong',{},d.title)])));
  const article = node('article',{class:'document-view'},[
    node('div',{class:'document-header'},[node('span',{},'完整笔记 · 保留源码版本与事实限制'),safeExternalLink(doc.sourceUrl,'GitHub 原文 ↗')]),markdown(doc.markdown,doc.sourceUrl)
  ]);
  $('study-content').replaceChildren(node('div',{class:'reading-grid'},[nav,article]));
}
function moveQuestion(direction) {
  const pool = questionPool();
  const index = pool.findIndex(q => q.id === ui.id);
  if (!pool.length) return;
  let target;
  if (direction === 'random') {
    if (pool.length < 2) return;
    let next = Math.floor(Math.random() * (pool.length - 1));
    if (next >= index) next++;
    target = pool[next];
  } else target = pool[index + (direction==='next'?1:-1)];
  if (target) navigate({id:target.id},{scroll:true});
}
function formatDate(date) {
  if (!date || Number.isNaN(Date.parse(date))) return '日期未知';
  return new Intl.DateTimeFormat('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(date));
}
function setSyncStatus(status) {
  const fallback = ['offline','cached'].includes(status.phase);
  $('sync-indicator').classList.toggle('offline',fallback);
  let message = status.message || '正在检查 GitHub 题库';
  if (status.fetchedAt && !message.includes('时间')) message += ` · ${formatDate(status.fetchedAt)}`;
  $('sync-status').textContent = message;
  $('sync-status').title = status.warning || message;
}
async function refreshCatalog(force = false) {
  if (loadBusy) return;
  loadBusy = true; $('refresh-catalog').disabled = true;
  try {
    catalog = await loadCatalog({force,onStatus:setSyncStatus});
    if (!catalog?.questions?.length) throw new Error('题库中暂未找到可用题目');
    if (catalog.warning) setSyncStatus({phase:'offline',message:catalog.warning,fetchedAt:catalog.fetchedAt});
    render();
    if (force) toast(catalog.warning ? '更新暂未成功，继续使用上次可用题库' : `题库已检查，共 ${catalog.questions.length} 道题`);
  } catch (error) {
    setSyncStatus({phase:'offline',message:'题库读取失败，请稍后重试',warning:error.message});
    if (!catalog) $('study-content').replaceChildren(node('div',{class:'empty-state'},[node('h2',{},'题库暂时无法读取'),node('p',{},'请检查网络后，点击上方“更新题库”重试。')]));
    toast('读取题库失败，请稍后重试');
  } finally { loadBusy = false; $('refresh-catalog').disabled = false; }
}

$('topics').addEventListener('click',event=>{const b=event.target.closest('[data-topic]');if(b)navigate({topic:b.dataset.topic,id:null,doc:null});});
document.querySelector('.mode-nav').addEventListener('click',event=>{const b=event.target.closest('[data-mode]');if(b)navigate({mode:b.dataset.mode});});
$('scope-bar').addEventListener('click',event=>{const b=event.target.closest('[data-scope]');if(b)navigate({scope:b.dataset.scope,id:null});});
$('search-input').addEventListener('input',event=>{clearTimeout(searchTimer);const query=event.target.value;searchTimer=setTimeout(()=>navigate({query,id:null,doc:null},{replace:true}),130);});
$('clear-search').addEventListener('click',()=>{clearTimeout(searchTimer);navigate({query:'',id:null,doc:null});$('search-input').focus();});
$('reset-filters').addEventListener('click',()=>navigate({topic:'all',scope:'all',query:'',id:null,doc:null}));
$('refresh-catalog').addEventListener('click',()=>refreshCatalog(true));
$('settings-toggle').addEventListener('click',()=>{const show=$('settings').hidden;$('settings').hidden=!show;$('settings-toggle').setAttribute('aria-expanded',show);});
$('study-content').addEventListener('click',event=>{
  const button=event.target.closest('[data-action]');if(!button || button.disabled)return;
  const {action,id}=button.dataset;
  if(action==='reset')navigate({mode:'practice',topic:'all',scope:'all',query:'',id:null,doc:null});
  if(action==='practice')navigate({mode:'practice',id},{scroll:true});
  if(action==='favorite') {const old=itemState(id);updateItem(id,{favorite:!old.favorite});toast(old.favorite?'已取消收藏':'已加入我的收藏');}
  if(action==='mastery') {updateItem(id,{mastery:button.dataset.mastery});toast(`已标记为${MASTERIES[button.dataset.mastery]}`);}
  if(action==='reveal') {revealed=true;progress.items[ui.id]={...itemState(ui.id),seenAt:new Date().toISOString()};saveProgress();render();}
  if(action==='hide-answer') {revealed=false;render();}
  if(['previous','next','random'].includes(action))moveQuestion(action);
  if(action==='page-prev'||action==='page-next') {page+=action==='page-next'?1:-1;render();$('workspace').scrollIntoView({behavior:'smooth',block:'start'});}
  if(action==='read')navigate({doc:id});
});
$('export-progress').addEventListener('click',()=>{
  const date=new Date().toISOString().slice(0,10);
  downloadJSON({...progress,exportedAt:new Date().toISOString(),application:'android-study'},`安卓复习进度-${date}.json`);
  toast('进度已导出，请妥善保存文件');
});
function downloadJSON(value,filename) {
  const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json;charset=utf-8'}));
  const link=node('a',{href:url,download:filename});document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
$('import-progress').addEventListener('change',async event=>{
  const input=event.target;const file=input.files?.[0];if(!file)return;
  try {
    if(file.size>3*1024*1024)throw new Error('进度文件不能超过 3MB');
    const imported=normalizeProgress(JSON.parse(await file.text()));
    const merged=mergeProgress(progress,imported);
    progress=merged.progress;
    saveProgress();render();toast(`已导入 ${merged.count} 条进度记录，其余保留本机较新的状态`);
  }catch(error){toast(`导入未完成：${error.message || '文件内容无法识别'}`);}
  finally{input.value='';}
});
$('clean-orphans').addEventListener('click',()=>{
  if(!catalog)return;
  const ids=new Set(catalog.questions.map(q=>q.id));let count=0;
  for(const id of Object.keys(progress.items))if(!ids.has(id)){delete progress.items[id];count++;}
  saveProgress();render();toast(`已清理 ${count} 条已移除题目的记录`);
});
window.addEventListener('popstate',()=>{ui=readRoute();revealed=false;page=0;render();});
window.addEventListener('hashchange',()=>{ui=readRoute();revealed=false;page=0;render();});
window.addEventListener('storage',event=>{if(event.key===PROGRESS_KEY){progress=readProgress();render();}});
document.addEventListener('keydown',event=>{
  if(event.key==='/'&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName)){event.preventDefault();$('search-input').focus();}
});
document.querySelector('.skip-link').addEventListener('click',event=>{event.preventDefault();$('workspace').focus();$('workspace').scrollIntoView({behavior:'smooth',block:'start'});});
refreshCatalog();

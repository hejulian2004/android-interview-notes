import {apiRequest, getSession, login, logout, subscribeSession} from './api.mjs';
import {renderMarkdown} from './markdown.mjs';

const DRAFT_PREFIX = 'android-study.editor-draft.v1:';
const token = () => globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`;
const text = value => typeof value === 'string' ? value : '';
function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [name,value] of Object.entries(attrs)) {
    if (name === 'text') node.textContent = value;
    else if (name === 'class') node.className = value;
    else if (name === 'checked') node.checked = !!value;
    else if (name === 'hidden') node.hidden = !!value;
    else if (value !== undefined && value !== null) node.setAttribute(name,value);
  }
  for (const child of Array.isArray(children) ? children : [children]) if (child !== undefined && child !== null) node.append(typeof child === 'string' ? document.createTextNode(child) : child);
  return node;
}
function field(label, input, hint = '') { return el('label',{class:'admin-field'},[el('span',{},label),input,hint ? el('small',{},hint) : null]); }
function button(label, id, type = 'button') { return el('button',{type,class:'button secondary',id},label); }
function status(node,message,error = false) { node.textContent=message; node.classList.toggle('is-error',error); }
export function readEditorDraft(storage,key) { try { const value=JSON.parse(storage.getItem(DRAFT_PREFIX+key)); return value && value.version===1 && typeof value.title==='string' && typeof value.answerMarkdown==='string' ? value : null; } catch { return null; } }
export function writeEditorDraft(storage,key,value) {
  // Explicit fields prevent credentials or session data from entering draft storage.
  const safe={version:1,questionId:value.questionId||null,operation:value.operation,documentPath:value.documentPath,title:value.title,answerMarkdown:value.answerMarkdown,baseRevision:value.baseRevision,blobSha:value.blobSha,requestKey:value.requestKey,pendingDraftId:value.pendingDraftId||null,pendingOperation:value.pendingOperation||null};
  storage.setItem(DRAFT_PREFIX+key,JSON.stringify(safe));
}
export function createAdmin({getCatalog,getCurrentQuestion,onSaved=()=>{},onAuthenticated=()=>{},onLoggedOut=()=>{},notify=()=>{}}) {
  const shell=document.querySelector('.app-shell');
  const loginBox=el('section',{id:'login-screen',class:'login-screen','aria-labelledby':'login-heading'});
  const loginForm=el('form',{id:'login-form',class:'login-card',method:'post',action:'./api/login'});
  const username=el('input',{id:'login-username',name:'username',autocomplete:'username',required:'',maxlength:'100'});
  const password=el('input',{id:'login-password',name:'password',type:'password',autocomplete:'current-password',required:'',maxlength:'1024'});
  const loginStatus=el('p',{id:'login-status',class:'admin-status',role:'status','aria-live':'polite'});
  const signIn=button('登录复习室','login-submit','submit');signIn.className='button';
  loginForm.append(el('div',{class:'eyebrow'},'ANDROID STUDY'),el('h1',{id:'login-heading'},'登录你的复习室'),el('p',{class:'muted'},'题库管理与 AI 操作仅向管理员开放。学习进度仍保存在当前浏览器。'),field('管理员账号',username),field('密码',password),signIn,loginStatus);
  loginBox.append(loginForm);document.body.prepend(loginBox);
  const topbar=document.querySelector('.topbar');
  const actions=el('div',{class:'account-actions'});
  const manage=button('管理题库','admin-toggle');manage.setAttribute('aria-controls','admin-panel');manage.setAttribute('aria-expanded','false');
  const signOut=button('退出','logout-button');actions.append(manage,signOut);topbar.append(actions);
  const panel=el('section',{id:'admin-panel',class:'admin-panel',hidden:true,'aria-labelledby':'admin-heading'});
  const close=button('收起','admin-close');
  const heading=el('div',{class:'admin-panel-heading'},[el('div',{},[el('div',{class:'eyebrow'},'YOUR CONTENT DESK'),el('h2',{id:'admin-heading'},'维护你的题库')]),close]);
  const tabs=el('div',{class:'admin-tabs',role:'tablist','aria-label':'管理功能'});
  const panes={};
  for(const [id,label] of [['editor','手动编辑'],['agent','AI 对话'],['source','源码查询'],['model','模型设置']]) {
    const tab=button(label,`admin-tab-${id}`);tab.setAttribute('role','tab');tab.setAttribute('aria-controls',`admin-${id}`);tab.setAttribute('aria-selected',id==='editor'?'true':'false');tab.dataset.adminTab=id;tabs.append(tab);
    panes[id]=el('div',{id:`admin-${id}`,class:'admin-pane',role:'tabpanel','aria-labelledby':`admin-tab-${id}`,hidden:id!=='editor'});
  }
  const globalStatus=el('p',{id:'admin-global-status',class:'admin-status',role:'status'});
  panel.append(heading,el('p',{class:'admin-intro'},'手动保存会直接提交 GitHub。AI 建议先展示改动，确认后才提交。草稿仅保存在本机。'),tabs,...Object.values(panes),globalStatus);
  document.querySelector('.hero').after(panel);

  // Editor: retain server-issued versions even when a draft is restored after another edit.
  const editorForm=el('form',{id:'editor-form'});
  const questionSelect=el('select',{id:'editor-question','aria-label':'选择题目'});
  const loadQuestion=button('载入题目','editor-load');
  const createQuestion=button('新增题目','editor-new');
  const documentSelect=el('select',{id:'editor-document',required:''});
  const titleInput=el('input',{id:'editor-title',required:'',maxlength:'240'});
  const answerInput=el('textarea',{id:'editor-answer',required:'',rows:'14',maxlength:'150000',spellcheck:'false'});
  const editorMeta=el('p',{id:'editor-meta',class:'muted small'});
  const editorContext=el('div',{id:'editor-context',class:'markdown-body'});
  const contextDetails=el('details',{class:'admin-context'},[el('summary',{},'来源、追问与事实边界（只读）'),editorContext]);
  const editorStatus=el('p',{id:'editor-status',class:'admin-status',role:'status'});
  const preview=button('预览改动','editor-preview');
  const save=button('保存到 GitHub','editor-save','submit');save.className='button';
  const deleteConfirm=el('input',{id:'editor-delete-confirm',type:'checkbox'});
  const remove=button('删除这道题','editor-delete');remove.classList.add('danger');
  const diff=el('pre',{id:'editor-diff',class:'admin-diff',tabindex:'0',hidden:true,'aria-label':'题库修改差异'});
  const compareLatest=button('对比最新原文','editor-compare');
  const conflictBox=el('div',{id:'editor-conflict',hidden:true});
  const latestText=el('pre',{id:'editor-latest',class:'admin-diff',tabindex:'0','aria-label':'GitHub 最新原文'});
  const baselineConfirm=el('input',{id:'editor-baseline-confirm',type:'checkbox'});
  const adoptBaseline=button('采用此版本为保存基准','editor-adopt-baseline');
  conflictBox.append(el('p',{class:'admin-disclosure'},'下面是 GitHub 最新原文。请先把需要保留的新改动合并到上方草稿，再确认采用新的保存基准。此操作不会直接提交。'),latestText,el('label',{class:'admin-check'},[baselineConfirm,'我已比较并合并最新原文，下一次保存以此版本为基准。']),adoptBaseline);
  editorForm.append(el('div',{class:'admin-inline'},[questionSelect,loadQuestion,createQuestion]),field('新增到文档',documentSelect,'新增题目使用新的稳定题号；既有题目路径与编号保持不变。'),field('题目',titleInput),field('参考答案（Markdown）',answerInput,'保留事实边界、追问与来源。代码示例只作为文字保存。'),contextDetails,editorMeta,el('div',{class:'admin-inline'},[preview,save,compareLatest]),diff,conflictBox,el('div',{class:'admin-delete'},[el('label',{class:'admin-check'},[deleteConfirm,'我确认删除当前题目；学习记录将保留为暂不可用记录。']),remove]),editorStatus);
  panes.editor.append(editorForm);
  let edit=null, editorOperation='update', draftKey='', requestKey=token(), pending=null, editorBusy=false, latest=null;
  let editGeneration=0, loadGeneration=0, previewBusy=false, editorLockDepth=0, savedDisabled=[];
  function lockEditor(){
    if(editorLockDepth++===0){savedDisabled=[...editorForm.querySelectorAll('input,textarea,select,button')].map(control=>[control,control.disabled]);for(const [control]of savedDisabled)control.disabled=true;}
    return()=>{if(--editorLockDepth===0){for(const [control,disabled]of savedDisabled)control.disabled=disabled;savedDisabled=[];save.disabled=preview.disabled=previewBusy;remove.disabled=editorOperation==='create'||!edit;compareLatest.disabled=editorOperation==='create'||!edit;}};
  }
  const state = () => ({...edit,operation:editorOperation,title:titleInput.value,answerMarkdown:answerInput.value,documentPath:editorOperation==='create'?documentSelect.value:edit?.path,requestKey,pendingDraftId:pending?.draftId,pendingOperation:pending?.operation});
  function persist() { if(!edit)return;try{writeEditorDraft(localStorage,draftKey,state());}catch{status(editorStatus,'浏览器无法保存草稿，请复制内容备份。',true);} }
  function invalidate() {editGeneration++;pending=null;requestKey=token();diff.hidden=true;persist();}
  function renderChoices() {
    const catalog=getCatalog();const previous=questionSelect.value;
    questionSelect.replaceChildren(...(catalog?.questions||[]).map(q=>el('option',{value:q.id},`${q.number} · ${q.title}`)));
    const current=getCurrentQuestion();if((catalog?.questions||[]).some(q=>q.id===(current?.id||previous)))questionSelect.value=current?.id||previous;
    const paths=[...new Set((catalog?.questions||[]).filter(q=>q.path?.startsWith('docs/')).map(q=>q.path))];
    documentSelect.replaceChildren(...paths.map(path=>el('option',{value:path},catalog.documents?.find(d=>d.path===path)?.title||path)));
  }
  function showDraft(value,key,operation) {
    editGeneration++;
    edit=value;draftKey=key;editorOperation=operation;pending=null;requestKey=token();
    const stored=readEditorDraft(localStorage,key);
    if(stored){edit={...value,...stored};requestKey=stored.requestKey||requestKey;pending=stored.pendingDraftId?{draftId:stored.pendingDraftId,operation:stored.pendingOperation||stored.operation}:null;status(editorStatus,'已恢复本机草稿；保存时仍会检查原始版本，避免覆盖其他修改。');}
    else status(editorStatus,'');
    titleInput.value=edit.title||'';answerInput.value=edit.answerMarkdown||'';
    editorContext.innerHTML=renderMarkdown(text(value.contextMarkdown),getCatalog()?.questions.find(q=>q.id===(value.questionId||value.id))?.sourceUrl);
    contextDetails.hidden=!value.contextMarkdown;contextDetails.open=false;
    if(edit.documentPath)documentSelect.value=edit.documentPath;
    else if(edit.path?.startsWith('docs/'))documentSelect.value=edit.path;
    documentSelect.closest('label').hidden=operation!=='create';
    remove.disabled=operation==='create';compareLatest.disabled=operation==='create';deleteConfirm.checked=false;diff.hidden=true;conflictBox.hidden=true;latest=null;
    editorMeta.textContent=`${operation==='create'?'新题（保存后分配编号）':`${edit.number||''} · ${edit.path}`} · 基于 ${text(edit.baseRevision).slice(0,12)||'当前版本'}`;
  }
  async function openQuestion(id=questionSelect.value) {
    if(!id)return;const generation=++loadGeneration;editGeneration++;pending=null;const unlock=lockEditor();status(editorStatus,'正在读取可编辑原文…');
    try {const value=await apiRequest(`edit?questionId=${encodeURIComponent(id)}`);if(generation!==loadGeneration)return;showDraft(value,id,'update');questionSelect.value=id;}
    catch(error){status(editorStatus,error.message,true);}
    finally{unlock();}
  }
  function newQuestion() {
    const catalog=getCatalog();
    showDraft({title:'',answerMarkdown:'',baseRevision:catalog?.revision,documentPath:documentSelect.value},'new','create');
  }
  function changePayload(operation=editorOperation) {
    if(!edit)throw new Error('请先载入题目，或选择新增题目');
    const payload={operation,questionId:edit.questionId||edit.id,title:titleInput.value.trim(),answerMarkdown:answerInput.value,documentPath:operation==='create'?documentSelect.value:edit.path,baseRevision:edit.baseRevision,blobSha:edit.blobSha};
    if(operation!=='delete'&&(!payload.title||payload.answerMarkdown.trim().length<10))throw new Error('请填写题目及至少 10 个字符的完整答案');
    return payload;
  }
  function showDiff(value) {diff.textContent=text(value.diff)||'没有可提交的差异';diff.hidden=false;}
  async function prepare(operation=editorOperation) {
    const generation=editGeneration, scope=draftKey, payload=changePayload(operation);
    const value=await apiRequest('changes/preview',{method:'POST',body:payload});
    if(generation!==editGeneration||scope!==draftKey)throw new Error('草稿已变化，旧预览已忽略；请重新预览或保存当前内容');
    pending={...value,operation};persist();showDiff(value);return pending;
  }
  async function committed(value,storedKey=draftKey) {
    if(!value?.commit)throw new Error('服务器没有确认提交成功，草稿已保留；请重试检查');
    try{localStorage.removeItem(DRAFT_PREFIX+storedKey);}catch{}
    pending=null;requestKey=token();
    await onSaved(value);renderChoices();
    const result=value.deleted?'题目已删除': '已保存到 GitHub';
    notify(result);
    if(!value.deleted && value.questionId)await openQuestion(value.questionId);
    else {edit=null;titleInput.value='';answerInput.value='';}
    status(editorStatus,`${result} · 提交 ${value.commit.slice(0,12)}`);
  }
  async function saveEditor(operation=editorOperation) {
    if(editorBusy||previewBusy)return;
    if(operation==='delete'&&!deleteConfirm.checked){status(editorStatus,'请先勾选删除确认。',true);return;}
    editorBusy=true;loadGeneration++;const generation=editGeneration,scope=draftKey,unlock=lockEditor();
    try{
      if(pending?.operation!==operation)pending=null;
      const draft=pending?.draftId?pending:await prepare(operation);
      status(editorStatus,'正在保存到 GitHub，请勿关闭页面…');
      const value=await apiRequest('changes/commit',{method:'POST',body:{draftId:draft.draftId,idempotencyKey:requestKey}});
      if(generation!==editGeneration||scope!==draftKey||!wasAuthenticated){status(editorStatus,value.commit?'GitHub 已确认提交；当前草稿或会话已变化，草稿保持不变，请重新读取核对。':'提交结果尚未确认，草稿已保留。',!value.commit);return;}
      await committed(value);
    }catch(error){if(error.status===410){pending=null;requestKey=token();}persist();status(editorStatus,`${error.message}。草稿已保留。${error.status===409?'请点击“对比最新原文”并合并冲突；不会自动覆盖。':''}`,true);}
    finally{editorBusy=false;unlock();}
  }
  loadQuestion.addEventListener('click',()=>openQuestion());createQuestion.addEventListener('click',newQuestion);
  questionSelect.addEventListener('change',()=>openQuestion());
  editorForm.addEventListener('submit',event=>{event.preventDefault();saveEditor();});
  preview.addEventListener('click',async()=>{if(editorBusy||previewBusy)return;previewBusy=true;preview.disabled=save.disabled=true;try{await prepare();status(editorStatus,'这是提交前的改动预览，尚未写入 GitHub。');}catch(error){status(editorStatus,error.message,true);}finally{previewBusy=false;preview.disabled=save.disabled=editorLockDepth>0;}});
  remove.addEventListener('click',()=>saveEditor('delete'));
  for(const input of [titleInput,answerInput,documentSelect])input.addEventListener('input',invalidate);
  compareLatest.addEventListener('click',async()=>{
    if(!edit?.questionId)return;compareLatest.disabled=true;
    try{latest=await apiRequest(`edit?questionId=${encodeURIComponent(edit.questionId)}`);latestText.textContent=`# ${latest.title}\n\n${latest.answerMarkdown}\n\n版本：${latest.baseRevision}`;conflictBox.hidden=false;baselineConfirm.checked=false;status(editorStatus,'已读取最新原文，当前草稿保持不变。');}
    catch(error){status(editorStatus,error.message,true);}finally{compareLatest.disabled=false;}
  });
  adoptBaseline.addEventListener('click',()=>{
    if(!latest||!baselineConfirm.checked){status(editorStatus,'请先比较并勾选采用最新版本。',true);return;}
    edit={...edit,baseRevision:latest.baseRevision,blobSha:latest.blobSha};invalidate();conflictBox.hidden=true;
    editorMeta.textContent=`${edit.number||''} · ${edit.path} · 基于 ${text(edit.baseRevision).slice(0,12)}`;status(editorStatus,'已更新保存基准；草稿内容保持不变，请预览后保存。');
  });

  // AI requests never send question/source text until the corresponding explicit consent.
  const chatLog=el('div',{id:'agent-messages',class:'agent-messages','aria-live':'polite',role:'log'});
  const chatForm=el('form',{id:'agent-form'});
  const chatInput=el('textarea',{id:'agent-message',rows:'3',maxlength:'6000',required:'',placeholder:'例如：完善当前题的口述回答，并补充一个取消协程的追问。'});
  const questionConsent=el('input',{id:'agent-question-consent',type:'checkbox'});
  const questionDisclosure=el('p',{id:'agent-question-scope',class:'admin-disclosure'});
  const sourceConsent=el('input',{id:'agent-source-consent',type:'checkbox'});
  const agentRepo=el('select',{id:'agent-repository'});
  const sourcePrefixes=el('textarea',{id:'agent-source-prefixes',rows:'3',maxlength:'2000',spellcheck:'false'});
  const sourceScopeDisclosure=el('p',{id:'agent-source-scope',class:'admin-disclosure'});
  const sourceDefaults=el('p',{id:'agent-source-defaults',class:'muted small'});
  const providerDisclosure=el('p',{id:'agent-provider',class:'admin-disclosure'},'尚未配置模型。手动题库管理仍可使用。');
  const send=button('发送给模型','agent-send','submit');send.className='button';send.disabled=true;
  const newConversation=button('开始新对话','agent-new-conversation');
  const chatStatus=el('p',{id:'agent-status',class:'admin-status',role:'status'});
  const proposalBox=el('div',{id:'agent-proposal',hidden:true});
  const proposalDiff=el('pre',{id:'agent-diff',class:'admin-diff',tabindex:'0','aria-label':'AI 建议修改差异'});
  const proposalConfirm=el('input',{id:'agent-commit-confirm',type:'checkbox'});
  const privatePublicationConfirm=el('input',{id:'agent-publication-confirm',type:'checkbox'});
  const privatePublicationLabel=el('label',{id:'agent-publication-warning',class:'admin-check',hidden:true},[privatePublicationConfirm,'我确认可将建议中的内容公开到题库，已检查无私有敏感片段。授权发送私有源码给模型不代表授权公开源码。']);
  const proposalSources=el('p',{id:'agent-proposal-sources',class:'admin-disclosure',hidden:true});
  const applyProposal=button('确认并保存建议','agent-apply');applyProposal.className='button';
  proposalBox.append(el('h3',{},'建议修改 · 尚未提交'),el('p',{class:'admin-disclosure'},'保存目标：公开仓库 hejulian2004/android-interview-notes。提交后的题目和答案可被任何人阅读；请检查完整差异。'),proposalSources,proposalDiff,el('label',{class:'admin-check'},[proposalConfirm,'我已检查改动，确认直接提交上述公开 GitHub 仓库。']),privatePublicationLabel,applyProposal);
  chatForm.append(providerDisclosure,el('p',{id:'agent-history-disclosure',class:'admin-disclosure'},'同一授权范围内，最近的对话与已授权参考片段会再次发送给所示供应商，以支持连续追问。授权范围、题目或供应商变化会自动开始新对话；对话历史不保存在浏览器存储。'),field('对话内容',chatInput,'你输入的对话会发送给配置的模型供应商；不要输入密码或密钥。'),questionDisclosure,el('label',{class:'admin-check'},[questionConsent,'本次允许发送上述题目与参考答案给上述供应商。']),field('源码仓库',agentRepo),sourceDefaults,field('允许发送的路径前缀',sourcePrefixes,'每行填写一个前缀；只能在服务器允许的范围内缩小授权，修改后须重新勾选。'),sourceScopeDisclosure,el('label',{class:'admin-check'},[sourceConsent,'本次允许把上方明确仓库、版本、路径范围内的必要源码片段发送给上述供应商；私有内容也包含在此授权中。']),el('div',{class:'admin-inline'},[send,newConversation]),chatStatus);
  panes.agent.append(chatLog,chatForm,proposalBox);
  let configured=false, providerConfigVersion='', disclosedBaseUrl='',disclosedModel='',proposal=null, proposalKey=token(), repos=[];
  let conversationId=token(), conversationScope=null, wasAuthenticated=false, chatBusy=false, disclosedQuestionId=null;
  function resetConversation(note='已开始新对话，后续请求不会使用此前的对话历史。',scope=null){conversationId=token();conversationScope=scope;chatLog.replaceChildren();if(note)status(chatStatus,note);}
  newConversation.addEventListener('click',()=>resetConversation());
  function questionChanged(){
    const question=getCurrentQuestion(),id=question?.id||null;
    questionDisclosure.textContent=question?`当前题目：${question.number||''} ${question.title||''}（${id}）`:'当前没有选定题目；选择题目后才能授权发送参考答案。';
    questionConsent.disabled=!id;
    if(disclosedQuestionId!==id){disclosedQuestionId=id;questionConsent.checked=false;resetConversation('当前题目已变化，请重新核对并勾选题目授权。');}
  }
  function allowedPrefixes(repo){const prefixes=repo?.allowedPathPrefixes||repo?.safeAllowedPathPrefixes;return Array.isArray(prefixes)?prefixes.filter(value=>typeof value==='string'&&value.length>0):[];}
  function selectedSourceScope(){
    const repo=repos.find(value=>value.repository===agentRepo.value),allowed=allowedPrefixes(repo);
    const pathPrefixes=[...new Set(sourcePrefixes.value.split(/[\n,]/).map(value=>value.trim()).filter(Boolean))].sort();
    const valid=repo&&/^[a-f\d]{40}$/.test(repo.revision||'')&&allowed.length>0&&pathPrefixes.length>0&&pathPrefixes.length<=20&&pathPrefixes.every(prefix=>!/[\\\u0000-\u001f]/.test(prefix)&&!prefix.startsWith('/')&&!prefix.split('/').some(part=>part==='.'||part==='..')&&allowed.some(base=>prefix===base||prefix.startsWith(base.endsWith('/')?base:base+'/')));
    return {repository:repo?.repository,private:repo?.private===true,revision:repo?.revision,pathPrefixes,valid:!!valid};
  }
  function showSourceScope(resetPrefixes=false){
    const repo=repos.find(value=>value.repository===agentRepo.value),allowed=allowedPrefixes(repo);
    if(resetPrefixes)sourcePrefixes.value=allowed.join('\n');
    sourceDefaults.textContent=allowed.length?`服务器允许范围（只读）：${allowed.join('、')}`:'服务器尚未提供可授权的安全路径范围。';
    const scope=selectedSourceScope();
    sourceConsent.disabled=!scope.valid;if(!scope.valid)sourceConsent.checked=false;
    sourceScopeDisclosure.textContent=scope.valid?`仓库：${scope.repository}（${scope.private?'私有':'公开'}）\n版本：${scope.revision}\n供应商：${disclosedBaseUrl||'未配置'} · 模型：${disclosedModel||'未配置'}\n本次可发送范围：${scope.pathPrefixes.join('、')}`:'源码外发未授权：请加载有效的仓库完整版本，并填写服务器允许范围内的路径前缀。';
  }
  for(const control of [questionConsent,sourceConsent])control.addEventListener('change',()=>resetConversation('授权范围已变化，已开始新对话。'));
  agentRepo.addEventListener('change',()=>{sourceConsent.checked=false;showSourceScope(true);resetConversation('源码仓库已变化，旧授权已清除；请核对新范围后重新勾选。');});
  sourcePrefixes.addEventListener('input',()=>{sourceConsent.checked=false;showSourceScope();resetConversation('源码路径范围已变化，请重新核对并勾选授权。');});
  function renderProposal(){
    proposalBox.hidden=!proposal;proposalConfirm.checked=privatePublicationConfirm.checked=false;
    privatePublicationLabel.hidden=proposal?.privateSourceUsed!==true&&proposal?.requiresPublicConfirmation!==true;proposalSources.hidden=!proposal?.sourceDisclosure;
    if(proposal){proposalDiff.textContent=text(proposal.diff);proposalSources.textContent=typeof proposal.sourceDisclosure==='string'?proposal.sourceDisclosure:JSON.stringify(proposal.sourceDisclosure||{},null,2);}
  }
  function preserveProposal(){try{if(proposal)localStorage.setItem(DRAFT_PREFIX+'agent-proposal',JSON.stringify({version:1,proposal:{draftId:proposal.draftId,diff:proposal.diff,questionId:proposal.questionId,baseRevision:proposal.baseRevision,privateSourceUsed:proposal.privateSourceUsed===true,requiresPublicConfirmation:proposal.requiresPublicConfirmation===true,sourceDisclosure:proposal.sourceDisclosure},requestKey:proposalKey}));else localStorage.removeItem(DRAFT_PREFIX+'agent-proposal');}catch{status(chatStatus,'无法持久保存 AI 建议，请保留当前页面或复制差异备份。',true);}}
  function message(role,content) {chatLog.append(el('div',{class:`agent-message agent-${role}`},[el('strong',{},role==='user'?'你':'Agent'),el('p',{},content)]));while(chatLog.children.length>30)chatLog.firstElementChild.remove();}
  chatForm.addEventListener('submit',async event=>{
    event.preventDefault();if(!configured||chatBusy)return;
    const content=chatInput.value.trim();if(!content)return;
    questionChanged();
    const allowQuestionExport=questionConsent.checked,allowSourceExport=sourceConsent.checked;
    const questionId=allowQuestionExport?getCurrentQuestion()?.id:undefined,sourceScope=selectedSourceScope();
    if(allowSourceExport&&!sourceScope.valid){sourceConsent.checked=false;status(chatStatus,'源码范围无效，请重新加载并核对仓库、版本与路径后授权。',true);return;}
    const scope=JSON.stringify([providerConfigVersion,allowQuestionExport,questionId||null,allowSourceExport,allowSourceExport?sourceScope:null]);
    if(conversationScope!==null&&conversationScope!==scope)resetConversation('授权范围已变化，已开始新对话。',scope);
    conversationScope=scope;
    const requestConversation=conversationId;
    chatBusy=true;send.disabled=true;status(chatStatus,'正在请求模型；修改只会生成建议…');message('user',content);
    try{
      if(allowSourceExport)await apiRequest('source/authorize',{method:'POST',body:{repository:sourceScope.repository,allowModelExport:true,revision:sourceScope.revision,providerConfigVersion,pathPrefixes:sourceScope.pathPrefixes}});
      if(requestConversation!==conversationId)return;
      const value=await apiRequest('agent/chat',{method:'POST',body:{message:content,questionId,allowQuestionExport,sourceRepository:sourceScope.repository||undefined,sourceRevision:sourceScope.revision||undefined,allowSourceExport,providerConfigVersion,conversationId:requestConversation}});
      if(requestConversation!==conversationId)return;
      if(value.historyReset){chatLog.replaceChildren();message('user',content);}
      message('assistant',text(value.reply)||'本次调用已结束。');chatInput.value='';
      if(Array.isArray(value.citations)&&value.citations.length)message('assistant',value.citations.map(c=>typeof c==='string'?c:`${c.repository||''}@${c.revision||''} ${c.path||''}:${c.startLine||c.line||''}`).join('\n'));
      proposal=value.proposal?{...value.proposal,privateSourceUsed:value.privateSourceUsed===true||value.proposal.privateSourceUsed===true,sourceDisclosure:value.proposal.sourceDisclosure||value.sourceDisclosure}:null;proposalKey=token();renderProposal();preserveProposal();
      status(chatStatus,(value.historyReset?'对话上下文已重置或精简，请按当前授权继续。':'')+(proposal?'建议已生成，请检查差异；尚未写入 GitHub。':'对话完成，未写入 GitHub。'));
    }catch(error){if(requestConversation!==conversationId)return;if(error.status===409||error.code==='supplier_config_changed'){questionConsent.checked=sourceConsent.checked=false;await loadManagement();status(chatStatus,`${error.message}。已重新加载范围，请核对新版本与供应商并重新勾选授权。`,true);}else status(chatStatus,error.message,true);}
    finally{chatBusy=false;send.disabled=!configured;}
  });
  applyProposal.addEventListener('click',async()=>{
    if(!proposal?.draftId)return;
    if(!proposalConfirm.checked){status(chatStatus,'请先检查差异并勾选提交确认。',true);return;}
    if((proposal.privateSourceUsed===true||proposal.requiresPublicConfirmation===true)&&!privatePublicationConfirm.checked){status(chatStatus,'建议涉及私有源码授权范围；请确认已检查无敏感片段，并明确同意公开到题库。',true);return;}
    applyProposal.disabled=true;
    try{const value=await apiRequest('changes/commit',{method:'POST',body:{draftId:proposal.draftId,idempotencyKey:proposalKey,confirmPublicPublication:privatePublicationConfirm.checked}});if(!value.commit)throw new Error('提交尚未确认');await onSaved(value);proposal=null;preserveProposal();proposalBox.hidden=true;status(chatStatus,`建议已提交 · ${value.commit.slice(0,12)}`);notify('AI 建议已保存到 GitHub');}
    catch(error){status(chatStatus,`${error.message}。建议仍保留，未确认成功前不会标记为已保存。`,true);}
    finally{applyProposal.disabled=false;}
  });

  // Source tools expose only repositories registered on the server.
  const sourceForm=el('form',{id:'source-form'});
  const sourceRepo=el('select',{id:'source-repository'});
  const sourceQuery=el('input',{id:'source-query',type:'search',required:'',maxlength:'500',placeholder:'输入类名、方法名或关键词'});
  const search=button('查询源码','source-search','submit');
  const sourceStatus=el('p',{id:'source-status',class:'admin-status',role:'status'});
  const sourceResults=el('div',{id:'source-results',class:'source-results'});
  sourceForm.append(el('p',{class:'admin-disclosure'},'只读查询服务器已授权的仓库；每次结果固定源码版本。其他仓库须先由管理员在服务器登记，查询不会自动发送给模型。'),field('已授权仓库',sourceRepo),field('检索关键词',sourceQuery),search,sourceStatus);
  panes.source.append(sourceForm,sourceResults);
  sourceForm.addEventListener('submit',async event=>{
    event.preventDefault();search.disabled=true;status(sourceStatus,'正在查询已授权源码…');sourceResults.replaceChildren();
    try{
      const value=await apiRequest('source/search',{method:'POST',body:{query:sourceQuery.value.trim(),repository:sourceRepo.value}});
      const results=value.results||value.matches||[];
      for(const result of results){
        const info=el('div',{class:'source-result'});
        const line=result.line||result.startLine||1;
        info.append(el('strong',{},`${result.path||''}:${line}`),el('small',{},`${result.repository||sourceRepo.value}@${result.revision||value.revision||''}`),el('pre',{class:'source-snippet'},text(result.text)||text(result.content)||text(result.snippet)));
        const read=button('读取附近内容');read.addEventListener('click',async()=>{read.disabled=true;try{const source=await apiRequest('source/read',{method:'POST',body:{repository:result.repository||sourceRepo.value,revision:result.revision||value.revision,path:result.path,startLine:Math.max(1,line-8),endLine:line+40}});info.querySelector('pre').textContent=text(source.content)||text(source.text); }catch(error){status(sourceStatus,error.message,true);}finally{read.disabled=false;}});info.append(read);sourceResults.append(info);
      }
      status(sourceStatus,`找到 ${results.length} 处结果${value.truncated?'（达到结果上限）':''}。版本：${text(value.revision).slice(0,12)}`);
    }catch(error){status(sourceStatus,error.message,true);}finally{search.disabled=false;}
  });

  const modelForm=el('form',{id:'model-form'});
  const baseUrl=el('input',{id:'model-base-url',type:'url',maxlength:'2048',placeholder:'https://api.example.com/v1',autocomplete:'off'});
  const modelName=el('input',{id:'model-name',maxlength:'200',autocomplete:'off'});
  const modelKey=el('input',{id:'model-key',type:'password',autocomplete:'new-password',maxlength:'4096'});
  const clearKey=el('input',{id:'model-clear-key',type:'checkbox'});
  const modelStatus=el('p',{id:'model-status',class:'admin-status',role:'status'});
  const saveModel=button('保存模型设置','model-save','submit');saveModel.className='button';
  modelForm.append(el('p',{class:'admin-disclosure'},'模型请求由本站服务器发起。Base URL 必须在服务器供应商允许列表中；填写新的地址不会自动扩大访问权限。密钥不会返回页面，也不保存到本机草稿。当前管理设置保存在服务进程内，重启后的配置由部署设置决定。费用限额还应在供应商侧设置。'),field('兼容 API 的 Base URL',baseUrl),field('模型名称',modelName),field('API Key',modelKey,'留空保留服务端已有密钥。保存后会立即清空此输入框。'),el('label',{class:'admin-check'},[clearKey,'清除服务器保存的模型密钥']),saveModel,modelStatus);
  panes.model.append(modelForm);
  function showModel(value) {
    if(providerConfigVersion!==text(value.configVersion)){questionConsent.checked=sourceConsent.checked=false;resetConversation('供应商配置已变化，已开始新对话。');}
    providerConfigVersion=text(value.configVersion);
    disclosedBaseUrl=text(value.baseUrl);disclosedModel=text(value.model);
    configured=value.configured===true;send.disabled=!configured||chatBusy;
    baseUrl.value=text(value.baseUrl);modelName.value=text(value.model);modelKey.value='';clearKey.checked=false;
    let supplier='未配置供应商';try{if(baseUrl.value)supplier=new URL(baseUrl.value).origin;}catch{configured=false;send.disabled=true;}
    providerDisclosure.textContent=configured?`本次供应商：${supplier} · 模型：${modelName.value}。仅发送你勾选授权的题目或必要源码片段。`:'模型尚未配置或配置不完整，AI 暂不可用；手动题库编辑仍可使用。';
    showSourceScope();
    status(modelStatus,`模型${configured?'已启用':'未启用'} · 密钥${value.keyConfigured?'已在服务端配置':'未配置'}`);
  }
  modelForm.addEventListener('submit',async event=>{
    event.preventDefault();saveModel.disabled=true;
    const body={baseUrl:baseUrl.value.trim(),model:modelName.value.trim(),clearKey:clearKey.checked};if(modelKey.value)body.key=modelKey.value;
    modelKey.value='';
    try{const value=await apiRequest('settings/model',{method:'PUT',body});showModel(value);questionConsent.checked=sourceConsent.checked=false;status(modelStatus,'模型设置已保存。下一次发送前请重新确认内容授权。');}
    catch(error){status(modelStatus,error.message,true);}finally{saveModel.disabled=false;}
  });
  async function loadManagement() {
    renderChoices();questionChanged();
    const values=await Promise.allSettled([apiRequest('settings/model'),apiRequest('source/repos')]);
    if(values[0].status==='fulfilled')showModel(values[0].value);else{configured=false;send.disabled=true;status(modelStatus,values[0].reason.message,true);}
    if(values[1].status==='fulfilled'){
      const previousScope=selectedSourceScope();
      repos=values[1].value.repositories||[];
      for(const select of [sourceRepo,agentRepo]){const previous=select.value;select.replaceChildren(...repos.map(repo=>el('option',{value:repo.repository},`${repo.repository}${repo.private?'（私有）':'（公开）'}`)));if(repos.some(repo=>repo.repository===previous))select.value=previous;}
      const currentRepo=repos.find(repo=>repo.repository===agentRepo.value);
      if(previousScope.repository!==currentRepo?.repository||previousScope.revision!==currentRepo?.revision||previousScope.private!==!!currentRepo?.private){sourceConsent.checked=false;showSourceScope(true);resetConversation('源码版本或仓库范围已更新，请重新核对授权。');}
      else showSourceScope();
    }else status(sourceStatus,values[1].reason.message,true);
    if(!edit&&questionSelect.value)await openQuestion();
    if(!proposal){try{const stored=JSON.parse(localStorage.getItem(DRAFT_PREFIX+'agent-proposal'));if(stored?.version===1&&typeof stored.proposal?.draftId==='string'&&typeof stored.proposal?.diff==='string'){proposal=stored.proposal;proposalKey=stored.requestKey||token();renderProposal();status(chatStatus,'已恢复本机 AI 建议；提交时服务器仍会检查草稿有效期与版本。');}}catch{}}
  }
  manage.addEventListener('click',async()=>{panel.hidden=!panel.hidden;manage.setAttribute('aria-expanded',String(!panel.hidden));if(!panel.hidden){await loadManagement();panel.scrollIntoView({block:'start',behavior:'smooth'});}});
  close.addEventListener('click',()=>{panel.hidden=true;manage.setAttribute('aria-expanded','false');manage.focus();});
  tabs.addEventListener('click',event=>{const id=event.target.closest('[data-admin-tab]')?.dataset.adminTab;if(!id)return;for(const [key,pane]of Object.entries(panes)){pane.hidden=key!==id;document.getElementById(`admin-tab-${key}`).setAttribute('aria-selected',String(key===id));}});
  function setAuthenticated(value) {
    const signed=!!value?.authenticated;shell.hidden=!signed;loginBox.hidden=signed;
    if(signed&&!wasAuthenticated)resetConversation('');
    wasAuthenticated=signed;
    if(!signed){
      editGeneration++;loadGeneration++;
      panel.hidden=true;modelKey.value='';password.value='';questionConsent.checked=sourceConsent.checked=false;
      resetConversation('');chatInput.value='';proposal=null;proposalBox.hidden=true;proposalDiff.textContent='';sourceResults.replaceChildren();sourcePrefixes.value='';sourceScopeDisclosure.textContent='';disclosedQuestionId=null;questionDisclosure.textContent='';
      titleInput.value='';answerInput.value='';editorContext.replaceChildren();diff.textContent='';questionSelect.replaceChildren();documentSelect.replaceChildren();
      edit=null;pending=null;latest=null;latestText.textContent='';conflictBox.hidden=true;configured=false;send.disabled=true;
      onLoggedOut();
    }
  }
  subscribeSession(setAuthenticated);
  loginForm.addEventListener('submit',async event=>{
    event.preventDefault();signIn.disabled=true;status(loginStatus,'正在验证身份…');
    const supplied=password.value;password.value='';
    try{await login(username.value.trim(),supplied);status(loginStatus,'');await onAuthenticated();}
    catch(error){status(loginStatus,error.message,true);}finally{signIn.disabled=false;}
  });
  signOut.addEventListener('click',async()=>{signOut.disabled=true;try{await logout();status(loginStatus,'已退出，服务器会话已撤销。');}catch(error){notify(`退出未完成：${error.message}`);}finally{signOut.disabled=false;}});
  setAuthenticated(null);
  return {async start(){try{await getSession();await onAuthenticated();return true;}catch(error){if(error.status!==401)status(loginStatus,error.message,true);return false;}}, refreshChoices:renderChoices,questionChanged, openEditor:async id=>{panel.hidden=false;await loadManagement();await openQuestion(id);}};
}

import test, {after} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM} from 'jsdom';
import {setTimeout as delay} from 'node:timers/promises';

const dom=new JSDOM(readFileSync(new URL('../src/index.html',import.meta.url),'utf8'),{url:'https://study.example/android-study/',pretendToBeVisual:true});
for(const key of ['window','document','Node','HTMLElement','localStorage','location','history'])Object.defineProperty(globalThis,key,{configurable:true,writable:true,value:key==='window'?dom.window:dom.window[key]});
dom.window.HTMLElement.prototype.scrollIntoView=function(){};
after(()=>dom.window.close());
const {createAdmin,readEditorDraft,writeEditorDraft}=await import('../src/admin.mjs');
const {apiRequest}=await import('../src/api.mjs');
const id='docs/android-interview-handbook.md#n01';
const revision='a'.repeat(40);
const question={id,path:'docs/android-interview-handbook.md',number:'N01',title:'原始题目',answerMarkdown:'这是原始参考答案，保留代码与事实边界。'};
let activeQuestion=question;
const privateRepository='example/private-project',privateRevision='e'.repeat(40);
const catalog={revision,questions:[question],documents:[{path:question.path,title:'面试手册'}]};
const requests=[];let authenticated=false,refreshNeeded=false,refreshCount=0,loginCount=0,logoutCount=0,commitMode='success',commits=0,previewCount=0,configured=false,lastVersion=revision,providerVersion='provider-version',modelConfigCounter=0,resetNextHistory=false,holdNextChat=false,releaseChat=null,holdNextPreview=false,releasePreview=null,holdNextCommit=false,releaseCommit=null,holdMetadata=false,releaseModel=null,releaseSources=null,sourcePending=false;
const response=(value,status=200)=>({ok:status>=200&&status<300,status,json:async()=>value});
const fail=(code,message,status)=>response({error:{code,message}},status);
globalThis.fetch=async(url,options)=>{
  const parsed=new URL(url);assert.equal(parsed.origin,location.origin);assert.ok(parsed.pathname.startsWith('/android-study/api/'));
  assert.equal(options.credentials,'same-origin');assert.equal(options.cache,'no-store');
  const path=parsed.pathname.split('/api/')[1]+parsed.search;const body=options.body?JSON.parse(options.body):null;
  requests.push({path,body,method:options.method,csrf:options.headers['X-CSRF-Token']});
  if(path==='session'){
    if(refreshNeeded)return response({error:{code:'access_expired',message:'已过期'},needsRefresh:true,csrfToken:'refresh-csrf'},401);
    return authenticated?response({authenticated:true,user:'admin',csrfToken:'csrf',expiresAt:Date.now()+900000}):fail('unauthorized','请登录',401);
  }
  if(path==='login'){loginCount++;authenticated=body.username==='admin'&&body.password==='test-password';return authenticated?response({authenticated:true,user:'admin',csrfToken:'csrf'}):fail('invalid_login','账号或密码不正确',401);}
  if(path==='session/refresh'){assert.ok(['csrf','refresh-csrf'].includes(options.headers['X-CSRF-Token']));refreshNeeded=false;authenticated=true;refreshCount++;return response({authenticated:true,user:'admin',csrfToken:'csrf'});}
  if(!authenticated)return fail('unauthorized','请登录',401);
  if(options.method!=='GET')assert.equal(options.headers['X-CSRF-Token'],'csrf');
  if(path==='logout'){authenticated=false;logoutCount++;return response({ok:true});}
  if(path==='settings/model'&&options.method==='GET'){
    const value={configured,baseUrl:configured?'https://model.example/v1':'',model:configured?'test-model':'',keyConfigured:configured,configVersion:providerVersion};
    if(holdMetadata)return new Promise(resolve=>{releaseModel=()=>resolve(response(value));});return response(value);
  }
  if(path==='settings/model'){configured=body.clearKey?false:!!body.key||configured;providerVersion='provider-version-'+(++modelConfigCounter);return response({configured,baseUrl:body.baseUrl,model:body.model,keyConfigured:configured,configVersion:providerVersion});}
  if(path==='source/repos'){
    const value={repositories:[{repository:'hejulian2004/android-interview-notes',private:false,allowModelExport:false,revision,allowedPathPrefixes:['docs/']},{repository:privateRepository,private:true,allowModelExport:false,revision:privateRevision,allowedPathPrefixes:['app/src/'],available:true}]};
    if(sourcePending)value.repositories=value.repositories.map(repo=>({repository:repo.repository,private:null,revision:null,allowedPathPrefixes:[],available:false,pending:true}));
    if(holdMetadata)return new Promise(resolve=>{releaseSources=()=>resolve(response(value));});return response(value);
  }
  if(path.startsWith('edit?'))return response({...question,questionId:id,baseRevision:lastVersion,blobSha:'b'.repeat(40),sourceKind:'guide'});
  if(path==='changes/preview'){
    previewCount++;const value={draftId:'draft-'+previewCount,diff:'--- previous\n+++ proposed\n- old\n+ <script>example</script>',baseRevision:body.baseRevision,questionId:body.questionId||id,changedPaths:[question.path]};
    if(holdNextPreview){holdNextPreview=false;return new Promise(resolve=>{releasePreview=()=>resolve(response(value));});}return response(value);
  }
  if(path==='changes/commit'){
    commits++;if(holdNextCommit){holdNextCommit=false;return new Promise(resolve=>{releaseCommit=()=>resolve(fail('github_failed','GitHub 暂不可用',503));});}
    if(commitMode==='failure')return fail('github_failed','GitHub 暂不可用',503);
    if(commitMode==='conflict')return fail('conflict','文档已有新修改',409);
    if(commitMode==='expired')return fail('draft_expired','草稿已过期',410);
    return response({commit:'c'.repeat(40),questionId:id,deleted:false});
  }
  if(path==='agent/chat'){
    const privateScope=body.allowSourceExport&&body.sourceRepository===privateRepository;
    const value={reply:'这是改进建议。',proposal:{draftId:'agent-draft',diff:'- 原答案\n+ 改进答案',questionId:id,requiresPublicConfirmation:privateScope},citations:[],usage:{},historyReset:resetNextHistory,privateSourceUsed:false,sourceDisclosure:privateScope?{repository:privateRepository,private:true,revision:privateRevision,pathPrefixes:['app/src/main/']}:undefined};resetNextHistory=false;
    if(holdNextChat){holdNextChat=false;return new Promise(resolve=>{releaseChat=()=>resolve(response(value));});}
    return response(value);
  }
  if(path==='source/authorize')return response({ok:true});
  if(path==='source/search')return response({revision,results:[{path:'README.md',line:3,text:'Android 复习资料',revision,repository:'hejulian2004/android-interview-notes'}]});
  if(path==='source/read')return response({content:'固定版本的附近源码内容',revision});
  throw new Error('Unexpected endpoint '+path);
};
let authenticatedCalls=0,savedCalls=0,loggedOutCalls=0;
const progressRaw=JSON.stringify({version:1,items:{[id]:{favorite:true,mastery:'mastered'}}});localStorage.setItem('android-study.progress.v1',progressRaw);
const administration=createAdmin({getCatalog:()=>catalog,getCurrentQuestion:()=>activeQuestion,onAuthenticated:()=>{authenticatedCalls++;},onSaved:()=>{savedCalls++;},onLoggedOut:()=>{loggedOutCalls++;}});
const $=id=>document.getElementById(id);
function input(id,value){$(id).value=value;$(id).dispatchEvent(new dom.window.Event('input',{bubbles:true}));}
function submit(id){$(id).dispatchEvent(new dom.window.Event('submit',{bubbles:true,cancelable:true}));}
async function until(predicate){for(let i=0;i<200&&!predicate();i++)await delay(5);assert.ok(predicate(),'expected asynchronous UI state');}

test('login gates business requests; cookies and CSRF remain in-memory',async()=>{
  assert.equal(await administration.start(),false);assert.equal(requests.length,1);assert.equal(requests[0].path,'session');
  assert.equal(document.querySelector('.app-shell').hidden,true);assert.equal($('login-screen').hidden,false);
  assert.equal($('login-password').type,'password');assert.equal($('login-password').autocomplete,'current-password');
  input('login-username','admin');input('login-password','test-password');submit('login-form');
  await until(()=>authenticatedCalls===1);assert.equal(loginCount,1);assert.equal($('login-password').value,'');
  assert.equal($('login-screen').hidden,true);assert.equal(document.querySelector('.app-shell').hidden,false);
  assert.equal(localStorage.getItem('android-study.progress.v1'),progressRaw);
  assert.ok(!Object.keys(localStorage).some(key=>/jwt|token|csrf/i.test(key)));
});

test('editor becomes usable while unrelated model settings and source metadata are still pending',async()=>{
  holdMetadata=true;$('admin-toggle').click();
  await until(()=>$('editor-title').value==='原始题目'&&releaseModel&&releaseSources);
  assert.equal($('editor-save').disabled,false);
  assert.equal($('agent-send').disabled,true);
  assert.equal(requests.filter(r=>r.path.startsWith('edit?')).length,1);
  releaseModel();await until(()=>$('model-status').textContent.includes('未启用'));
  assert.equal($('source-refresh').disabled,true);
  releaseSources();holdMetadata=false;await until(()=>!$('source-refresh').disabled);
  $('admin-close').click();
});

test('manual drafts use original versions, safe diff and idempotent retries without losing progress',async()=>{
  $('admin-toggle').click();await until(()=>$('editor-title').value==='原始题目');
  assert.equal($('agent-send').disabled,true);
  input('editor-title','改进后的问题');input('editor-answer','新的参考答案，保留完整追问与事实边界。');
  const stored=readEditorDraft(localStorage,id);assert.equal(stored.baseRevision,revision);assert.equal(stored.title,'改进后的问题');
  const before=commits;$('editor-preview').click();await until(()=>!$('editor-diff').hidden);
  assert.equal(commits,before);assert.match($('editor-diff').textContent,/<script>example<\/script>/);assert.equal($('editor-diff').querySelector('script'),null);
  commitMode='failure';submit('editor-form');await until(()=>$('editor-status').textContent.includes('草稿已保留'));
  const first=requests.filter(r=>r.path==='changes/commit').at(-1);
  assert.equal(readEditorDraft(localStorage,id).title,'改进后的问题');assert.equal(savedCalls,0);
  commitMode='success';submit('editor-form');await until(()=>savedCalls===1);
  const second=requests.filter(r=>r.path==='changes/commit').at(-1);
  assert.deepEqual(second.body,first.body);assert.equal(readEditorDraft(localStorage,id),null);
  assert.equal(localStorage.getItem('android-study.progress.v1'),progressRaw);
  assert.match($('editor-status').textContent,/已保存到 GitHub/);
});

test('visible Agent shortcut opens chat directly even without a model, preserves context and returns focus',async()=>{
  $('admin-close').click();
  const before=requests.filter(r=>r.path.startsWith('edit?')).length;
  assert.match($('agent-launch').textContent,/AI 助手.*Agent/);
  assert.equal($('agent-launch').closest('.app-shell').hidden,false);
  $('agent-launch').click();
  assert.equal($('admin-panel').hidden,false);assert.equal($('admin-agent').hidden,false);assert.equal($('admin-editor').hidden,true);
  assert.equal($('admin-tab-agent').getAttribute('aria-selected'),'true');assert.equal($('agent-launch').getAttribute('aria-expanded'),'true');
  assert.equal(document.activeElement,$('agent-message'));assert.match($('agent-provider').textContent,/模型尚未配置|尚未配置模型/);
  assert.equal($('agent-send').disabled,true);assert.match($('agent-question-scope').textContent,/原始题目/);
  $('agent-launch').click();assert.equal($('admin-panel').hidden,false);assert.equal($('admin-agent').hidden,false);
  assert.equal(requests.filter(r=>r.path.startsWith('edit?')).length,before);
  $('admin-close').click();assert.equal($('admin-panel').hidden,true);assert.equal(document.activeElement,$('agent-launch'));
  assert.equal($('agent-launch').getAttribute('aria-expanded'),'false');
  $('admin-toggle').click();assert.equal($('admin-editor').hidden,false);
});

test('conflict resolution explicitly compares latest source and keeps draft until user adopts baseline',async()=>{
  input('editor-title','冲突草稿');input('editor-answer','保留这份手动草稿，并合并别人补充的新内容。');
  commitMode='conflict';submit('editor-form');await until(()=>$('editor-status').textContent.includes('对比最新原文'));
  assert.equal(readEditorDraft(localStorage,id).baseRevision,revision);
  lastVersion='d'.repeat(40);$('editor-compare').click();await until(()=>!$('editor-conflict').hidden);
  assert.ok(requests.filter(r=>r.path.startsWith('edit?')).at(-1).path.endsWith('&fresh=1'));
  assert.match($('editor-latest').textContent,new RegExp(lastVersion));assert.equal($('editor-title').value,'冲突草稿');
  $('editor-adopt-baseline').click();assert.equal(readEditorDraft(localStorage,id).baseRevision,revision);
  $('editor-baseline-confirm').checked=true;$('editor-adopt-baseline').click();
  assert.equal(readEditorDraft(localStorage,id).baseRevision,lastVersion);assert.equal($('editor-title').value,'冲突草稿');
  commitMode='success';submit('editor-form');await until(()=>savedCalls===2);
  assert.equal(requests.filter(r=>r.path==='changes/preview').at(-1).body.baseRevision,lastVersion);
});

test('delete requires confirmation and a failed deletion cannot be reused by normal save',async()=>{
  const before=commits;$('editor-delete').click();assert.equal(commits,before);assert.match($('editor-status').textContent,/勾选删除确认/);
  $('editor-delete-confirm').checked=true;commitMode='failure';$('editor-delete').click();await until(()=>commits===before+1&&!$('editor-save').disabled);
  const deletedDraft=requests.filter(r=>r.path==='changes/commit').at(-1).body.draftId;
  commitMode='success';submit('editor-form');await until(()=>savedCalls===3);
  const update=requests.filter(r=>r.path==='changes/commit').at(-1);
  assert.notEqual(update.body.draftId,deletedDraft);assert.equal(requests.filter(r=>r.path==='changes/preview').at(-1).body.operation,'update');
});

test('model keys are transmitted once and never returned to inputs/drafts; AI writes require diff confirmation',async()=>{
  input('model-base-url','https://model.example/v1');input('model-name','test-model');input('model-key','example-key-never-persist');submit('model-form');
  await until(()=>!$('agent-send').disabled);assert.equal($('model-key').value,'');assert.equal(localStorage.getItem('android-study.progress.v1'),progressRaw);
  assert.ok(!Object.values(localStorage).some(value=>String(value).includes('example-key-never-persist')));
  const before=commits;input('agent-message','先给我一个修改建议');submit('agent-form');await until(()=>!$('agent-proposal').hidden);
  const chat=requests.filter(r=>r.path==='agent/chat').at(-1);
  assert.equal(chat.body.allowQuestionExport,false);assert.equal(chat.body.questionId,undefined);assert.equal(chat.body.allowSourceExport,false);assert.equal(chat.body.providerConfigVersion,providerVersion);
  assert.equal(commits,before);$('agent-apply').click();assert.equal(commits,before);assert.match($('agent-status').textContent,/勾选提交确认/);
  $('agent-commit-confirm').checked=true;$('agent-apply').click();await until(()=>savedCalls===4);
  assert.equal(requests.filter(r=>r.path==='changes/commit').at(-1).body.confirmPublicPublication,false);
  assert.equal($('agent-proposal').hidden,true);assert.equal(localStorage.getItem('android-study.editor-draft.v1:agent-proposal'),null);
});

test('source search is same-origin, pinned reads and explicit model export stay separate',async()=>{
  const chatBefore=requests.filter(r=>r.path==='agent/chat').length;
  input('source-query','Android');submit('source-form');await until(()=>document.querySelector('.source-result'));
  assert.equal(requests.filter(r=>r.path==='agent/chat').length,chatBefore);
  document.querySelector('.source-result button').click();await until(()=>document.querySelector('.source-result pre').textContent.includes('固定版本'));
  assert.equal(requests.filter(r=>r.path==='source/read').at(-1).body.revision,revision);
  $('agent-question-consent').checked=true;$('agent-source-consent').checked=true;input('agent-message','结合已授权源码完善当前题');submit('agent-form');await until(()=>requests.filter(r=>r.path==='agent/chat').length===chatBefore+1);
  const chat=requests.filter(r=>r.path==='agent/chat').at(-1);assert.equal(chat.body.questionId,id);assert.equal(chat.body.allowSourceExport,true);
  assert.equal(requests.filter(r=>r.path==='source/authorize').at(-1).body.allowModelExport,true);
  assert.equal(requests.filter(r=>r.path==='source/authorize').at(-1).body.revision,revision);
  assert.equal(requests.filter(r=>r.path==='source/authorize').at(-1).body.providerConfigVersion,providerVersion);
  assert.deepEqual(requests.filter(r=>r.path==='source/authorize').at(-1).body.pathPrefixes,['docs/']);
  assert.equal(chat.body.sourceRevision,revision);
});

test('followups retain memory-only conversation IDs; reset, scope and supplier changes start fresh context',async()=>{
  await until(()=>!$('agent-send').disabled);
  const chats=()=>requests.filter(r=>r.path==='agent/chat');
  const original=chats().at(-1).body.conversationId;assert.match(original,/^[A-Za-z0-9_-]{16,100}$/);
  let count=chats().length;input('agent-message','继续解释上一个回答中的边界');submit('agent-form');await until(()=>chats().length===count+1&&!$('agent-send').disabled);
  assert.equal(chats().at(-1).body.conversationId,original);assert.equal(chats().at(-1).body.history,undefined);
  assert.ok(!Object.values(localStorage).some(value=>String(value).includes(original)));
  $('agent-new-conversation').click();assert.equal($('agent-messages').textContent,'');
  count=chats().length;input('agent-message','开始一个全新问题');submit('agent-form');await until(()=>chats().length===count+1&&!$('agent-send').disabled);
  const fresh=chats().at(-1).body.conversationId;assert.notEqual(fresh,original);
  $('agent-source-consent').checked=false;$('agent-source-consent').dispatchEvent(new dom.window.Event('change',{bubbles:true}));assert.equal($('agent-messages').textContent,'');
  count=chats().length;input('agent-message','本次不要使用源码');submit('agent-form');await until(()=>chats().length===count+1&&!$('agent-send').disabled);
  const scopeId=chats().at(-1).body.conversationId;assert.notEqual(scopeId,fresh);assert.equal(chats().at(-1).body.allowSourceExport,false);
  const oldProviderVersion=providerVersion;input('model-name','different-model');submit('model-form');await until(()=>providerVersion!==oldProviderVersion&&!$('model-save').disabled);
  assert.equal($('agent-messages').textContent,'');assert.equal($('agent-question-consent').checked,false);
  count=chats().length;input('agent-message','使用新的模型继续');submit('agent-form');await until(()=>chats().length===count+1&&!$('agent-send').disabled);
  assert.notEqual(chats().at(-1).body.conversationId,scopeId);assert.equal(chats().at(-1).body.providerConfigVersion,providerVersion);
  resetNextHistory=true;count=chats().length;input('agent-message','服务重置后继续');submit('agent-form');await until(()=>chats().length===count+1&&!$('agent-send').disabled);
  assert.match($('agent-status').textContent,/对话上下文已重置或精简/);assert.equal($('agent-messages').children.length,2);
  assert.match($('agent-history-disclosure').textContent,/最近的对话/);
});

test('resetting a conversation suppresses an in-flight response from the old scope',async()=>{
  holdNextChat=true;releaseChat=null;input('agent-message','这个响应将属于旧对话');submit('agent-form');await until(()=>typeof releaseChat==='function');
  $('agent-new-conversation').click();releaseChat();await until(()=>!$('agent-send').disabled);
  assert.equal($('agent-messages').textContent,'');assert.match($('agent-status').textContent,/已开始新对话/);
});

test('reload can recover expired access with refresh CSRF; logout clears visible content without deleting drafts/progress',async()=>{
  await until(()=>!$('agent-send').disabled);refreshNeeded=true;await administration.start();assert.equal(refreshCount,1);
  input('editor-title','退出前保留的草稿');input('editor-answer','这个草稿应该在退出之后仍然保存在本地。');
  $('logout-button').click();await until(()=>logoutCount===1&&document.querySelector('.app-shell').hidden);
  assert.equal(document.querySelector('.app-shell').hidden,true);assert.equal($('login-screen').hidden,false);assert.equal($('editor-answer').value,'');assert.equal($('agent-messages').textContent,'');
  assert.equal(readEditorDraft(localStorage,id).title,'退出前保留的草稿');assert.equal(localStorage.getItem('android-study.progress.v1'),progressRaw);assert.ok(loggedOutCalls>=2);
  await assert.rejects(apiRequest('https://evil.example/api'),/无效的接口路径/);
  const previous=requests.filter(r=>r.path==='agent/chat').at(-1).body.conversationId;
  const beforeAuth=authenticatedCalls;input('login-username','admin');input('login-password','test-password');submit('login-form');await until(()=>authenticatedCalls===beforeAuth+1);
  $('admin-toggle').click();await until(()=>!$('agent-send').disabled);
  const count=requests.filter(r=>r.path==='agent/chat').length;input('agent-message','重新登录后开始');submit('agent-form');await until(()=>requests.filter(r=>r.path==='agent/chat').length===count+1&&!$('agent-send').disabled);
  assert.notEqual(requests.filter(r=>r.path==='agent/chat').at(-1).body.conversationId,previous);
});

test('draft allowlist excludes unknown secret fields and corrupt drafts recover safely',()=>{
  writeEditorDraft(localStorage,'probe',{title:'草稿',answerMarkdown:'参考答案',operation:'create',key:'never-store',jwt:'never-store',csrfToken:'never-store'});
  assert.ok(!localStorage.getItem('android-study.editor-draft.v1:probe').includes('never-store'));
  localStorage.setItem('android-study.editor-draft.v1:broken','{invalid');assert.equal(readEditorDraft(localStorage,'broken'),null);
});

test('stale preview cannot replace a newer draft; in-flight saves lock fields and restore them after failure',async()=>{
  input('editor-title','预览前的旧内容');input('editor-answer','原先输入的参考答案，有完整解释和边界。');
  holdNextPreview=true;releasePreview=null;$('editor-preview').click();await until(()=>typeof releasePreview==='function');
  const oldDraft='draft-'+previewCount;
  assert.equal($('editor-answer').disabled,false);assert.equal($('editor-save').disabled,true);
  input('editor-title','预览期间输入的新内容');input('editor-answer','这是预览返回之前修改的新答案，绝不能被旧预览覆盖。');
  releasePreview();await until(()=>$('editor-status').textContent.includes('旧预览已忽略'));
  assert.equal($('editor-diff').hidden,true);assert.equal(readEditorDraft(localStorage,id).pendingDraftId,null);
  assert.equal(readEditorDraft(localStorage,id).title,'预览期间输入的新内容');
  holdNextCommit=true;releaseCommit=null;submit('editor-form');await until(()=>typeof releaseCommit==='function');
  for(const control of document.querySelectorAll('#editor-form input,#editor-form textarea,#editor-form select,#editor-form button'))assert.equal(control.disabled,true,control.id+' locked while saving');
  assert.notEqual(requests.filter(r=>r.path==='changes/commit').at(-1).body.draftId,oldDraft);
  assert.equal(requests.filter(r=>r.path==='changes/preview').at(-1).body.title,'预览期间输入的新内容');
  const retryBody=requests.filter(r=>r.path==='changes/commit').at(-1).body;
  releaseCommit();await until(()=>$('editor-status').textContent.includes('草稿已保留')&&!$('editor-save').disabled);
  for(const id of ['editor-answer','editor-title','editor-question','editor-load','editor-new','editor-compare','editor-adopt-baseline'])assert.equal($(id).disabled,false,id+' restored after failure');
  assert.equal(readEditorDraft(localStorage,id).title,'预览期间输入的新内容');
  const savedBefore=savedCalls;submit('editor-form');await until(()=>savedCalls===savedBefore+1);
  assert.deepEqual(requests.filter(r=>r.path==='changes/commit').at(-1).body,retryBody);
  assert.equal(localStorage.getItem('android-study.progress.v1'),progressRaw);
  assert.equal(document.querySelector('#login-form').getAttribute('method'),'post');
  assert.equal(new URL(document.querySelector('#login-form').getAttribute('action'),document.baseURI).origin,location.origin);
});

test('switching from an authorized public repo to private source clears consent and pins explicit narrowed grant',async()=>{
  await until(()=>!$('agent-send').disabled);
  $('agent-repository').value='hejulian2004/android-interview-notes';$('agent-repository').dispatchEvent(new dom.window.Event('change',{bubbles:true}));
  $('agent-source-consent').checked=true;
  const grants=requests.filter(r=>r.path==='source/authorize').length;
  $('agent-repository').value=privateRepository;$('agent-repository').dispatchEvent(new dom.window.Event('change',{bubbles:true}));
  assert.equal($('agent-source-consent').checked,false);assert.equal($('agent-source-consent').disabled,false);
  assert.match($('agent-source-scope').textContent,/私有/);assert.match($('agent-source-scope').textContent,new RegExp(privateRevision));assert.match($('agent-source-scope').textContent,/app\/src\//);
  let chats=requests.filter(r=>r.path==='agent/chat').length;input('agent-message','暂时不发送新仓库内容');submit('agent-form');await until(()=>requests.filter(r=>r.path==='agent/chat').length===chats+1&&!$('agent-send').disabled);
  assert.equal(requests.filter(r=>r.path==='source/authorize').length,grants);assert.equal(requests.filter(r=>r.path==='agent/chat').at(-1).body.allowSourceExport,false);
  input('agent-source-prefixes','app/src/main/');assert.equal($('agent-source-consent').checked,false);
  $('agent-source-consent').checked=true;input('model-base-url','https://unsaved-supplier.example/v1');
  // Editing an unsaved configuration field cannot change the supplier disclosed by the authorization UI.
  $('agent-source-prefixes').dispatchEvent(new dom.window.Event('input',{bubbles:true}));
  assert.equal($('agent-source-consent').checked,false);assert.match($('agent-source-scope').textContent,/https:\/\/model\.example\/v1/);assert.doesNotMatch($('agent-source-scope').textContent,/unsaved-supplier/);
  $('agent-source-consent').checked=true;chats=requests.filter(r=>r.path==='agent/chat').length;input('agent-message','只查看已明确授权的范围');submit('agent-form');await until(()=>requests.filter(r=>r.path==='agent/chat').length===chats+1&&!$('agent-send').disabled);
  const grant=requests.filter(r=>r.path==='source/authorize').at(-1).body;
  assert.deepEqual(grant,{repository:privateRepository,allowModelExport:true,revision:privateRevision,providerConfigVersion:providerVersion,pathPrefixes:['app/src/main/']});
  const chat=requests.filter(r=>r.path==='agent/chat').at(-1).body;assert.equal(chat.sourceRevision,privateRevision);assert.equal(chat.allowSourceExport,true);
  assert.equal($('agent-publication-warning').hidden,false);
  assert.equal(JSON.parse(localStorage.getItem('android-study.editor-draft.v1:agent-proposal')).proposal.requiresPublicConfirmation,true);
  const before=commits;$('agent-commit-confirm').checked=true;$('agent-apply').click();assert.equal(commits,before);assert.match($('agent-status').textContent,/私有源码/);
  $('agent-publication-confirm').checked=true;const saved=savedCalls;$('agent-apply').click();await until(()=>savedCalls===saved+1);
  assert.equal(requests.filter(r=>r.path==='changes/commit').at(-1).body.confirmPublicPublication,true);
});

test('changing the selected question immediately revokes its prior export consent',async()=>{
  $('agent-question-consent').checked=true;
  activeQuestion={...question,id:question.path+'#n02',number:'N02',title:'切换后的题目'};administration.questionChanged();
  assert.equal($('agent-question-consent').checked,false);assert.match($('agent-question-scope').textContent,/N02/);
  const count=requests.filter(r=>r.path==='agent/chat').length;input('agent-message','不发送新题的答案');submit('agent-form');await until(()=>requests.filter(r=>r.path==='agent/chat').length===count+1&&!$('agent-send').disabled);
  const chat=requests.filter(r=>r.path==='agent/chat').at(-1).body;assert.equal(chat.allowQuestionExport,false);assert.equal(chat.questionId,undefined);
  activeQuestion=question;administration.questionChanged();
});


test('pending source caches remain queryable but cannot be authorized for model export',async()=>{
  sourcePending=true;const before=requests.filter(r=>r.path==='source/repos').length;
  $('agent-source-consent').checked=true;$('source-refresh').click();
  await until(()=>requests.filter(r=>r.path==='source/repos').length===before+1&&!$('source-refresh').disabled);
  assert.match($('source-status').textContent,/后台准备/);assert.match($('source-repository').selectedOptions[0].textContent,/准备中/);
  assert.equal($('source-repository').selectedOptions[0].disabled,false);
  assert.equal($('agent-source-consent').checked,false);assert.equal($('agent-source-consent').disabled,true);
  sourcePending=false;$('source-refresh').click();await until(()=>!$('source-refresh').disabled&&!$('agent-source-consent').disabled);
});

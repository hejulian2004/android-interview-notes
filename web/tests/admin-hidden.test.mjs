import test,{after} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM} from 'jsdom';
import {setTimeout as delay} from 'node:timers/promises';
import {AGENT_ENABLED} from '../src/features.mjs';
const dom=new JSDOM(readFileSync(new URL('../src/index.html',import.meta.url),'utf8'),{url:'https://study.example/android-study/#practice?id=docs%2Fguide.md%23n01',pretendToBeVisual:true});
for(const key of ['window','document','Node','HTMLElement','localStorage','location','history'])Object.defineProperty(globalThis,key,{configurable:true,writable:true,value:key==='window'?dom.window:dom.window[key]});
dom.window.HTMLElement.prototype.scrollIntoView=function(){};
Object.defineProperty(window,'innerWidth',{configurable:true,writable:true,value:1280});
after(()=>dom.window.close());
const {createAdmin}=await import('../src/admin.mjs');
const id='docs/guide.md#n01',path='docs/guide.md',revision='a'.repeat(40);
const rows=new Map([[id,{id,questionId:id,path,number:'N01',title:'现有题目',answerMarkdown:'现有完整参考答案，保留来源与边界。'}]]);
const catalog={revision,questions:[...rows.values()],documents:[{path,title:'指南'}]};
const requests=[];let draft=null,commits=0,saved=0;
const response=value=>({ok:true,status:200,json:async()=>value});
globalThis.fetch=async(url,options)=>{
  const endpoint=new URL(url).pathname.split('/api/')[1],body=options.body?JSON.parse(options.body):null;
  assert.equal(new URL(url).origin,location.origin);assert.equal(options.credentials,'same-origin');requests.push({endpoint,body});
  if(endpoint==='session')return response({authenticated:true,user:'admin',csrfToken:'csrf',expiresAt:Date.now()+900000});
  if(options.method!=='GET')assert.equal(options.headers['X-CSRF-Token'],'csrf');
  if(endpoint==='edit')return response({...rows.get(new URL(url).searchParams.get('questionId')),baseRevision:catalog.revision,blobSha:'b'.repeat(40),sourceKind:'guide'});
  if(endpoint==='changes/preview'){draft={...body,questionId:body.operation==='create'?path+'#n02':body.questionId};return response({draftId:'draft-'+commits,questionId:draft.questionId,operation:draft.operation,diff:'- 原内容\n+ 手动修改',baseRevision:catalog.revision});}
  if(endpoint==='changes/commit'){
    commits++;if(draft.operation==='delete')rows.delete(draft.questionId);else rows.set(draft.questionId,{id:draft.questionId,questionId:draft.questionId,path,number:draft.operation==='create'?'N02':'N01',title:draft.title,answerMarkdown:draft.answerMarkdown});
    catalog.revision=String(commits).repeat(40);catalog.questions=[...rows.values()];return response({commit:catalog.revision,questionId:draft.questionId,deleted:draft.operation==='delete'});
  }
  throw new Error('Unexpected disabled feature request '+endpoint);
};
const aiDraft='{"version":1,"proposal":{"draftId":"keep-existing-agent-draft","diff":"keep exact content"}}';
localStorage.setItem('android-study.editor-draft.v1:agent-proposal',aiDraft);
localStorage.setItem('android-study.progress.v1','{"version":1,"items":{"unchanged":{"favorite":true}}}');
const originalGet=dom.window.Storage.prototype.getItem;let aiDraftReads=0;
dom.window.Storage.prototype.getItem=function(key){if(key==='android-study.editor-draft.v1:agent-proposal')aiDraftReads++;return originalGet.call(this,key);};
document.body.classList.add('agent-sidebar-open','agent-drawer-modal');
for(const node of [document.querySelector('.app-shell'),document.querySelector('.skip-link')]){node.setAttribute('inert','');node.setAttribute('aria-hidden','true');}
history.replaceState({androidStudyAgentDrawer:'old-ui-marker',preserve:'other-state'},'',location.href);const route=location.href;
const administration=createAdmin({getCatalog:()=>catalog,getCurrentQuestion:()=>rows.get(id),onSaved:()=>{saved++;}});
const $=id=>document.getElementById(id);
const input=(id,value)=>{$(id).value=value;$(id).dispatchEvent(new dom.window.Event('input',{bubbles:true}));};
const submit=id=>$(id).dispatchEvent(new dom.window.Event('submit',{bubbles:true,cancelable:true}));
async function until(predicate){for(let i=0;i<200&&!predicate();i++)await delay(5);assert.ok(predicate(),'expected asynchronous UI state');}

test('production default hides the assistant and clears only its stale presentation state',async()=>{
  assert.equal(AGENT_ENABLED,false);assert.equal(await administration.start(),true);
  assert.equal($('agent-launch').hidden,true);assert.equal($('agent-drawer').hidden,true);assert.equal($('agent-backdrop').hidden,true);
  assert.equal(document.body.classList.contains('agent-sidebar-open'),false);assert.equal(document.body.classList.contains('agent-drawer-modal'),false);
  assert.equal(document.querySelector('.app-shell').hasAttribute('inert'),false);assert.equal(document.querySelector('.skip-link').hasAttribute('inert'),false);
  assert.equal(document.querySelector('.app-shell').getAttribute('aria-hidden'),null);assert.equal(history.state.androidStudyAgentDrawer,undefined);assert.equal(history.state.preserve,'other-state');assert.equal(location.href,route);
  assert.doesNotMatch($('login-form').textContent,/AI|Agent/);assert.equal(aiDraftReads,0);assert.equal(originalGet.call(localStorage,'android-study.editor-draft.v1:agent-proposal'),aiDraft);
});

test('desktop/mobile history, resize and hidden handlers cannot reopen or request disabled tools',async()=>{
  for(const width of [1280,390,320]){
    window.innerWidth=width;document.body.classList.add('agent-sidebar-open','agent-drawer-modal');$('agent-drawer').hidden=false;
    history.replaceState({androidStudyAgentDrawer:'old-'+width,preserve:'other-state'},'',location.href);
    window.dispatchEvent(new dom.window.Event('resize'));window.dispatchEvent(new dom.window.PopStateEvent('popstate'));
    $('agent-launch').click();$('source-refresh').click();submit('source-form');submit('model-form');submit('agent-form');$('agent-apply').dispatchEvent(new dom.window.Event('click'));
    assert.equal($('agent-drawer').hidden,true);assert.equal($('agent-launch').hidden,true);assert.equal(document.querySelector('.app-shell').hasAttribute('inert'),false);assert.equal(location.href,route);assert.equal(history.state.preserve,'other-state');
    $('search-input').focus();assert.equal(document.activeElement,$('search-input'));
  }
  await delay(10);assert.deepEqual(requests.map(x=>x.endpoint),['session']);assert.equal(aiDraftReads,0);
});

test('default management keeps manual edit/create/preview/save/delete working without AI metadata',async()=>{
  $('admin-toggle').click();await until(()=>$('editor-title').value==='现有题目');
  assert.doesNotMatch(document.querySelector('.admin-intro').textContent,/AI|Agent/);assert.equal($('admin-panel').hidden,false);
  input('editor-title','改好的题目');input('editor-answer','这份手动补充的参考答案包含原理与明确边界。');$('editor-preview').click();await until(()=>!$('editor-diff').hidden);
  assert.equal(commits,0);assert.match($('editor-diff').textContent,/手动修改/);submit('editor-form');await until(()=>saved===1&&!$('editor-save').disabled);assert.equal(rows.get(id).title,'改好的题目');
  $('editor-new').click();input('editor-title','手动新增练习');input('editor-answer','这是手动新建的完整答案，并保留可口述原理与边界。');$('editor-preview').click();await until(()=>!$('editor-diff').hidden);submit('editor-form');await until(()=>saved===2&&!$('editor-save').disabled);
  assert.equal(rows.get(path+'#n02').title,'手动新增练习');assert.equal(requests.filter(x=>x.endpoint==='changes/preview').at(-1).body.operation,'create');
  $('editor-delete-confirm').checked=true;$('editor-delete').click();await until(()=>saved===3&&!$('editor-save').disabled);assert.equal(rows.has(path+'#n02'),false);
  assert.ok(requests.every(x=>['session','edit','changes/preview','changes/commit'].includes(x.endpoint)));
  assert.equal(aiDraftReads,0);assert.equal(originalGet.call(localStorage,'android-study.editor-draft.v1:agent-proposal'),aiDraft);assert.equal(originalGet.call(localStorage,'android-study.progress.v1'),'{"version":1,"items":{"unchanged":{"favorite":true}}}');
});

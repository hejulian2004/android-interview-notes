import test, { after } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { cp, mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { setTimeout as delay } from 'node:timers/promises';
import { JSDOM } from 'jsdom';

const html=readFileSync(new URL('../src/index.html',import.meta.url),'utf8');
const snapshot=JSON.parse(readFileSync(new URL('../engine/snapshot.json',import.meta.url),'utf8'));
const docPath='docs/android-interview-handbook.md';
const id=docPath+'#n01';
const dom=new JSDOM(html,{url:'https://study.example/android-study/#reading?doc='+encodeURIComponent(docPath)+'&anchor=network',pretendToBeVisual:true});
for(const key of ['window','document','Node','HTMLElement','localStorage','location','history']) {
  Object.defineProperty(globalThis,key,{configurable:true,writable:true,value:key==='window'?dom.window:dom.window[key]});
}
const scrolled=[];
dom.window.HTMLElement.prototype.scrollIntoView=function(){scrolled.push(this.dataset.markdownAnchor||this.id);};
localStorage.setItem('android-study.progress.v1',JSON.stringify({version:1,items:{[id]:{favorite:true,mastery:'mastered'}}}));
const businessRequests=[];
let catalogUpdated=false;
globalThis.fetch=async (url,options)=>{
  const parsed=new URL(url),path=parsed.pathname;businessRequests.push([path,options.method]);
  assert.equal(new URL(url).origin,'https://study.example');
  assert.equal(options.credentials,'same-origin');
  if(path.endsWith('/api/session'))return {ok:true,status:200,json:async()=>({authenticated:true,user:'admin',csrfToken:'test-csrf',expiresAt:Date.now()+900000})};
  if(path.endsWith('/api/catalog'))return {ok:true,status:200,json:async()=>({...snapshot,...(catalogUpdated?{revision:'d'.repeat(40)}:{}),origin:'server-cache',refreshing:false,fetchedAt:'2026-11-01T00:00:00Z'})};
  if(path.endsWith('/api/catalog/refresh')){catalogUpdated=true;return {ok:true,status:200,json:async()=>({...snapshot,origin:'server-cache',cacheStatus:'stale',refreshing:true,fetchedAt:'2026-11-02T00:00:00Z'})};}
  if(path.endsWith('/api/settings/model'))return {ok:true,status:200,json:async()=>({configured:false,keyConfigured:false,configVersion:'fixture-provider'})};
  if(path.endsWith('/api/source/repos'))return {ok:true,status:200,json:async()=>({repositories:[]})};
  if(path.endsWith('/api/edit'))return {ok:true,status:200,json:async()=>({id,questionId:id,number:'N01',path:docPath,title:'Fixture question',answerMarkdown:'A complete answer for this mock edit.',baseRevision:snapshot.revision,blobSha:'b'.repeat(40),sourceKind:'guide'})};
  if(path.endsWith('/api/changes/preview'))return {ok:true,status:200,json:async()=>({draftId:'mock-draft',questionId:id,diff:'- previous\n+ updated'})};
  if(path.endsWith('/api/changes/commit'))return {ok:true,status:200,json:async()=>({commit:'c'.repeat(40),questionId:id,deleted:false})};
  throw new Error('Unexpected business request '+path);
};
// Exercise the actual static assembly contract: src/* and engine/ share a root.
const assembly=await mkdtemp(join(tmpdir(),'android-study-markdown-'));
await cp(new URL('../src/',import.meta.url),assembly,{recursive:true});
await cp(new URL('../engine/',import.meta.url),join(assembly,'engine'),{recursive:true});
await writeFile(join(assembly,'package.json'),'{"type":"module"}');
after(async()=>{dom.window.close();await rm(assembly,{recursive:true,force:true});});
await import(pathToFileURL(join(assembly,'app.mjs')).href);
for(let attempt=0;!document.querySelector('.document-view')&&attempt<200;attempt++)await delay(10);

test('direct reading hash opens its source anchor while stable-ID progress remains intact',()=>{
  assert.equal(document.querySelector('#total-count').textContent,'371');
  assert.equal(document.querySelector('#mastered-count').textContent,'1');
  assert.ok(scrolled.includes('network'));
  assert.equal(document.activeElement.dataset.markdownAnchor,'network');
  assert.equal(JSON.parse(localStorage.getItem('android-study.progress.v1')).items[id].mastery,'mastered');
});

test('a real table-of-contents link scrolls locally and retains SPA route state',()=>{
  const link=[...document.querySelectorAll('.document-view a[data-markdown-anchor]')].find(a=>a.dataset.markdownAnchor==='q-n01');
  assert.ok(link);
  assert.match(link.getAttribute('href'),/^#reading\?doc=/);
  assert.equal(new URLSearchParams(link.getAttribute('href').split('?')[1]).get('anchor'),'q-n01');
  const event=new dom.window.MouseEvent('click',{bubbles:true,cancelable:true});
  link.dispatchEvent(event);
  assert.equal(event.defaultPrevented,true);
  assert.equal(document.activeElement.dataset.markdownAnchor,'q-n01');
  const params=new URLSearchParams(location.hash.split('?')[1]);
  assert.equal(params.get('doc'),docPath);assert.equal(params.get('anchor'),'q-n01');
  assert.equal(document.querySelector('#mastered-count').textContent,'1');
});

test('a compatible relative Markdown link opens another reading document; source-only links keep safe fallback',()=>{
  document.querySelector('[data-action="read"][data-id="docs/flutter-interview-guide.md"]').click();
  const link=[...document.querySelectorAll('.document-view a[data-document-path]')].find(a=>a.dataset.documentPath==='docs/sdk-source-deep-dive.md');
  assert.ok(link);
  const event=new dom.window.MouseEvent('click',{bubbles:true,cancelable:true});
  link.dispatchEvent(event);
  assert.equal(event.defaultPrevented,true);
  assert.match(document.querySelector('.document-view h1').textContent,/Rust SDK/);
  assert.equal(new URLSearchParams(location.hash.split('?')[1]).get('doc'),'docs/sdk-source-deep-dive.md');
  assert.equal(JSON.parse(localStorage.getItem('android-study.progress.v1')).items[id].favorite,true);
});

test('actual practice navigation clears question export consent when the selected ID changes',()=>{
  document.querySelector('[data-mode="practice"]').click();
  const consent=document.querySelector('#agent-question-consent');assert.equal(consent.disabled,false);
  consent.checked=true;
  const before=document.querySelector('#agent-question-scope').textContent;
  document.querySelector('[data-action="next"]').click();
  assert.equal(consent.checked,false);assert.notEqual(document.querySelector('#agent-question-scope').textContent,before);
});

test('a confirmed save reads the committed server cache; explicit refresh still checks GitHub',async()=>{
  document.querySelector('#admin-toggle').click();
  for(let attempt=0;!document.querySelector('#editor-title').value&&attempt<100;attempt++)await delay(5);
  const answer=document.querySelector('#editor-answer');answer.value='Updated complete answer for the mocked confirmed commit.';answer.dispatchEvent(new dom.window.Event('input',{bubbles:true}));
  const before=businessRequests.length;
  document.querySelector('#editor-form').dispatchEvent(new dom.window.Event('submit',{bubbles:true,cancelable:true}));
  for(let attempt=0;!document.querySelector('#editor-status').textContent.includes('已保存到 GitHub')&&attempt<100;attempt++)await delay(5);
  assert.match(document.querySelector('#editor-status').textContent,/已保存到 GitHub/);
  const afterSave=businessRequests.slice(before);
  assert.ok(afterSave.some(([path])=>path.endsWith('/api/catalog')));
  assert.ok(!afterSave.some(([path])=>path.endsWith('/api/catalog/refresh')));
  document.querySelector('#refresh-catalog').click();
  for(let attempt=0;!businessRequests.some(([path])=>path.endsWith('/api/catalog/refresh'))&&attempt<100;attempt++)await delay(5);
  assert.ok(businessRequests.some(([path,method])=>path.endsWith('/api/catalog/refresh')&&method==='POST'));
  assert.equal(JSON.parse(localStorage.getItem('android-study.progress.v1')).items[id].favorite,true);
  for(let attempt=0;document.querySelector('#refresh-catalog').disabled&&attempt<100;attempt++)await delay(5);
  document.querySelector('[data-scope="favorites"]').click();const selectedRoute=location.hash;
  for(let attempt=0;!document.querySelector('#revision-label').textContent.includes('ddddddd')&&attempt<400;attempt++)await delay(10);
  assert.match(document.querySelector('#revision-label').textContent,/ddddddd/);
  assert.equal(location.hash,selectedRoute);assert.equal(JSON.parse(localStorage.getItem('android-study.progress.v1')).items[id].favorite,true);
  assert.equal(businessRequests.filter(([path])=>path.endsWith('/api/catalog/refresh')).length,1);
  // Keep the fixture DOM alive until the UI's existing toast timeout completes.
  for(let attempt=0;(!document.querySelector('#toast').hidden||document.querySelector('#refresh-catalog').disabled)&&attempt<400;attempt++)await delay(10);
});

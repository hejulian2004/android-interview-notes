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
globalThis.fetch=async (url,options)=>{
  const path=new URL(url).pathname;
  assert.equal(new URL(url).origin,'https://study.example');
  assert.equal(options.credentials,'same-origin');
  if(path.endsWith('/api/session'))return {ok:true,status:200,json:async()=>({authenticated:true,user:'admin',csrfToken:'test-csrf',expiresAt:Date.now()+900000})};
  if(path.endsWith('/api/catalog'))return {ok:true,status:200,json:async()=>({...snapshot,origin:'server-cache',fetchedAt:'2026-11-01T00:00:00Z'})};
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

import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { JSDOM } from 'jsdom';
import { parseMarkdownSources } from '../engine/index.mjs';

const dom = new JSDOM('<!doctype html><body></body>', { url:'https://study.example/android-study/' });
globalThis.window = dom.window;
globalThis.document = dom.window.document;
const { renderMarkdown, resolveMarkdownLink } = await import('../src/markdown.mjs');
const source = 'https://github.com/hejulian2004/android-interview-notes/blob/main/docs/flutter-interview-guide.md';
const options = { documentPath:'docs/flutter-interview-guide.md', idPrefix:'test-' };
const fixture = readFileSync(new URL('./fixture-markdown-edge.md',import.meta.url),'utf8');
function render(text, extra={}) {
  const root = document.createElement('div');
  root.innerHTML = renderMarkdown(text,source,{...options,...extra});
  return root;
}

test('mature GFM rendering preserves headings, formatting, nested lists, tables, quotes, links and rules',()=>{
  const root=render(fixture+'\n\n---\n');
  assert.equal(root.querySelector('h1').textContent,'Markdown QA fixture');
  assert.ok(root.querySelector('strong'));assert.ok(root.querySelector('em'));assert.ok(root.querySelector('del'));
  assert.ok(root.querySelector('ol li ul li'));assert.ok(root.querySelector('blockquote strong'));
  assert.equal(root.querySelectorAll('thead th').length,3);assert.ok(root.querySelector('.table-scroll table'));
  assert.ok(root.querySelector('hr'));assert.ok(root.querySelector('p code'));
  assert.equal(root.querySelector('.table-scroll').tabIndex,0);
});

test('known fenced languages get local syntax highlighting; all code remains exact inert text',()=>{
  const samples={
    kotlin:'data class Reply(val message: String)\nfun main() { println("<script>literal</script>") }',
    java:'public class Answer { public static void main(String[] args) {} }',
    dart:'void main() { final answer = 42; print(answer); }',
    rust:'fn main() { let answer = "<img onerror=alert(1)>"; println!("{}", answer); }',
    xml:'<LinearLayout android:orientation="vertical"><TextView /></LinearLayout>',
    javascript:'const answer = "</code><script>alert(1)</script>";',
    sql:'SELECT title FROM questions WHERE mastered = true;',
  };
  for(const [language,code] of Object.entries(samples)) {
    const root=render('```'+language+'\n'+code+'\n```');
    assert.equal(root.querySelector('pre code').textContent,code+'\n',language);
    assert.ok(root.querySelector('pre code span[class*="hljs-"]'),language);
    assert.ok(root.querySelector('.code-language-label').textContent.length);
    assert.equal(root.querySelector('pre').tabIndex,0);
    assert.equal(root.querySelector('script, img, iframe'),null);
  }
});

test('unknown and absent fence languages are escaped plain text without automatic detection',()=>{
  const code='<script>globalThis.executed = true</script>\n<a id="fake-anchor-in-code"></a>';
  for(const lang of ['not-a-real-language','']) {
    const root=render('```'+lang+'\n'+code+'\n```');
    assert.equal(root.querySelector('code').textContent,code+'\n');
    assert.equal(root.querySelector('code span'),null);
    assert.equal(root.querySelector('script,[data-markdown-anchor="fake-anchor-in-code"]'),null);
    assert.match(root.querySelector('.code-language-label').textContent,/纯文本/);
  }
});

test('raw HTML, event handlers, dangerous links and image trackers never become executable nodes',()=>{
  const root=render(fixture+'\n\n<iframe srcdoc="<script>alert(1)</script>"></iframe>\n\n[encoded](javascript&#58;alert%281%29)');
  assert.equal(root.querySelector('script,img,iframe,object,embed,form,style'),null);
  assert.equal(root.querySelector('[onclick],[onerror],[onload],[srcdoc],[style]'),null);
  for(const a of root.querySelectorAll('a[href]')) {
    assert.ok(!/^\s*(?:javascript|data|vbscript):/i.test(a.getAttribute('href')));
    if(a.getAttribute('href').startsWith('http')) {
      assert.equal(a.target,'_blank');assert.match(a.rel,/noopener/);assert.match(a.rel,/noreferrer/);
    }
  }
  assert.equal(root.querySelector('[data-markdown-anchor="unsafe"]'),null);
});

test('explicit source anchors and duplicate heading slugs are namespaced and safe',()=>{
  const root=render(fixture);
  assert.ok(root.querySelector('span[data-markdown-anchor="network"]'));
  assert.ok(root.querySelector('span[data-markdown-anchor="q01"]'));
  const headings=[...root.querySelectorAll('h3')].filter(h=>h.textContent==='Duplicate heading');
  assert.equal(headings.length,2);assert.notEqual(headings[0].id,headings[1].id);
  assert.ok([...root.querySelectorAll('[id]')].every(el=>el.id.startsWith('test-')));
  assert.equal(new Set([...root.querySelectorAll('[id]')].map(el=>el.id)).size,root.querySelectorAll('[id]').length);
  const link=[...root.querySelectorAll('a')].find(a=>a.textContent==='Jump to Q01');
  assert.equal(link.dataset.markdownAnchor,'q01');assert.equal(link.dataset.documentPath,options.documentPath);
  assert.equal(link.getAttribute('href'),'#'+root.querySelector('span[data-markdown-anchor="q01"]').id);
});

test('relative Markdown links keep repository path/source revision and carry inert navigation metadata',()=>{
  const link=resolveMarkdownLink('sdk-source-deep-dive.md#21-abi',source,options.documentPath);
  assert.equal(link.documentPath,'docs/sdk-source-deep-dive.md');assert.equal(link.anchor,'21-abi');
  assert.match(link.href,/\/blob\/main\/docs\/sdk-source-deep-dive\.md#21-abi$/);
  const root=render(fixture);
  const relative=[...root.querySelectorAll('a')].find(a=>a.textContent==='relative reading link');
  assert.equal(relative.dataset.documentPath,'docs/sdk-source-deep-dive.md');
  const original=[...root.querySelectorAll('a')].find(a=>a.textContent==='source-only link');
  assert.match(original.href,/\/blob\/main\/sources\/S004\.md$/);
  assert.equal(resolveMarkdownLink('javascript:alert(1)',source,options.documentPath).href,'');
});

test('real handbook and Flutter TOC targets survive parsing and sanitized rendering without changing IDs',()=>{
  const snapshot=JSON.parse(readFileSync(new URL('../engine/snapshot.json',import.meta.url)));
  const catalog=parseMarkdownSources(snapshot.files,{revision:snapshot.revision});
  assert.equal(catalog.questions.length,371);
  for(const [suffix,anchors] of [['android-interview-handbook.md',['network','agent','android','intern','q-n01']],['flutter-interview-guide.md',['q01','q52']]]) {
    const doc=catalog.documents.find(d=>d.path.endsWith(suffix));
    const root=document.createElement('div');root.innerHTML=renderMarkdown(doc.markdown,doc.sourceUrl,{documentPath:doc.id,idPrefix:'real-'});
    for(const anchor of anchors)assert.ok(root.querySelector(`span[data-markdown-anchor="${anchor}"]`),`${suffix} ${anchor}`);
    assert.equal(root.querySelector('script,img,iframe'),null);
  }
  assert.ok(catalog.questions.some(q=>q.id==='docs/android-interview-handbook.md#n01'));
});

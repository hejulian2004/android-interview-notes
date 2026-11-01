import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { JSDOM } from 'jsdom';
import { parseMarkdownSources } from '../engine/index.mjs';
import { Marked } from '../src/vendor/marked.esm.js';

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

test('real N01 screenshot labels and Chinese punctuation followed by Latin technical words render as strong',()=>{
  const examples=[
    ['**面试回答：**它是面向移动端的远程服务器管理与协作工具。','面试回答：'],
    ['**追问：**你的贡献和使用开源库有什么区别？','追问：'],
    ['**代码事实：**以下问题围绕当前简历的 SDK 展开。','代码事实：'],
    ['**参考回答:**QUIC 提供可靠流。','参考回答:'],
    ['**不能看到 pid 就说进程 ID，更不能把 gid 直接说成 Linux 组 ID。**需要回忆字段定义。','不能看到 pid 就说进程 ID，更不能把 gid 直接说成 Linux 组 ID。'],
  ];
  for(const [markdown,label]of examples) {
    const root=render(markdown);
    assert.equal(root.querySelector('strong')?.textContent,label);
    assert.ok(!root.textContent.includes('**'));
  }
  const nested=render('- **面试回答：**正文\n  - **追问：**下一层\n\n### **参考回答：**标题正文');
  assert.equal(nested.querySelectorAll('li strong').length,2);
  assert.equal(nested.querySelector('h3 strong').textContent,'参考回答：');
});

test('compatibility does not consume escaped stars, multiplication, globs, code or other delimiter runs',()=>{
  const standard=new Marked({gfm:true});
  for(const source of [String.raw`\*\*参考回答：\*\*正文`,String.raw`\**参考回答：**正文`,'***中文：***正文','****中文：****正文','**中文粗体**紧接中文','a * b','a ** b ** c','**/*.md','**未闭合的双星号','`**面试回答：**它`']) {
    const baseline=document.createElement('div');baseline.innerHTML=standard.parse(source);
    const result=render(source);
    assert.equal(result.innerHTML.trim(),baseline.innerHTML.trim(),source);
  }
  const code='let pointer: *mut u8;\nlet product = a * b;\nlet glob = "**/*.md";\nlet text = "**面试回答：**它";';
  assert.equal(render('```rust\n'+code+'\n```').querySelector('pre code').textContent,code+'\n');
  const raw=render('**代码事实：**<img src=x onerror=alert(1)>\n\n**危险标签：**javascript:alert(1)');
  assert.equal(raw.querySelector('img,script,[onerror]'),null);
});

test('all 371 real answers and seven guides lose only unintended prose delimiters; code stars stay exact',()=>{
  const snapshot=JSON.parse(readFileSync(new URL('../engine/snapshot.json',import.meta.url)));
  const catalog=parseMarkdownSources(snapshot.files,{revision:snapshot.revision});
  const standard=new Marked({gfm:true});
  function visiblePairs(root) {
    const walker=document.createTreeWalker(root,dom.window.NodeFilter.SHOW_TEXT);let node,count=0;
    while(node=walker.nextNode())if(!node.parentElement?.closest('pre,code'))count+=(node.textContent.match(/\*\*[^*\n]{1,700}\*\*/g)||[]).length;
    return count;
  }
  let baselineAffected=0,baselinePairs=0;
  for(const item of [...catalog.questions,...catalog.documents]) {
    const source=item.answerMarkdown??item.markdown;
    const before=document.createElement('div');before.innerHTML=standard.parse(source);
    const after=render(source,{documentPath:item.path});
    const pairs=visiblePairs(before);
    if(item.answerMarkdown&&pairs){baselineAffected++;baselinePairs+=pairs;}
    assert.equal(visiblePairs(after),0,item.id);
    assert.deepEqual([...after.querySelectorAll('code')].map(el=>el.textContent),[...before.querySelectorAll('code')].map(el=>el.textContent),item.id+' preserves all code');
  }
  assert.equal(catalog.questions.length,371);
  assert.equal(baselineAffected,37);assert.equal(baselinePairs,98);
});

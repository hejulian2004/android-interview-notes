import { Marked, Renderer } from './vendor/marked.esm.js';
import DOMPurify from './vendor/purify.es.mjs';
import { highlightCode } from './vendor/highlight.mjs';

const DEFAULT_SOURCE = 'https://github.com/hejulian2004/android-interview-notes/blob/main/README.md';
const PUBLIC_REPOSITORY = 'hejulian2004/android-interview-notes';
const escapeHtml = text => String(text).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const decode = value => {try{return decodeURIComponent(value);}catch{return value;}};

/** GitHub-style Unicode slugs; duplicate suffixes are applied per rendered document. */
export function githubHeadingSlug(text) {
  return String(text).toLowerCase().replace(/[^\p{L}\p{N}\p{M} _-]/gu,'').replace(/ /g,'-');
}
function githubSource(url) {
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== 'https:' || parsed.hostname !== 'github.com') return null;
    const match = parsed.pathname.match(/^\/([^/]+)\/([^/]+)\/blob\/([^/]+)\/(.+)$/);
    if (!match || `${match[1]}/${match[2]}`.toLowerCase() !== PUBLIC_REPOSITORY.toLowerCase()) return null;
    return {revision:decode(match[3]),path:match[4].split('/').map(decode).join('/')};
  } catch {return null;}
}
function safeRepoPath(path) {
  if (typeof path !== 'string' || !path || /[\u0000-\u001f\\]/.test(path)) return null;
  const segments = [];
  for (const part of path.split('/')) {
    if (!part || part === '.') continue;
    if (part === '..') {if(!segments.length)return null;segments.pop();}
    else segments.push(part);
  }
  return segments.join('/');
}
function sourceHref(source, path, anchor = '', query = '') {
  return `https://github.com/${PUBLIC_REPOSITORY}/blob/${encodeURIComponent(source.revision)}/${path.split('/').map(encodeURIComponent).join('/')}${query}${anchor?'#'+encodeURIComponent(anchor):''}`;
}
/** Pure link resolver. Only this public repo's Markdown is offered to SPA navigation. */
export function resolveMarkdownLink(href, sourceUrl = DEFAULT_SOURCE, documentPath) {
  if (typeof href !== 'string' || !href.trim() || /[\u0000-\u001f]/.test(href)) return {href:'',internal:false};
  const value = href.trim();
  const source = githubSource(sourceUrl);
  const currentPath = safeRepoPath(documentPath || source?.path);
  if (value.startsWith('#')) {
    const anchor = decode(value.slice(1));
    return {href:value,internal:true,documentPath:currentPath || undefined,anchor};
  }
  // Relative repository paths are resolved as POSIX segments, independently of URL blob routing.
  if (source && currentPath && !/^[A-Za-z][A-Za-z\d+.-]*:/.test(value) && !value.startsWith('/') && !value.includes('\\')) {
    const hash = value.indexOf('#');
    const beforeHash = hash < 0 ? value : value.slice(0,hash);
    const anchor = hash < 0 ? '' : decode(value.slice(hash+1));
    const question = beforeHash.indexOf('?');
    const relativePath = question < 0 ? beforeHash : beforeHash.slice(0,question);
    const query = question < 0 ? '' : beforeHash.slice(question);
    const base = currentPath.split('/').slice(0,-1).join('/');
    const path = safeRepoPath(`${base}/${decode(relativePath)}`);
    if (path) return {href:sourceHref(source,path,anchor,query),internal:/\.md$/i.test(path),documentPath:/\.md$/i.test(path)?path:undefined,anchor};
  }
  try {
    const resolved = new URL(value,sourceUrl);
    if (!['https:','http:'].includes(resolved.protocol)) return {href:'',internal:false};
    const target = githubSource(resolved.href);
    const path = target && safeRepoPath(target.path);
    return {href:resolved.href,internal:Boolean(path && /\.md$/i.test(path)),documentPath:path && /\.md$/i.test(path)?path:undefined,anchor:decode(resolved.hash.slice(1))};
  } catch {return {href:'',internal:false};}
}

/** Render GFM safely. Raw HTML remains text; exact empty anchor markers become inert spans. */
export function renderMarkdown(markdown, sourceUrl = DEFAULT_SOURCE, {idPrefix = 'md-',documentPath} = {}) {
  const prefix = String(idPrefix || 'md-').replace(/[^A-Za-z\d_-]/g,'-').slice(0,150);
  const headingCounts = new Map();
  const domIds = new Set();
  const uniqueId = base => {let id=prefix+base,index=0;while(domIds.has(id))id=prefix+base+'-'+(++index);domIds.add(id);return id;};
  const renderer = new Renderer();
  renderer.html = ({text}) => escapeHtml(text);
  renderer.image = ({text}) => `<span class="markdown-image">[图片：${escapeHtml(text || '查看原文')}]</span>`;
  renderer.heading = function({tokens,depth}) {
    const html = this.parser.parseInline(tokens);
    const text = document.createElement('template');text.innerHTML=html;
    const base = githubHeadingSlug(text.content.textContent || '');
    let count = headingCounts.get(base) || 0;
    let slug = base;
    while (headingCounts.has(slug)) slug = base + '-' + (++count);
    headingCounts.set(base,count);headingCounts.set(slug,0);
    return `<h${depth} id="${escapeHtml(uniqueId(slug || 'heading'))}" data-markdown-anchor="${escapeHtml(slug)}" tabindex="-1">${html}</h${depth}>\n`;
  };
  renderer.code = ({text,lang}) => {
    // Marked removes the fence's one terminating newline; restore it without trimming intentional blank lines.
    const code = String(text) + '\n';
    const result = highlightCode(code,lang);
    const className = result.html === null ? 'hljs nohighlight' : `hljs language-${result.language}`;
    return `<figure class="markdown-code-block" data-code-language="${escapeHtml(result.language)}"><figcaption class="code-language-label">${escapeHtml(result.label)}</figcaption><pre tabindex="0" aria-label="${escapeHtml(result.label)} 代码，可横向滚动"><code class="${escapeHtml(className)}">${result.html ?? escapeHtml(code)}</code></pre></figure>\n`;
  };
  const anchorPattern = /^ {0,3}<a[ \t]+(?:id|name)[ \t]*=[ \t]*(["'])([\p{L}\p{N}_.:-]{1,200})\1[ \t]*>[ \t]*<\/a>[ \t]*(?:\n|$)/u;
  const parser = new Marked({gfm:true,breaks:false,renderer,extensions:[{
    name:'safeSourceAnchor',level:'block',
    start(src) {const match=/^ {0,3}<a[ \t]+(?:id|name)[ \t]*=/m.exec(src);return match?.index;},
    tokenizer(src) {const match=anchorPattern.exec(src);if(match)return {type:'safeSourceAnchor',raw:match[0],anchor:match[2]};},
    renderer(token) {return `<span id="${escapeHtml(uniqueId('anchor-'+token.anchor))}" class="markdown-anchor" data-markdown-anchor="${escapeHtml(token.anchor)}" aria-hidden="true"></span>\n`;}
  }]});
  const clean = DOMPurify.sanitize(parser.parse(String(markdown || '')), {
    USE_PROFILES:{html:true},
    FORBID_TAGS:['style','script','iframe','object','embed','form','input','button','textarea','select'],
    FORBID_ATTR:['style','srcdoc','onerror','onclick'],
  });
  const template = document.createElement('template');template.innerHTML=clean;
  template.content.querySelectorAll('a').forEach(link => {
    const result = resolveMarkdownLink(link.getAttribute('href'),sourceUrl,documentPath);
    if (!result.href) {link.removeAttribute('href');return;}
    link.href=result.href;
    if (result.internal) {
      link.dataset.markdownAnchor=result.anchor || '';
      if(result.documentPath)link.dataset.documentPath=result.documentPath;
      if(result.href.startsWith('#')) {
        const target=[...template.content.querySelectorAll('h1[data-markdown-anchor],h2[data-markdown-anchor],h3[data-markdown-anchor],h4[data-markdown-anchor],h5[data-markdown-anchor],h6[data-markdown-anchor],span[data-markdown-anchor]')]
          .find(el=>el.dataset.markdownAnchor===result.anchor);
        if(target)link.setAttribute('href','#'+target.id);
        else {
          const fallback=new URL(sourceUrl);fallback.hash=result.anchor||'';
          link.href=fallback.href;link.target='_blank';link.rel='noopener noreferrer';
        }
      }
    }
    if (!result.href.startsWith('#')) {link.target='_blank';link.rel='noopener noreferrer';}
  });
  template.content.querySelectorAll('table').forEach(table => {
    const wrapper=document.createElement('div');wrapper.className='table-scroll';wrapper.tabIndex=0;
    wrapper.setAttribute('role','region');wrapper.setAttribute('aria-label','表格，可横向滚动');
    table.replaceWith(wrapper);wrapper.append(table);
  });
  return template.innerHTML;
}

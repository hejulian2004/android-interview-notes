import { marked } from './vendor/marked.esm.js';
import DOMPurify from './vendor/purify.es.mjs';

const escapeHtml = text => String(text).replace(/[&<>\"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[char]));
const renderer = new marked.Renderer();
// Treat repository HTML as text, never executable markup.
renderer.html = ({ text }) => escapeHtml(text);
marked.use({ renderer, gfm: true, breaks: false });

export function renderMarkdown(markdown, sourceUrl = 'https://github.com/hejulian2004/android-interview-notes/blob/main/README.md') {
  const clean = DOMPurify.sanitize(marked.parse(String(markdown || '')), {
    USE_PROFILES: { html: true },
    FORBID_TAGS: ['style', 'script', 'iframe', 'object', 'embed', 'form', 'input', 'button', 'textarea', 'select'],
    FORBID_ATTR: ['style', 'srcdoc', 'onerror', 'onclick'],
  });
  const template = document.createElement('template');
  template.innerHTML = clean;
  template.content.querySelectorAll('a').forEach(link => {
    const href = link.getAttribute('href');
    if (!href) return;
    try {
      const resolved = new URL(href, sourceUrl);
      if (!['https:', 'http:'].includes(resolved.protocol)) {
        link.removeAttribute('href');
        return;
      }
      link.href = resolved.href;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
    } catch { link.removeAttribute('href'); }
  });
  // Documentation images are optional links; the site never loads remote image trackers.
  template.content.querySelectorAll('img').forEach(img => {
    const label = document.createElement('span');
    label.textContent = `[图片：${img.alt || '查看原文'}]`;
    img.replaceWith(label);
  });
  template.content.querySelectorAll('table').forEach(table => {
    const wrapper = document.createElement('div');
    wrapper.className = 'table-scroll';
    wrapper.tabIndex = 0;
    wrapper.setAttribute('role', 'region');
    wrapper.setAttribute('aria-label', '表格，可横向滚动');
    table.replaceWith(wrapper);
    wrapper.append(table);
  });
  return template.innerHTML;
}

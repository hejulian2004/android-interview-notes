// Official Highlight.js 11.12.0 browser ESM, self-hosted from @highlightjs/cdn-assets.
import hljs from './highlight-core.min.js';
import kotlin from './highlight-kotlin.min.js';
import java from './highlight-java.min.js';
import xml from './highlight-xml.min.js';
import dart from './highlight-dart.min.js';
import rust from './highlight-rust.min.js';
import bash from './highlight-bash.min.js';
import json from './highlight-json.min.js';
import javascript from './highlight-javascript.min.js';
import typescript from './highlight-typescript.min.js';
import sql from './highlight-sql.min.js';
import yaml from './highlight-yaml.min.js';
import c from './highlight-c.min.js';
import cpp from './highlight-cpp.min.js';
for (const [name, language] of Object.entries({kotlin,java,xml,dart,rust,bash,json,javascript,typescript,sql,yaml,c,cpp})) {
  hljs.registerLanguage(name, language);
}
const aliases = Object.freeze({kt:'kotlin',kts:'kotlin',html:'xml',xhtml:'xml',svg:'xml',sh:'bash',shell:'bash',zsh:'bash',js:'javascript',jsx:'javascript',ts:'typescript',tsx:'typescript',yml:'yaml','c++':'cpp',h:'c',hpp:'cpp'});
const labels = Object.freeze({kotlin:'Kotlin',java:'Java',xml:'XML / HTML',dart:'Dart',rust:'Rust',bash:'Bash',json:'JSON',javascript:'JavaScript',typescript:'TypeScript',sql:'SQL',yaml:'YAML',c:'C',cpp:'C++'});
export function highlightCode(text, info = '') {
  const requested = String(info || '').trim().split(/\s+/)[0].slice(0,40).toLowerCase();
  const language = aliases[requested] || requested;
  const known = Boolean(hljs.getLanguage(language));
  // Explicit fences only: unknown/unlabelled text is never guessed or executed.
  if (!known || text.length > 100000) return {language:requested || 'text',label:requested && !['text','plaintext','plain','none'].includes(requested) ? `${labels[language] || requested} · 纯文本` : '纯文本',html:null};
  try {
    return {language,label:labels[language] || language,html:hljs.highlight(String(text),{language,ignoreIllegals:true}).value};
  } catch {
    return {language,label:`${labels[language] || language} · 纯文本`,html:null};
  }
}

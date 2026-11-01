# Self-hosted Highlight.js browser modules

Pinned version: **11.12.0**, BSD-3-Clause (see `highlight-LICENSE`).

Official package: `@highlightjs/cdn-assets@11.12.0`.
Official source and browser-module instructions:
<https://github.com/highlightjs/highlight.js#browser-es6-modules>

`highlight-core.min.js` is an unchanged copy of package `es/core.min.js`.
Each `highlight-LANGUAGE.min.js` is an unchanged copy of package
`es/languages/LANGUAGE.min.js`. Only 13 languages relevant to Android, Flutter,
Rust and configuration examples are included. `highlight.mjs` is the application's
registration and explicit-language wrapper. No library, grammar, or stylesheet is
fetched from a CDN at runtime. Unknown/unlabelled fences remain plain text;
auto-detection is not used. Marked parsing and DOMPurify sanitizing remain in
`../markdown.mjs`. The theme is local application CSS in `../markdown.css`.

To update, change the exact package pin and lockfile, install dependencies,
recopy these unchanged modules plus license, update this provenance and wrapper
version, and run the Markdown/security/browser checks before deployment.

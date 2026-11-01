# Public GitHub content engine

The only content origin is the public repository `https://github.com/hejulian2004/android-interview-notes`.
No GitHub credential, private repository read, background cron, server runtime, or data upload is used.
Existing links to private project source remain links; this application does not fetch their targets.

## Browser integration

```js
import { loadCatalog, TOPICS } from './engine/index.mjs';
const catalog = await loadCatalog({
  force: false,
  onStatus: status => console.log(status.phase, status.message),
});
```

`loadCatalog` returns `{questions, documents, topics, revision, fetchedAt, checkedAt, generatedAt, origin, warning}`.
`origin` is `snapshot`, `cache`, or `github`. `generatedAt` dates the bundled offline snapshot;
`fetchedAt` is the last successful GitHub verification, and is null for a snapshot never verified online.
A failed update keeps the prior successful `fetchedAt` and revision, and sets `warning`.
Show both origin and warning; do not label a snapshot or failed check as live content.

Question fields:

- `id`: source document path plus explicit question code, for example `docs/android-interview-handbook.md#n01`. It is independent of array order and displayed title. A source document move/rename changes this ID.
- `number`, `title`, `section`, `priority` (`P0/P1/P2` or empty).
- `topicId`, `topicIds`; topic IDs are `android`, `compose`, `xml`, `flutter`, `rust`, `quic`, `agent`, `internship`.
- `answerMarkdown`: full answer, followups, evidence, mistakes and references up to the next peer/parent heading. For independent Q/E files it contains the entire document after the title, preserving all provenance.
- `contextMarkdown`: source introduction and evidence labels; public Q/E entries include their source evidence before the reference answer. Display it alongside the answer.
- `path`, `docId`, `sourceUrl`, `searchText`, `kind` (`guide`, `public`, `supplement`).

Reading documents contain `{id,path,title,markdown,contextMarkdown,topicId,topicIds,sourceUrl,kind}`.
The seven guide documents are readable in full, including fact tables, version boundaries and exercises.
SDK, QUIC and AI takeover guides remain reading documents rather than synthetic question banks.
`parseMarkdownSources(files, {revision,fetchedAt,origin})` is also exported as a pure parser.
Files are `{path,sha,content}` records. It never interprets or emits HTML.

Render Markdown with the application's sanitizing renderer. This module returns untrusted content strings;
raw source HTML must not be enabled. Links should permit only safe HTTP(S), local hash links as intended,
and known relative source-document links resolved against their verified GitHub `sourceUrl`.

## Refresh behavior

On each page load, the engine checks `main` at most once per 30 minutes (`CHECK_INTERVAL`).
The explicit refresh button passes `force:true`. No timer runs while the site is idle.

1. Load the successful local cache, otherwise `snapshot.json` relative to this module.
2. Fetch `https://api.github.com/repos/hejulian2004/android-interview-notes/commits/main`.
3. If the commit changed, fetch its recursive tree and discover compatible Markdown under `docs/`, plus independent Q/E Markdown under `questions/` and `supplements/`.
4. Download only new/changed blobs from `raw.githubusercontent.com` using the immutable commit. Up to six downloads run concurrently. Unchanged `sha`s reuse cached content.
5. Parse and validate the complete update before replacing the local cache. A partial download, empty/incompatible question bank, truncated tree, API failure, timeout, invalid SHA or size limit retains the prior complete version.

A main check with unchanged content makes one GitHub API request. A changed main requires two API requests plus changed raw documents. No token is needed for this public repository; public unauthenticated GitHub rate limits still apply. Failed checks also respect the 30-minute interval, but manual refresh bypasses it.
Requests use `credentials:'omit'` and `referrerPolicy:'no-referrer'`.
The deployment CSP must allow `connect-src 'self' https://api.github.com https://raw.githubusercontent.com`.

The cache key is `android-study:catalog:v1` in localStorage. It is separate from the UI's learning-progress key.
Denied storage and quota errors leave the current page usable; the warning explains that caching failed.
First offline use relies on the packaged snapshot; it does not imply the entire site itself is installed for offline startup.

The UI must keep learning progress by `question.id`. Removed questions disappear from the active catalog;
retain orphan progress only in local export/backup, and report it separately from active progress.
New questions do not inherit another question's state. Device/browser storage is local; it does not sync.

## Snapshot and tests

The shipped snapshot is commit `2a49c4de3f90706751014f12c673cd6992cb3efd` with 139 public Markdown files:

| Bank | Questions |
| --- | ---: |
| Personal project and internship handbook | 129 |
| Flutter guide | 52 |
| Word Crush XML guide | 38 |
| FeedLine guide | 20 |
| Public-source questions | 116 |
| Explicit supplemental exercises | 16 |
| Total | 371 |

TOC entries are never parsed as questions. Fenced code headings are ignored. Stable question codes are parsed only from real level-three headings in guide files; independent Q/E files use their level-one code. Explicit HTML anchors are used for source links without rendering the HTML; otherwise the GitHub heading slug is derived.

Run from the project root:

```sh
node --test tests/engine.test.mjs
python3 engine/build-snapshot.py content
```

The snapshot builder requires a clean checkout with the authorized public origin and refuses contact-like email/phone data for review. It does not fetch or push. Website content updates normally need only a GitHub commit: snapshot rebuilding is for refreshed offline fallback during a future website release.

Tests cover real 371-question counts, TOC/fence exclusion, complete followups and evidence limits, explicit source anchors, stable IDs after reorder, unchanged-main request counts, dynamic added/deleted documents, changed-blob-only fetching, rate limits, partial failure, explicit retry, first offline startup, and unavailable storage. Test mocks verify behavior; production network and browser connectivity still need separate verification.

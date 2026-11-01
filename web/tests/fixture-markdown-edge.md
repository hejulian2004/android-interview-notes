# Markdown QA fixture

> Fixture data only. Do not add this document to the public question bank.

## GFM and nested structure

**Bold**, *emphasis*, ~~strikethrough~~, and `inline <code>`.

1. First ordered item
   - Nested unordered item
   - A second nested item
2. Second ordered item

> A quote containing **formatted text**.
>
> A second paragraph.

- [x] Completed task
- [ ] Pending task

| Left | Center | Right |
| :--- | :---: | ---: |
| `a\|b` | **中文** | 123 |

## Code remains text

```javascript
const html = '<img src=x onerror="globalThis.__markdownXss = 1">';
function answer(value) { return value ?? 'fallback'; }
```

```rust
fn main() { println!("<script>not executable</script>"); }
```

```not-a-real-language
<script>globalThis.__markdownXss = 2</script>
### Q99 This is code, not a question or heading.
<a id="fake-anchor-in-code"></a>
```

## Original explicit anchors and duplicate headings

[Jump to Q01](#q01) · [Jump to section](#network)

<a id="network"></a>
## Network section

<a id="q01"></a>
### Q01 `rememberSaveable` 与状态恢复

An answer with a **fact boundary**, a [relative reading link](sdk-source-deep-dive.md#21-abi-是调用约定不是网络协议), and a [source-only link](../sources/S004.md).

### Duplicate heading

First instance.

### Duplicate heading

Second instance must have a different DOM id.

## Unsafe markup and destinations

<img src="https://example.invalid/tracker.png" onerror="globalThis.__markdownXss = 3">

<script>globalThis.__markdownXss = 4</script>

<a id="unsafe" onclick="globalThis.__markdownXss = 5">not an empty trusted anchor</a>

[javascript URL](javascript:alert%281%29)

[entity-obfuscated URL](jav&#x61;script:alert%281%29)

[data URL](data:text/html;base64,PHNjcmlwdD4=)

[external safe link](https://developer.android.com/guide/components/activities/activity-lifecycle)

![Remote Markdown image](https://example.invalid/markdown-tracker.png)

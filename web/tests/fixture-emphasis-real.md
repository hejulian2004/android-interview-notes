# Chinese strong-delimiter regression fixtures

These examples are QA data, excluded from the study catalog.

## Real broken examples

Source: `docs/android-interview-handbook.md#n01`.

**面试回答：**它是面向移动端的远程服务器管理与协作工具，不只是一个 SSH 登录页面。

**追问：**你的贡献和使用开源库有什么区别？

**代码事实：**以下问题围绕当前简历的 SDK 与可靠传输描述展开。

Source: `docs/android-interview-handbook.md#n34`.

**S｜背景：**网络流需要在背压条件下等待可发送状态。

**A｜行动（以代码事实为底稿）：**围绕条件检查和通知订阅的时序分析。

**备选主题：可靠传输的结果不确定性。**用“接收端已提交但 ACK 丢失”这个失败场景。

Source: `docs/android-interview-handbook.md#i16`.

**不能看到 pid 就说进程 ID，更不能把 gid 直接说成 Linux 组 ID。**需要回忆其后台字段定义。

## Existing valid formatting remains valid

N05 control: **面试回答：**`Send` 表示值的所有权可以安全跨线程转移。

**Normal bold**, *normal emphasis*, ***nested strong and emphasis***.

**中文粗体**紧接中文，and **punctuation-ending label:**followed by English.

**Outer with `inline code`：**后文。

## Asterisks that must remain literal

Escaped stars: \*\*刻意显示双星号\*\* and \*单星号\*.

Inline code: `*mut u8`, `a * b`, `**/*.md`, `**面试回答：**它`.

Literal wildcard path outside code: **/*.md

Spaced operators outside code: a ** b ** c

Unclosed formatting outside code: **未闭合的双星号

```rust
let pointer: *mut u8 = std::ptr::null_mut();
let product = a * b;
let glob = "**/*.md";
let markdown = "**面试回答：**它";
```

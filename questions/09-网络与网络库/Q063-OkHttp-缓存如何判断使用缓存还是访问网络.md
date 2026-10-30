---
id: Q063
title: "OkHttp 缓存如何判断使用缓存还是访问网络"
category: "09-网络与网络库"
kind: observed
priority: P1
updated_at: "2026-10-30"
---

# Q063 · OkHttp 缓存如何判断使用缓存还是访问网络

类别：09-网络与网络库　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S008 · 美团

提问线索：网络缓存。

面试日期：未明确；帖子显示：2025-02-17（已编辑）。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/592247f523b64d45bb0dd5f28bdfaf56) · [来源档案与限制](../../sources/S008.md)

### S028 · Soul

提问线索：公开一面：网络库缓存。

面试日期：2024（具体月日不明）；帖子显示：专栏 2024-07-07；文章头 2024-07-17。
日期依据：**面试年份明确**；访问状态：仅公开预览已读取。

[原始面经](https://blog.csdn.net/R3lish/article/details/140246444) · [来源档案与限制](../../sources/S028.md)

## 参考回答提纲

结合 Cache-Control、新鲜度、ETag 或 Last-Modified 解释直接复用和条件验证。缓存键、Vary 和请求语义影响命中；离线行为要由产品要求与协议策略共同定义。

## 易错点

Retrofit 不是独立的 HTTP 磁盘缓存实现；通常要看底层客户端的缓存配置。

## 延伸追问（整理者设计，不是原帖原题）

304 响应为什么能减少传输，却不意味着完全没有网络请求？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [OkHttp 缓存](https://lysine.dev/okhttp/features/caching/)（网页入口已核查）
- [RFC 9110：HTTP 语义](https://www.rfc-editor.org/rfc/rfc9110.html)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

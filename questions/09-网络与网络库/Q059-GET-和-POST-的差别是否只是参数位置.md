---
id: Q059
title: "GET 和 POST 的差别是否只是参数位置"
category: "09-网络与网络库"
kind: observed
priority: P0
updated_at: "2026-10-30"
---

# Q059 · GET 和 POST 的差别是否只是参数位置

类别：09-网络与网络库　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S011 · 百度

提问线索：二面：GET、POST 与参数限制。

面试日期：未明确；帖子显示：2025-04-08。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/6c2b6b3c15bc40e2b25fef6662c77988) · [来源档案与限制](../../sources/S011.md)

### S012 · 滴滴

提问线索：一面：HTTP 方法。

面试日期：未明确；帖子显示：2025-05-24。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/3b35b2df975b4ff7a8ab9039a5f38277?sourceSSR=subject) · [来源档案与限制](../../sources/S012.md)

## 参考回答提纲

先回答方法语义、安全性与幂等性约定，再讨论缓存、重试和载荷。URL 长度限制常来自客户端、代理或服务端实现；不能给整个 HTTP 协议编造统一的固定字节上限。

## 易错点

POST 并不天然比 GET 安全，传输保密仍依赖 HTTPS 等机制。

## 延伸追问（整理者设计，不是原帖原题）

网关为什么通常不应自动重试任意 POST 请求？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [RFC 9110：HTTP 语义](https://www.rfc-editor.org/rfc/rfc9110.html)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

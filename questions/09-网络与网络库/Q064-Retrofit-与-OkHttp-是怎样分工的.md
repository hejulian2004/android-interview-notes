---
id: Q064
title: "Retrofit 与 OkHttp 是怎样分工的"
category: "09-网络与网络库"
kind: observed
priority: P1
updated_at: "2026-10-30"
---

# Q064 · Retrofit 与 OkHttp 是怎样分工的

类别：09-网络与网络库　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S009 · 快手

提问线索：二面：Retrofit 与 OkHttp。

面试日期：2025-03-06 / 2025-03-10；帖子显示：2025-03-13（已编辑）。
日期依据：**面试年份由上下文推定**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/9b9f932f60a345afb0f20162a0374e50) · [来源档案与限制](../../sources/S009.md)

### S012 · 滴滴

提问线索：Retrofit 注解。

面试日期：未明确；帖子显示：2025-05-24。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/3b35b2df975b4ff7a8ab9039a5f38277?sourceSSR=subject) · [来源档案与限制](../../sources/S012.md)

### S028 · Soul

提问线索：公开一面：Retrofit 设计。

面试日期：2024（具体月日不明）；帖子显示：专栏 2024-07-07；文章头 2024-07-17。
日期依据：**面试年份明确**；访问状态：仅公开预览已读取。

[原始面经](https://blog.csdn.net/R3lish/article/details/140246444) · [来源档案与限制](../../sources/S028.md)

## 参考回答提纲

Retrofit 将声明式接口、注解和转换适配映射为 HTTP 调用；OkHttp 负责更底层的请求执行与连接、拦截器等。说明请求参数解析、序列化、调用适配、错误传播和取消的边界。

## 易错点

不要把 JSON 转换失败、HTTP 非成功状态与网络异常统统当成同一种失败。

## 延伸追问（整理者设计，不是原帖原题）

请求协程被取消时，如何保证底层调用也停止占用资源？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [Retrofit 官方文档](https://lysine.dev/retrofit/)（网页入口已核查）
- [OkHttp 拦截器](https://lysine.dev/okhttp/features/interceptors/)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

---
id: Q113
title: "Builder 模式适合解决哪些构造问题"
category: "16-工程设计与项目追问"
kind: observed
priority: P1
updated_at: "2026-10-30"
---

# Q113 · Builder 模式适合解决哪些构造问题

类别：16-工程设计与项目追问　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S015 · 字节跳动

提问线索：设计模式：Builder。

面试日期：未明确；帖子显示：2025-08-21。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/0bc82383dd644c88a358171c19b0c867) · [来源档案与限制](../../sources/S015.md)

## 参考回答提纲

对于可选参数多、构造约束复杂或需要分阶段组装的对象，Builder 可集中校验并提升调用可读性。比较命名参数、工厂方法和不可变对象构造，说明引入额外类型是否值得。

## 易错点

不要为了展示模式而给只有两个简单参数的对象强行增加多层 Builder。

## 延伸追问（整理者设计，不是原帖原题）

如何避免 build 后继续修改 builder 影响已构建对象？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [HttpRequest.Builder：Builder API 示例](https://docs.oracle.com/en/java/javase/17/docs/api/java.net.http/java/net/http/HttpRequest.Builder.html)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

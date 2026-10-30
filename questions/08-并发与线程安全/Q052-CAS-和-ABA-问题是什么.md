---
id: Q052
title: "CAS 和 ABA 问题是什么"
category: "08-并发与线程安全"
kind: observed
priority: P1
updated_at: "2026-10-30"
---

# Q052 · CAS 和 ABA 问题是什么

类别：08-并发与线程安全　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S020 · 小米

提问线索：CAS 与 ABA。

面试日期：2026-10-22；帖子显示：10-23（页面省略年份，已编辑）。
日期依据：**面试年份由上下文推定**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/27424c8609eb43c9aee0b0cbb57584eb) · [来源档案与限制](../../sources/S020.md)

## 参考回答提纲

CAS 在当前位置仍等于期望值时原子更新。它能构造无锁式重试，但值经历 A→B→A 时，单凭最终值可能遗漏状态变化。可用版本戳、约束生命周期或其他同步方式处理。

## 易错点

CAS 不保证无竞争或无重试，也不自动使多字段不变量原子化。

## 延伸追问（整理者设计，不是原帖原题）

AtomicInteger 计数和复用链表节点，为什么对 ABA 的敏感性不同？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [Java 原子变量 API](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/atomic/package-summary.html)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

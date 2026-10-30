---
id: E014
title: "结构化并发和 Supervisor 有什么不同"
category: "06-Kotlin与协程"
kind: supplement
priority: P0
updated_at: "2026-10-30"
---

# E014 · 结构化并发和 Supervisor 有什么不同

类别：06-Kotlin与协程　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 题目性质

**补充练习，不计入来源题数量，也不归属于任何公司的确定面试记录。** 本题用于补齐复习主题，不能写成“某公司近三年问过”。

## 参考回答提纲

普通父子 Job 关系会传播取消与失败；监督关系允许某些子任务失败不取消兄弟任务。需要结合 coroutineScope、supervisorScope 和异常处理位置讲具体传播路径。

## 易错点

async 的异常不只是“永远等 await 才发生作用”；父子关系会影响取消传播。

## 延伸追问（整理者设计，不是原帖原题）

两个并行请求中一个失败时，是整体失败还是保留另一个结果？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [协程异常处理](https://kotlinlang.org/docs/exception-handling.html)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

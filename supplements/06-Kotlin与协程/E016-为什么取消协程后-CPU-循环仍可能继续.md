---
id: E016
title: "为什么取消协程后 CPU 循环仍可能继续"
category: "06-Kotlin与协程"
kind: supplement
priority: P1
updated_at: "2026-10-30"
---

# E016 · 为什么取消协程后 CPU 循环仍可能继续

类别：06-Kotlin与协程　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 题目性质

**补充练习，不计入来源题数量，也不归属于任何公司的确定面试记录。** 本题用于补齐复习主题，不能写成“某公司近三年问过”。

## 参考回答提纲

取消是协作式的，纯计算循环若没有检查取消或调用可取消挂起点，可能继续占用线程。按合理粒度检查活动状态，并通过 finally 清理资源。

## 易错点

捕获所有异常后吞掉 CancellationException 会破坏取消传播。

## 延伸追问（整理者设计，不是原帖原题）

计算批次过大和检查过于频繁各有什么代价？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [Kotlin 协程取消（入口，本次页面直读为空）](https://kotlinlang.org/docs/cancellation-and-timeouts.html)（本次未成功核查页面，仅保留学习入口）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

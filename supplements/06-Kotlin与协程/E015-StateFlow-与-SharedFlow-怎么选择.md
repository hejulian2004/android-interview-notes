---
id: E015
title: "StateFlow 与 SharedFlow 怎么选择"
category: "06-Kotlin与协程"
kind: supplement
priority: P0
updated_at: "2026-10-30"
---

# E015 · StateFlow 与 SharedFlow 怎么选择

类别：06-Kotlin与协程　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 题目性质

**补充练习，不计入来源题数量，也不归属于任何公司的确定面试记录。** 本题用于补齐复习主题，不能写成“某公司近三年问过”。

## 参考回答提纲

StateFlow 表达始终存在的当前状态，并有相等性合并语义；SharedFlow 可配置重放与缓冲，更适合某些广播需求。选择还要定义无订阅者时的数据命运与重建后的消费语义。

## 易错点

SharedFlow 不是天然保证只消费一次的事件队列。

## 延伸追问（整理者设计，不是原帖原题）

支付成功导航在旋转后是否应重复发生，应该怎样建模？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [StateFlow API](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/)（网页入口已核查）
- [SharedFlow API](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-shared-flow/)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

---
id: E009
title: "Compose 如何按生命周期收集 Flow"
category: "05-JetpackCompose"
kind: supplement
priority: P0
updated_at: "2026-10-30"
---

# E009 · Compose 如何按生命周期收集 Flow

类别：05-JetpackCompose　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 题目性质

**补充练习，不计入来源题数量，也不归属于任何公司的确定面试记录。** 本题用于补齐复习主题，不能写成“某公司近三年问过”。

## 参考回答提纲

Android 页面可用 collectAsStateWithLifecycle 将 Flow 转为受生命周期约束的状态。需要同时考虑上游是否共享、订阅启停和初始值，避免页面不可见时持续做无关工作。

## 易错点

收集者停止不一定意味着独立运行的上游任务也自动结束。

## 延伸追问（整理者设计，不是原帖原题）

多个页面收集同一个冷 Flow 会不会重复请求？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [Compose 状态](https://developer.android.com/develop/ui/compose/state)（网页入口已核查）
- [StateFlow API](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

---
id: E004
title: "共享 RecycledViewPool 与增大缓存有哪些条件"
category: "04-RecyclerView"
kind: supplement
priority: P1
updated_at: "2026-10-30"
---

# E004 · 共享 RecycledViewPool 与增大缓存有哪些条件

类别：04-RecyclerView　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 题目性质

**补充练习，不计入来源题数量，也不归属于任何公司的确定面试记录。** 本题用于补齐复习主题，不能写成“某公司近三年问过”。

## 参考回答提纲

共享池只适用于 viewType 与 holder 结构、绑定契约兼容的列表。更大缓存会保留更多对象，收益要与内存、预取和滚动方式一起衡量。

## 易错点

不同 adapter 恰好用了同一个整数类型，不代表 holder 可以安全互换。

## 延伸追问（整理者设计，不是原帖原题）

跨页面共享池时如何避免意外保留旧 Context？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [RecyclerView API](https://developer.android.com/reference/androidx/recyclerview/widget/RecyclerView)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

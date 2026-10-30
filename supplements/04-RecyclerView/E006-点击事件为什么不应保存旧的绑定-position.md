---
id: E006
title: "点击事件为什么不应保存旧的绑定 position"
category: "04-RecyclerView"
kind: supplement
priority: P1
updated_at: "2026-10-30"
---

# E006 · 点击事件为什么不应保存旧的绑定 position

类别：04-RecyclerView　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 题目性质

**补充练习，不计入来源题数量，也不归属于任何公司的确定面试记录。** 本题用于补齐复习主题，不能写成“某公司近三年问过”。

## 参考回答提纲

列表更新后，绑定时的位置可能已经变化。点击时使用合适的当前 adapter 位置并处理 NO_POSITION，或让回调传递稳定业务 ID。ConcatAdapter 场景还需分清局部与绝对位置。

## 易错点

旧 position 可能指向另一条数据；Stable ID 也不会自动修复所有点击逻辑。

## 延伸追问（整理者设计，不是原帖原题）

动画或删除过程中点击项目，怎样避免越界和误操作？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [RecyclerView API](https://developer.android.com/reference/androidx/recyclerview/widget/RecyclerView)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

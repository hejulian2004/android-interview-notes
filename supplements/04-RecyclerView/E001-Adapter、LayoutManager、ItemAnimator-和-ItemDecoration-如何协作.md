---
id: E001
title: "Adapter、LayoutManager、ItemAnimator 和 ItemDecoration 如何协作"
category: "04-RecyclerView"
kind: supplement
priority: P0
updated_at: "2026-10-30"
---

# E001 · Adapter、LayoutManager、ItemAnimator 和 ItemDecoration 如何协作

类别：04-RecyclerView　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 题目性质

**补充练习，不计入来源题数量，也不归属于任何公司的确定面试记录。** 本题用于补齐复习主题，不能写成“某公司近三年问过”。

## 参考回答提纲

Adapter 提供项目与绑定，LayoutManager 决定布局和滚动，ItemAnimator 负责项目变化动画，ItemDecoration 增加装饰或偏移。将职责拆开才能判断问题应该在哪层修复。

## 易错点

不要把布局策略放进数据层，也不要用装饰绘制取代必要的可访问性内容。

## 延伸追问（整理者设计，不是原帖原题）

为异构卡片列表增加分隔线时，如何避免影响首尾间距？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [RecyclerView API](https://developer.android.com/reference/androidx/recyclerview/widget/RecyclerView)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

---
id: E012
title: "如何把现有 Custom View 嵌入 Compose"
category: "05-JetpackCompose"
kind: supplement
priority: P1
updated_at: "2026-10-30"
---

# E012 · 如何把现有 Custom View 嵌入 Compose

类别：05-JetpackCompose　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 题目性质

**补充练习，不计入来源题数量，也不归属于任何公司的确定面试记录。** 本题用于补齐复习主题，不能写成“某公司近三年问过”。

## 参考回答提纲

通过 AndroidView 创建并更新 View，明确状态如何流入以及回调如何流出。处理释放、生命周期和列表复用相关回调，避免在 update 中反复创建昂贵对象。

## 易错点

互操作不是忽略 View 生命周期的理由，也不需要为一个控件把整个页面退回 XML。

## 延伸追问（整理者设计，不是原帖原题）

嵌入播放器或地图时，谁负责释放底层资源？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [Compose 与 View 互操作](https://developer.android.com/develop/ui/compose/migrate/interoperability-apis)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

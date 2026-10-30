---
id: E008
title: "remember 与 rememberSaveable 有什么边界"
category: "05-JetpackCompose"
kind: supplement
priority: P0
updated_at: "2026-10-30"
---

# E008 · remember 与 rememberSaveable 有什么边界

类别：05-JetpackCompose　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 题目性质

**补充练习，不计入来源题数量，也不归属于任何公司的确定面试记录。** 本题用于补齐复习主题，不能写成“某公司近三年问过”。

## 参考回答提纲

remember 在相应组合位置存续期间缓存值；rememberSaveable 可借助保存机制恢复符合条件的状态。重要业务数据仍需数据库或其他持久化，保存大量对象也不合适。

## 易错点

两者都不是任意情况下永不丢失的数据存储。

## 延伸追问（整理者设计，不是原帖原题）

屏幕旋转、离开导航页面、系统回收进程分别怎样测试？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [Compose 状态](https://developer.android.com/develop/ui/compose/state)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

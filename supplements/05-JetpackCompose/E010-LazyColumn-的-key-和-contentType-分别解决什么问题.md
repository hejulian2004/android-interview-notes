---
id: E010
title: "LazyColumn 的 key 和 contentType 分别解决什么问题"
category: "05-JetpackCompose"
kind: supplement
priority: P0
updated_at: "2026-10-30"
---

# E010 · LazyColumn 的 key 和 contentType 分别解决什么问题

类别：05-JetpackCompose　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 题目性质

**补充练习，不计入来源题数量，也不归属于任何公司的确定面试记录。** 本题用于补齐复习主题，不能写成“某公司近三年问过”。

## 参考回答提纲

key 标识项目身份，帮助重排时匹配状态；contentType 描述结构兼容性，帮助组合复用。身份稳定与类型准确应分别建模，不能让所有随机 key 每次都变化。

## 易错点

使用当前位置当作可重排业务数据的唯一身份，可能导致状态错位。

## 延伸追问（整理者设计，不是原帖原题）

文件列表插入一条新记录后，怎样保持选中和滚动位置？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [Compose 懒加载列表](https://developer.android.com/develop/ui/compose/lists)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

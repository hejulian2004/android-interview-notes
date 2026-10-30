---
id: E013
title: "Compose 中副作用为什么需要明确作用域"
category: "05-JetpackCompose"
kind: supplement
priority: P1
updated_at: "2026-10-30"
---

# E013 · Compose 中副作用为什么需要明确作用域

类别：05-JetpackCompose　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 题目性质

**补充练习，不计入来源题数量，也不归属于任何公司的确定面试记录。** 本题用于补齐复习主题，不能写成“某公司近三年问过”。

## 参考回答提纲

组合描述 UI，不宜直接执行不可控外部动作。使用适当 effect API 绑定启动、重启和清理条件，明确 key 的含义；业务请求也可能更适合由 ViewModel 管理。

## 易错点

在 Composable 函数体直接发请求会把重组变成重复副作用。

## 延伸追问（整理者设计，不是原帖原题）

导航返回后需要重启请求还是复用结果，作用域应怎样选择？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [Compose 副作用](https://developer.android.com/develop/ui/compose/side-effects)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

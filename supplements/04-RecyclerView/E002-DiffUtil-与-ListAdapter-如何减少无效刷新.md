---
id: E002
title: "DiffUtil 与 ListAdapter 如何减少无效刷新"
category: "04-RecyclerView"
kind: supplement
priority: P0
updated_at: "2026-10-30"
---

# E002 · DiffUtil 与 ListAdapter 如何减少无效刷新

类别：04-RecyclerView　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 题目性质

**补充练习，不计入来源题数量，也不归属于任何公司的确定面试记录。** 本题用于补齐复习主题，不能写成“某公司近三年问过”。

## 参考回答提纲

DiffUtil 比较身份与内容生成更新操作；ListAdapter 借助差分器管理提交和更新。旧新列表及参与比较的数据在差分期间应保持不变，身份相同与内容相同是两个不同判断。

## 易错点

原地修改已提交列表后再提交同一实例，可能无法得到预期更新。

## 延伸追问（整理者设计，不是原帖原题）

列表快速连续提交时，怎样处理旧计算结果？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [DiffUtil API](https://developer.android.com/reference/androidx/recyclerview/widget/DiffUtil)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

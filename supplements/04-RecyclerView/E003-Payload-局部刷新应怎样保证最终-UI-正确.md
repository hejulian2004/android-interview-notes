---
id: E003
title: "Payload 局部刷新应怎样保证最终 UI 正确"
category: "04-RecyclerView"
kind: supplement
priority: P1
updated_at: "2026-10-30"
---

# E003 · Payload 局部刷新应怎样保证最终 UI 正确

类别：04-RecyclerView　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 题目性质

**补充练习，不计入来源题数量，也不归属于任何公司的确定面试记录。** 本题用于补齐复习主题，不能写成“某公司近三年问过”。

## 参考回答提纲

Payload 表达局部变化，局部绑定只更新相应属性，但完整绑定必须能恢复该项目全部显示状态。离屏更新等情况下不能假定一定收到全部 payload。

## 易错点

以 payload 更新作为唯一状态来源，会在回收复用后出现显示错误。

## 延伸追问（整理者设计，不是原帖原题）

只有收藏图标改变时，怎样避免重新触发整张图片请求？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [RecyclerView API](https://developer.android.com/reference/androidx/recyclerview/widget/RecyclerView)（网页入口已核查）
- [DiffUtil API](https://developer.android.com/reference/androidx/recyclerview/widget/DiffUtil)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

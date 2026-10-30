---
id: E011
title: "Compose 与 RecyclerView 怎样做公平性能对比"
category: "05-JetpackCompose"
kind: supplement
priority: P1
updated_at: "2026-10-30"
---

# E011 · Compose 与 RecyclerView 怎样做公平性能对比

类别：05-JetpackCompose　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 题目性质

**补充练习，不计入来源题数量，也不归属于任何公司的确定面试记录。** 本题用于补齐复习主题，不能写成“某公司近三年问过”。

## 参考回答提纲

固定设备、数据、图片缓存状态、构建模式和操作脚本，测帧时间分布、卡顿、分配与内存。两边先做合理优化，分别报告启动与持续滚动，不凭单一案例宣布框架全面获胜。

## 易错点

Debug 截图、一次肉眼判断或不同缓存条件不能证明性能优劣。

## 延伸追问（整理者设计，不是原帖原题）

120Hz 与 60Hz 的帧预算不同，报告应怎样标注？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [慢渲染排查](https://developer.android.com/topic/performance/issues/render)（网页入口已核查）
- [Compose 性能最佳实践](https://developer.android.com/develop/ui/compose/performance/bestpractices)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

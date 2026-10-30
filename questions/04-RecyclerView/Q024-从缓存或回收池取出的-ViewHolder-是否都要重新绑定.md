---
id: Q024
title: "从缓存或回收池取出的 ViewHolder 是否都要重新绑定"
category: "04-RecyclerView"
kind: observed
priority: P0
updated_at: "2026-10-30"
---

# Q024 · 从缓存或回收池取出的 ViewHolder 是否都要重新绑定

类别：04-RecyclerView　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S007 · 腾讯

提问线索：Scrap、Cache 复用与重新绑定。

面试日期：2024-07-23；帖子显示：2024-09-05（已编辑）。
日期依据：**面试年份由上下文推定**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/2ff38936c23e48deba9eb28b63b87f2a?sourceSSR=dynamic) · [来源档案与限制](../../sources/S007.md)

## 参考回答提纲

有效且仍对应目标数据的已绑定 holder，某些缓存命中可避免再次绑定；从按类型组织的池中取出的 holder 通常需要绑定到目标项目。是否重绑取决于更新标记、位置和布局阶段等条件。

## 易错点

onBindViewHolder 不是每次屏幕绘制都会调用；onViewRecycled 也不是每次移出可视区域都会调用。

## 延伸追问（整理者设计，不是原帖原题）

只更新某一行的选中状态，怎样保证旧 holder 不残留状态？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [RecyclerView API](https://developer.android.com/reference/androidx/recyclerview/widget/RecyclerView)（网页入口已核查）
- [AndroidX RecyclerView 源码（androidx-main，可变化分支）](https://android.googlesource.com/platform/frameworks/support/+/androidx-main/recyclerview/recyclerview/src/main/java/androidx/recyclerview/widget/RecyclerView.java)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

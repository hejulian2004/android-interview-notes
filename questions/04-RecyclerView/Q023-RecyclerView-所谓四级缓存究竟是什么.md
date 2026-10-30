---
id: Q023
title: "RecyclerView 所谓四级缓存究竟是什么"
category: "04-RecyclerView"
kind: observed
priority: P0
updated_at: "2026-10-30"
---

# Q023 · RecyclerView 所谓四级缓存究竟是什么

类别：04-RecyclerView　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S007 · 腾讯

提问线索：社招：缓存层级。

面试日期：2024-07-23；帖子显示：2024-09-05（已编辑）。
日期依据：**面试年份由上下文推定**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/2ff38936c23e48deba9eb28b63b87f2a?sourceSSR=dynamic) · [来源档案与限制](../../sources/S007.md)

### S011 · 百度

提问线索：二面：RecyclerView 四级缓存。

面试日期：未明确；帖子显示：2025-04-08。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/6c2b6b3c15bc40e2b25fef6662c77988) · [来源档案与限制](../../sources/S011.md)

## 参考回答提纲

常见教学划分为布局临时 Scrap、离屏 mCachedViews、可选 ViewCacheExtension 和按 viewType 保存的 RecycledViewPool。实际查找受预布局、位置、标识和有效性约束，并非四个固定顺序队列；回答应结合具体 AndroidX 版本。

## 易错点

不要将“滑出屏幕”直接等同于“进入池中”，也不要把所有缓存命中都说成无需绑定。

## 延伸追问（整理者设计，不是原帖原题）

快速向下滑再滑回来时，怎样用日志判断命中的是哪条路径？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [RecyclerView API](https://developer.android.com/reference/androidx/recyclerview/widget/RecyclerView)（网页入口已核查）
- [AndroidX RecyclerView 源码（androidx-main，可变化分支）](https://android.googlesource.com/platform/frameworks/support/+/androidx-main/recyclerview/recyclerview/src/main/java/androidx/recyclerview/widget/RecyclerView.java)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

---
id: Q025
title: "RecyclerView 预取为什么能改善滚动"
category: "04-RecyclerView"
kind: observed
priority: P1
updated_at: "2026-10-30"
---

# Q025 · RecyclerView 预取为什么能改善滚动

类别：04-RecyclerView　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S007 · 腾讯

提问线索：社招：预取策略。

面试日期：2024-07-23；帖子显示：2024-09-05（已编辑）。
日期依据：**面试年份由上下文推定**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/2ff38936c23e48deba9eb28b63b87f2a?sourceSSR=dynamic) · [来源档案与限制](../../sources/S007.md)

## 参考回答提纲

预取尝试利用滚动过程中可用的时间预算，提前准备将要出现的项目，减少临界帧内的创建和绑定工作。能否收益取决于绑定成本、滚动方向和内存压力，应通过 trace 对照验证。

## 易错点

预取不是提前创建所有数据，也不能掩盖主线程同步解码或 I/O。

## 延伸追问（整理者设计，不是原帖原题）

嵌套横向列表的预取数量应如何用实验确定？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [RecyclerView API](https://developer.android.com/reference/androidx/recyclerview/widget/RecyclerView)（网页入口已核查）
- [AndroidX RecyclerView 源码（androidx-main，可变化分支）](https://android.googlesource.com/platform/frameworks/support/+/androidx-main/recyclerview/recyclerview/src/main/java/androidx/recyclerview/widget/RecyclerView.java)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

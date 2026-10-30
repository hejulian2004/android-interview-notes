---
id: Q068
title: "ViewModel 为什么能跨配置变化保留状态"
category: "10-Jetpack架构与存储"
kind: observed
priority: P0
updated_at: "2026-10-30"
---

# Q068 · ViewModel 为什么能跨配置变化保留状态

类别：10-Jetpack架构与存储　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S012 · 滴滴

提问线索：ViewModel 与 Activity 生命周期。

面试日期：未明确；帖子显示：2025-05-24。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/3b35b2df975b4ff7a8ab9039a5f38277?sourceSSR=subject) · [来源档案与限制](../../sources/S012.md)

### S014 · 字节跳动

提问线索：ViewModel 生命周期。

面试日期：未明确；帖子显示：2025-07-10（已编辑）。
日期依据：**仅帖子日期**；访问状态：检索索引可见。

[原始面经](https://www.nowcoder.com/discuss/772917438592581632) · [来源档案与限制](../../sources/S014.md)

## 参考回答提纲

它由 ViewModelStoreOwner 管理，生命周期取决于 owner 而非某次 View 创建；配置重建时可以沿用对应存储。业务状态、可恢复 UI 状态和持久数据要分层，进程死亡后需要 SavedStateHandle 或持久化补充。

## 易错点

ViewModel 不自动抗进程死亡，也不应长期持有 Activity 或 View。

## 延伸追问（整理者设计，不是原帖原题）

导航图级和 Activity 级 ViewModel 的共享边界有何不同？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [ViewModel 概览](https://developer.android.com/topic/libraries/architecture/viewmodel)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

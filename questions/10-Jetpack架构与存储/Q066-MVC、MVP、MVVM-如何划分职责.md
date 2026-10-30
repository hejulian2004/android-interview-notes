---
id: Q066
title: "MVC、MVP、MVVM 如何划分职责"
category: "10-Jetpack架构与存储"
kind: observed
priority: P0
updated_at: "2026-10-30"
---

# Q066 · MVC、MVP、MVVM 如何划分职责

类别：10-Jetpack架构与存储　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S004 · 阿里巴巴

提问线索：架构模式。

面试日期：未明确；帖子显示：2024-03-27。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/4987069fb95942c7aeac2e118053c897) · [来源档案与限制](../../sources/S004.md)

### S010 · 京东

提问线索：MVVM 与 MVC。

面试日期：未明确；帖子显示：2025-04-01。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/f87cbbe5bebd4949823a5a68dec04e52?sourceSSR=users) · [来源档案与限制](../../sources/S010.md)

### S012 · 滴滴

提问线索：MVVM 与 Jetpack。

面试日期：未明确；帖子显示：2025-05-24。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/3b35b2df975b4ff7a8ab9039a5f38277?sourceSSR=subject) · [来源档案与限制](../../sources/S012.md)

## 参考回答提纲

用同一个登录业务说明 UI、状态、业务规则和数据访问分别放在哪里。重点是依赖方向、生命周期与可测试性，而不是给类名加后缀。Android 推荐的分层和单向数据流可以辅助落地，但模式不是唯一正确结构。

## 易错点

有 ViewModel 类并不自动等于良好 MVVM；把网络、数据库和导航全部塞进其中仍可能过度耦合。

## 延伸追问（整理者设计，不是原帖原题）

不启动 Activity，如何测试登录失败和重试逻辑？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [Android 架构建议](https://developer.android.com/topic/architecture/recommendations)（网页入口已核查）
- [ViewModel 概览](https://developer.android.com/topic/libraries/architecture/viewmodel)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

---
id: Q085
title: "MediaPlayer 为什么必须遵守状态机"
category: "13-音视频与Native"
kind: observed
priority: P1
updated_at: "2026-10-30"
---

# Q085 · MediaPlayer 为什么必须遵守状态机

类别：13-音视频与Native　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S019 · 滴滴

提问线索：二面：MediaPlayer 状态。

面试日期：未明确；帖子显示：2025-10-26。
日期依据：**仅帖子日期**；访问状态：检索索引可见。

[原始面经](https://www.nowcoder.com/feed/main/detail/864651bb82764281a3f0f5af7a9b6d0a?sourceSSR=users) · [来源档案与限制](../../sources/S019.md)

## 参考回答提纲

用创建、设置数据源、准备、播放、暂停、停止、释放说明合法调用关系，并区分同步和异步准备。错误与完成回调也是状态转换的一部分；页面销毁和后台播放要明确资源所有者。

## 易错点

不能在任意状态调用 start、seek 或 prepare；释放后继续调用旧实例也有风险。

## 延伸追问（整理者设计，不是原帖原题）

网络断开和重新播放应复用还是重建实例，依据是什么？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [MediaPlayer 状态与资源](https://developer.android.com/media/platform/mediaplayer/state-resources)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

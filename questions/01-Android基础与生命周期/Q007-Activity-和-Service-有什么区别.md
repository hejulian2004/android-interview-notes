---
id: Q007
title: "Activity 和 Service 有什么区别"
category: "01-Android基础与生命周期"
kind: observed
priority: P1
updated_at: "2026-10-30"
---

# Q007 · Activity 和 Service 有什么区别

类别：01-Android基础与生命周期　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S019 · 滴滴

提问线索：二面：Activity 与 Service。

面试日期：未明确；帖子显示：2025-10-26。
日期依据：**仅帖子日期**；访问状态：检索索引可见。

[原始面经](https://www.nowcoder.com/feed/main/detail/864651bb82764281a3f0f5af7a9b6d0a?sourceSSR=users) · [来源档案与限制](../../sources/S019.md)

## 参考回答提纲

Activity 的核心是用户交互和窗口生命周期；Service 不提供界面，可被启动或绑定。组件生命周期与执行线程是两个维度：耗时任务仍需专门调度，并遵循后台执行及前台服务限制。

## 易错点

不要通过“Service 永不被杀”来设计可靠任务；长期工作还需持久化、恢复和取消机制。

## 延伸追问（整理者设计，不是原帖原题）

音乐播放为什么要分离播放状态、通知和页面生命周期？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [Android 进程与线程](https://developer.android.com/guide/components/processes-and-threads)（网页入口已核查）
- [MediaPlayer 状态与资源](https://developer.android.com/media/platform/mediaplayer/state-resources)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

---
id: Q013
title: "IdleHandler 适合放哪些工作"
category: "02-Handler线程与IPC"
kind: observed
priority: P1
updated_at: "2026-10-30"
---

# Q013 · IdleHandler 适合放哪些工作

类别：02-Handler线程与IPC　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S007 · 腾讯

提问线索：社招：IdleHandler。

面试日期：2024-07-23；帖子显示：2024-09-05（已编辑）。
日期依据：**面试年份由上下文推定**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/2ff38936c23e48deba9eb28b63b87f2a?sourceSSR=dynamic) · [来源档案与限制](../../sources/S007.md)

## 参考回答提纲

它用于队列进入可处理空闲回调的时机，不保证固定时间执行。适合短小、可延后的工作；耗时任务应拆分或交给后台。返回值决定是否保留该回调，需要自行处理业务取消条件。

## 易错点

队列忙时可能迟迟没有机会运行；空闲回调依然在所属 Looper 线程执行。

## 延伸追问（整理者设计，不是原帖原题）

为什么不能把所有初始化都无条件塞进 IdleHandler？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [MessageQueue.IdleHandler API](https://developer.android.com/reference/android/os/MessageQueue.IdleHandler)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

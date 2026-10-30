---
id: Q012
title: "Looper 队列空闲时为什么不会一直占用 CPU"
category: "02-Handler线程与IPC"
kind: observed
priority: P0
updated_at: "2026-10-30"
---

# Q012 · Looper 队列空闲时为什么不会一直占用 CPU

类别：02-Handler线程与IPC　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S011 · 百度

提问线索：二面：Handler 阻塞与唤醒。

面试日期：未明确；帖子显示：2025-04-08。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/6c2b6b3c15bc40e2b25fef6662c77988) · [来源档案与限制](../../sources/S011.md)

## 参考回答提纲

没有立即可执行消息时，消息循环可以进入 native 等待，由事件或超时唤醒，而不是持续空转。区分线程阻塞等待、主线程被业务工作阻塞，以及进程结束三种情况。

## 易错点

“主线程死循环所以一定 ANR”混淆了事件循环和不能及时响应事件的长任务。

## 延伸追问（整理者设计，不是原帖原题）

加入更早到期的消息时，已有等待怎样被打断？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [Looper API](https://developer.android.com/reference/android/os/Looper)（网页入口已核查）
- [AOSP MessageQueue 源码入口（本次未成功直读）](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/core/java/android/os/MessageQueue.java)（本次未成功核查页面，仅保留学习入口）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

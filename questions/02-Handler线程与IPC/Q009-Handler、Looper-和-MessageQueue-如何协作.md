---
id: Q009
title: "Handler、Looper 和 MessageQueue 如何协作"
category: "02-Handler线程与IPC"
kind: observed
priority: P0
updated_at: "2026-10-30"
---

# Q009 · Handler、Looper 和 MessageQueue 如何协作

类别：02-Handler线程与IPC　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S002 · 美团

提问线索：一面：Handler。

面试日期：未明确；帖子显示：2023-11-02（已编辑）。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/6bce20c6f8f94b6397f13a4ac706dbbe) · [来源档案与限制](../../sources/S002.md)

### S006 · 字节跳动

提问线索：Handler 与消息队列。

面试日期：2024-07-08；帖子显示：2024-07-08。
日期依据：**面试年份由上下文推定**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/ccc1fe43cdd341ce9317578eb8fa44e9) · [来源档案与限制](../../sources/S006.md)

### S020 · 小米

提问线索：Handler 将任务交给哪个线程。

面试日期：2026-10-22；帖子显示：10-23（页面省略年份，已编辑）。
日期依据：**面试年份由上下文推定**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/27424c8609eb43c9aee0b0cbb57584eb) · [来源档案与限制](../../sources/S020.md)

## 参考回答提纲

Handler 将消息或 Runnable 加入关联 Looper 的消息队列；Looper 在所属线程依次取出并分发。处理线程由绑定的 Looper 决定，不由发送消息的线程决定。创建后台 Looper 时还要考虑退出、任务取消和资源释放。

## 易错点

不能因为在子线程调用某个主线程 Handler，就认为回调也在子线程执行。

## 延伸追问（整理者设计，不是原帖原题）

多个 Handler 绑定同一个 Looper，是否创建了多条工作线程？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [Handler API](https://developer.android.com/reference/android/os/Handler)（网页入口已核查）
- [Looper API](https://developer.android.com/reference/android/os/Looper)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

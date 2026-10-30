---
id: Q053
title: "ReentrantLock 相比 synchronized 多了哪些控制能力"
category: "08-并发与线程安全"
kind: observed
priority: P1
updated_at: "2026-10-30"
---

# Q053 · ReentrantLock 相比 synchronized 多了哪些控制能力

类别：08-并发与线程安全　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S020 · 小米

提问线索：可中断锁与公平锁。

面试日期：2026-10-22；帖子显示：10-23（页面省略年份，已编辑）。
日期依据：**面试年份由上下文推定**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/27424c8609eb43c9aee0b0cbb57584eb) · [来源档案与限制](../../sources/S020.md)

## 参考回答提纲

可讨论尝试获取、限时等待、可中断等待、公平性选择与多个 Condition。使用显式锁时必须在 finally 释放；比较应基于所需语义，而不是笼统宣称某种锁更快。

## 易错点

公平锁不保证整个应用业务任务严格 FIFO，也通常有吞吐权衡。

## 延伸追问（整理者设计，不是原帖原题）

需要超时取消的资源申请，怎样组织锁获取与清理？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [ReentrantLock API](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/locks/ReentrantLock.html)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

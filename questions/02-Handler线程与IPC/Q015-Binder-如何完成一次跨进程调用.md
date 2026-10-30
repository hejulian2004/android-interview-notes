---
id: Q015
title: "Binder 如何完成一次跨进程调用"
category: "02-Handler线程与IPC"
kind: observed
priority: P0
updated_at: "2026-10-30"
---

# Q015 · Binder 如何完成一次跨进程调用

类别：02-Handler线程与IPC　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S002 · 美团

提问线索：一面：IPC 与 Binder。

面试日期：未明确；帖子显示：2023-11-02（已编辑）。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/6bce20c6f8f94b6397f13a4ac706dbbe) · [来源档案与限制](../../sources/S002.md)

### S016 · 蔚来

提问线索：IPC 和 Binder。

面试日期：未明确；帖子显示：2025-09-15。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/discuss/797066691023736832?sourceSSR=enterprise) · [来源档案与限制](../../sources/S016.md)

## 参考回答提纲

以客户端代理、Parcel 序列化、Binder 驱动、服务端 Stub 和线程池说明调用链。同步调用会等待结果，服务端方法通常不在应用主线程执行。再补充调用者身份校验、进程死亡、并发和大数据传输的设计。

## 易错点

不要把“只复制一次”当作所有调用无条件更快的结论；序列化、调度和阻塞也有成本。

## 延伸追问（整理者设计，不是原帖原题）

服务端进程退出后，客户端怎样恢复连接而不重复执行业务？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [AOSP Binder 概览](https://source.android.com/docs/core/architecture/ipc/binder-overview)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

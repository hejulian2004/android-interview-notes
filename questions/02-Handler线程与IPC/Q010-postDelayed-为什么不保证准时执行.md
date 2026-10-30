---
id: Q010
title: "postDelayed 为什么不保证准时执行"
category: "02-Handler线程与IPC"
kind: observed
priority: P0
updated_at: "2026-10-30"
---

# Q010 · postDelayed 为什么不保证准时执行

类别：02-Handler线程与IPC　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S006 · 字节跳动

提问线索：post、postDelayed 和队列时序。

面试日期：2024-07-08；帖子显示：2024-07-08。
日期依据：**面试年份由上下文推定**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/ccc1fe43cdd341ce9317578eb8fa44e9) · [来源档案与限制](../../sources/S006.md)

## 参考回答提纲

延迟表示消息在指定 uptime 时间之后才有资格被处理，而不是届时必然执行。主线程正忙、队列中其他任务、同步屏障或设备休眠都会影响实际触发时间。对精确时序需求要先明确时钟来源与调度保证。

## 易错点

不要把它当作实时定时器；UI 时间显示更应基于时钟差计算，而非累计回调次数。

## 延伸追问（整理者设计，不是原帖原题）

倒计时页面暂停数秒后怎样保证显示仍正确？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [Handler API](https://developer.android.com/reference/android/os/Handler)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

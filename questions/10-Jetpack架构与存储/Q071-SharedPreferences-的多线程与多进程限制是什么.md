---
id: Q071
title: "SharedPreferences 的多线程与多进程限制是什么"
category: "10-Jetpack架构与存储"
kind: observed
priority: P1
updated_at: "2026-10-30"
---

# Q071 · SharedPreferences 的多线程与多进程限制是什么

类别：10-Jetpack架构与存储　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S009 · 快手

提问线索：二面：SP 多线程与多进程。

面试日期：2025-03-06 / 2025-03-10；帖子显示：2025-03-13（已编辑）。
日期依据：**面试年份由上下文推定**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/9b9f932f60a345afb0f20162a0374e50) · [来源档案与限制](../../sources/S009.md)

## 参考回答提纲

区分单进程中的方法调用安全与读取后修改的复合原子性；并发读改写仍可能丢失业务更新。普通 SharedPreferences 不支持可靠的跨进程协调，apply 的内存更新与磁盘持久化也不是同一时点。

## 易错点

不能因为 apply 异步，就断言它永远不会影响主线程生命周期切换。

## 延伸追问（整理者设计，不是原帖原题）

计数器由两个线程同时读取并加一，如何避免覆盖？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [SharedPreferences API](https://developer.android.com/reference/android/content/SharedPreferences)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

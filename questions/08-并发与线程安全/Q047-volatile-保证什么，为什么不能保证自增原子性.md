---
id: Q047
title: "volatile 保证什么，为什么不能保证自增原子性"
category: "08-并发与线程安全"
kind: observed
priority: P0
updated_at: "2026-10-30"
---

# Q047 · volatile 保证什么，为什么不能保证自增原子性

类别：08-并发与线程安全　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S004 · 阿里巴巴

提问线索：volatile 与非原子自增。

面试日期：未明确；帖子显示：2024-03-27。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/4987069fb95942c7aeac2e118053c897) · [来源档案与限制](../../sources/S004.md)

### S020 · 小米

提问线索：volatile 和 i++。

面试日期：2026-10-22；帖子显示：10-23（页面省略年份，已编辑）。
日期依据：**面试年份由上下文推定**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/27424c8609eb43c9aee0b0cbb57584eb) · [来源档案与限制](../../sources/S020.md)

## 参考回答提纲

volatile 约束可见性与相关内存顺序，但 i++ 包含读、计算、写多个步骤，多个线程可丢失更新。用锁或原子读改写操作实现计数，再解释 happens-before 而不是用“强制刷新所有缓存”替代理由。

## 易错点

可见性、原子性和有序性是不同问题，不能互相替代。

## 延伸追问（整理者设计，不是原帖原题）

volatile boolean 停止标记与 volatile int 计数器为何有不同安全结论？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [JLS 17：线程与锁](https://docs.oracle.com/javase/specs/jls/se17/html/jls-17.html)（网页入口已核查）
- [Java 原子变量 API](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/atomic/package-summary.html)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

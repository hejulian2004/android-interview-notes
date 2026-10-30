---
id: Q016
title: "为什么大数据不应直接塞进 Binder 事务"
category: "02-Handler线程与IPC"
kind: observed
priority: P2
updated_at: "2026-10-30"
---

# Q016 · 为什么大数据不应直接塞进 Binder 事务

类别：02-Handler线程与IPC　｜　方向：应用开发　｜　学习优先级：P2（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S029 · 阿里巴巴

提问线索：播放优化：Binder 上限和共享 fd。

面试日期：2024（具体月日不明）；帖子显示：2024-07-28（作者专栏日期）。
日期依据：**面试年份明确**；访问状态：正文已读取。

[原始面经](https://blog.csdn.net/R3lish/article/details/140750384) · [来源档案与限制](../../sources/S029.md)

## 参考回答提纲

Binder 适合传递控制消息与小型结构化数据。大型载荷要考虑事务缓冲区、并发事务和序列化开销；可传递文件描述符或共享内存句柄，并明确所有权、访问权限和关闭时机。

## 易错点

不要假定“单次小于某个数字就绝对安全”；共享内存也不等于任意 Java 对象天然跨进程共享。

## 延伸追问（整理者设计，不是原帖原题）

共享数据正在被写入时，读端怎样获得一致快照？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [AOSP Binder 概览](https://source.android.com/docs/core/architecture/ipc/binder-overview)（网页入口已核查）
- [SharedMemory API](https://developer.android.com/reference/android/os/SharedMemory)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

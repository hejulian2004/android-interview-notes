---
id: Q036
title: "ConcurrentHashMap 如何支持并发访问"
category: "07-Java集合与JVM"
kind: observed
priority: P0
updated_at: "2026-10-30"
---

# Q036 · ConcurrentHashMap 如何支持并发访问

类别：07-Java集合与JVM　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S002 · 美团

提问线索：一面：ConcurrentHashMap。

面试日期：未明确；帖子显示：2023-11-02（已编辑）。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/6bce20c6f8f94b6397f13a4ac706dbbe) · [来源档案与限制](../../sources/S002.md)

### S005 · 哔哩哔哩

提问线索：HashMap、Hashtable 和并发容器。

面试日期：2024-04-12；帖子显示：2024-04-25（已编辑）。
日期依据：**面试日期明确**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/10da7a46c08d42c99c1655cfee0c1b08?sourceSSR=subject) · [来源档案与限制](../../sources/S005.md)

## 参考回答提纲

说明并发读写的 API 保证，再按具体 JDK/Android 版本谈细粒度同步和 CAS 等实现。get 后再 put 的复合业务并不会自动变为原子操作，可使用 putIfAbsent、compute 等适配语义。

## 易错点

不要混用不同版本的分段锁和桶级实现；容器线程安全不等于值对象内部也安全。

## 延伸追问（整理者设计，不是原帖原题）

怎样安全地为不存在的 key 初始化一个昂贵对象？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [ConcurrentHashMap API（Java 8）](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/ConcurrentHashMap.html)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

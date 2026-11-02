---
id: Q037
title: "ArrayList 为什么查询快而中间插入可能昂贵"
category: "07-Java集合与JVM"
kind: observed
priority: P1
updated_at: "2026-11-02"
---

# Q037 · ArrayList 为什么查询快而中间插入可能昂贵

类别：07-Java集合与JVM　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S002 · 美团

提问线索：一面：ArrayList。

面试日期：未明确；帖子显示：2023-11-02（已编辑）。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/6bce20c6f8f94b6397f13a4ac706dbbe) · [来源档案与限制](../../sources/S002.md)

### S003 · 小米

提问线索：Java 集合。

面试日期：未明确；帖子显示：2024-01-06（已编辑）。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/b8302581e1844e298da9d1fb7e2af3b8?sourceSSR=subject) · [来源档案与限制](../../sources/S003.md)

### S017 · vivo

提问线索：ArrayList 与 HashSet。

面试日期：2025-09-23；帖子显示：2025-11-11。
日期依据：**面试年份由上下文推定**；访问状态：检索索引可见。

[原始面经](https://www.nowcoder.com/feed/main/detail/237d9f1418df4f0d9ceb7d542fbb09e4) · [来源档案与限制](../../sources/S017.md)

## 参考回答提纲

数组提供按下标访问；中间插入或删除可能移动后续元素。动态扩容需要分配更大的存储并搬移，尾部追加通常具有摊还优势。容量、大小、迭代器失效与并发访问要分开讨论。 按 OpenJDK 17 源码，容量不足时用 grow/ArraysSupport 计算新容量，常见首选增长为旧容量的一半，但还受最小所需容量与溢出/上限处理影响，不是所有情况固定乘 1.5，更不是 Java API 对 Android 所有版本的承诺。多线程可选外部统一锁或 synchronizedList（遍历仍在同一包装对象的锁内）、读多写少时评估 CopyOnWriteArrayList，或发布不可变快照；单次调用同步不自动保证多步业务原子性。

## 易错点

不要把所有插入操作都概括成 O(1)，也不要认为 LinkedList 在真实设备上必然更快。

## 延伸追问（整理者设计，不是原帖原题）

已知最终元素数量时，预设容量有什么收益和代价？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [ArrayList API（Java 8）](https://docs.oracle.com/javase/8/docs/api/java/util/ArrayList.html)（网页入口已核查）
- [OpenJDK 17 ArrayList 源码](https://raw.githubusercontent.com/openjdk/jdk17u/master/src/java.base/share/classes/java/util/ArrayList.java)（网页入口已核查）
- [Collections.synchronizedList 及遍历同步](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/Collections.html#synchronizedList(java.util.List))（网页入口已核查）
- [CopyOnWriteArrayList 快照与复制代价](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CopyOnWriteArrayList.html)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

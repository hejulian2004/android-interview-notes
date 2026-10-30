---
id: Q035
title: "HashMap 如何定位元素并处理冲突和扩容"
category: "07-Java集合与JVM"
kind: observed
priority: P0
updated_at: "2026-10-30"
---

# Q035 · HashMap 如何定位元素并处理冲突和扩容

类别：07-Java集合与JVM　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S001 · 小红书

提问线索：二面：HashMap 冲突和扩容。

面试日期：2023-10-30；帖子显示：2023-11-08（已编辑）。
日期依据：**面试日期明确**；访问状态：检索索引可见。

[原始面经](https://www.nowcoder.com/discuss/551787076040015872) · [来源档案与限制](../../sources/S001.md)

### S008 · 美团

提问线索：HashMap 扩容。

面试日期：未明确；帖子显示：2025-02-17（已编辑）。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/592247f523b64d45bb0dd5f28bdfaf56) · [来源档案与限制](../../sources/S008.md)

### S017 · vivo

提问线索：集合原理。

面试日期：2025-09-23；帖子显示：2025-11-11。
日期依据：**面试年份由上下文推定**；访问状态：检索索引可见。

[原始面经](https://www.nowcoder.com/feed/main/detail/237d9f1418df4f0d9ceb7d542fbb09e4) · [来源档案与限制](../../sources/S017.md)

## 参考回答提纲

先通过哈希确定桶，再在桶内查找；冲突处理、树化阈值和迁移策略属于具体实现细节。以明确的 Java 版本讲数组、链表、树结构及容量与负载因子的权衡。它不提供并发更新安全保证。

## 易错点

不要把 JDK 7 的链表成环故事推广为每个 Android 运行时的现行实现。

## 延伸追问（整理者设计，不是原帖原题）

为什么容量、数据分布与键的 hashCode 质量都会影响性能？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [HashMap API（Java 8）](https://docs.oracle.com/javase/8/docs/api/java/util/HashMap.html)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

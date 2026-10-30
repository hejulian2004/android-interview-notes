---
id: Q034
title: "Java 的 equals、hashCode 与双等号如何区分"
category: "07-Java集合与JVM"
kind: observed
priority: P0
updated_at: "2026-10-30"
---

# Q034 · Java 的 equals、hashCode 与双等号如何区分

类别：07-Java集合与JVM　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S005 · 哔哩哔哩

提问线索：集合与对象比较。

面试日期：2024-04-12；帖子显示：2024-04-25（已编辑）。
日期依据：**面试日期明确**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/10da7a46c08d42c99c1655cfee0c1b08?sourceSSR=subject) · [来源档案与限制](../../sources/S005.md)

### S009 · 快手

提问线索：一面：== 与 equals。

面试日期：2025-03-06 / 2025-03-10；帖子显示：2025-03-13（已编辑）。
日期依据：**面试年份由上下文推定**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/9b9f932f60a345afb0f20162a0374e50) · [来源档案与限制](../../sources/S009.md)

### S020 · 小米

提问线索：equals 和 hashCode。

面试日期：2026-10-22；帖子显示：10-23（页面省略年份，已编辑）。
日期依据：**面试年份由上下文推定**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/27424c8609eb43c9aee0b0cbb57584eb) · [来源档案与限制](../../sources/S020.md)

## 参考回答提纲

Java 引用类型的 == 比较引用身份；equals 的意义由实现定义。相等对象必须有相等 hashCode，但哈希相等不推出对象相等。作为哈希键使用的字段应在入表后保持稳定，否则定位可能失效。

## 易错点

Object 默认 equals 并不是自动比较所有字段；Kotlin 的 == 又有不同语言语义。

## 延伸追问（整理者设计，不是原帖原题）

一个可变对象作为 HashMap 的 key，修改字段后为何可能取不到值？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [Object API（Java 8）](https://docs.oracle.com/javase/8/docs/api/java/lang/Object.html)（网页入口已核查）
- [HashMap API（Java 8）](https://docs.oracle.com/javase/8/docs/api/java/util/HashMap.html)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

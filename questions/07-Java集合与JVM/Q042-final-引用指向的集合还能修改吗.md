---
id: Q042
title: "final 引用指向的集合还能修改吗"
category: "07-Java集合与JVM"
kind: observed
priority: P1
updated_at: "2026-10-30"
---

# Q042 · final 引用指向的集合还能修改吗

类别：07-Java集合与JVM　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S005 · 哔哩哔哩

提问线索：final ArrayList 可否修改。

面试日期：2024-04-12；帖子显示：2024-04-25（已编辑）。
日期依据：**面试日期明确**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/10da7a46c08d42c99c1655cfee0c1b08?sourceSSR=subject) · [来源档案与限制](../../sources/S005.md)

## 参考回答提纲

final 限制变量再次赋值，不会使指向的对象自动不可变。集合仍可能增删元素，除非其 API 或实现禁止修改。要解释不可变对象、只读接口和不可修改包装之间的区别。

## 易错点

只禁止 set 引用并不能保证集合内容线程安全。

## 延伸追问（整理者设计，不是原帖原题）

Kotlin val 与 List 是否就能保证整个对象图不可变？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [JLS 4：类型、值与变量](https://docs.oracle.com/javase/specs/jls/se17/html/jls-4.html)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

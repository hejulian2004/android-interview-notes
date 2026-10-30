---
id: Q038
title: "Java 泛型擦除后还能获得哪些类型信息"
category: "07-Java集合与JVM"
kind: observed
priority: P1
updated_at: "2026-10-30"
---

# Q038 · Java 泛型擦除后还能获得哪些类型信息

类别：07-Java集合与JVM　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S001 · 小红书

提问线索：二面：泛型擦除与类型获取。

面试日期：2023-10-30；帖子显示：2023-11-08（已编辑）。
日期依据：**面试日期明确**；访问状态：检索索引可见。

[原始面经](https://www.nowcoder.com/discuss/551787076040015872) · [来源档案与限制](../../sources/S001.md)

## 参考回答提纲

区分运行时对象的实际类和声明在类、父类或方法签名中的泛型元数据。普通类型变量通常被擦除，但反射可能读取 Signature；匿名子类保留泛型声明的技巧依赖具体声明上下文。

## 易错点

不能保证从任意 List 实例恢复其所有元素的泛型实参；空列表尤其不能靠取元素猜类型。

## 延伸追问（整理者设计，不是原帖原题）

为什么某些序列化库要求传 TypeToken 而不是单个 Class？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [Kotlin 泛型与型变](https://kotlinlang.org/docs/generics.html)（网页入口已核查）
- [Java 泛型擦除](https://docs.oracle.com/javase/tutorial/java/generics/erasure.html)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

---
id: Q031
title: "Kotlin 的作用域函数应该怎样选择"
category: "06-Kotlin与协程"
kind: observed
priority: P1
updated_at: "2026-10-30"
---

# Q031 · Kotlin 的作用域函数应该怎样选择

类别：06-Kotlin与协程　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S020 · 小米

提问线索：一面：Kotlin 作用域函数。

面试日期：2026-10-22；帖子显示：10-23（页面省略年份，已编辑）。
日期依据：**面试年份由上下文推定**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/27424c8609eb43c9aee0b0cbb57584eb) · [来源档案与限制](../../sources/S020.md)

## 参考回答提纲

从两个维度回答：接收者以 this 还是 it 访问，返回接收者还是 lambda 结果。apply、also 常用于配置或旁路动作；let、run、with 常用于计算结果。选择应以可读性为主，避免层层嵌套导致接收者含糊。

## 易错点

作用域函数不会自动切换线程、保证原子性或处理生命周期。

## 延伸追问（整理者设计，不是原帖原题）

对 nullable 对象使用 let 与 run 时，安全调用分别放在哪里？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [Kotlin 作用域函数](https://kotlinlang.org/docs/scope-functions.html)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

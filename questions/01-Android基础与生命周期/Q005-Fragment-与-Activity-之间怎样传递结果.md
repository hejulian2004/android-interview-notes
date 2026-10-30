---
id: Q005
title: "Fragment 与 Activity 之间怎样传递结果"
category: "01-Android基础与生命周期"
kind: observed
priority: P1
updated_at: "2026-10-30"
---

# Q005 · Fragment 与 Activity 之间怎样传递结果

类别：01-Android基础与生命周期　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S008 · 美团

提问线索：一面：Fragment 与 Activity 通信。

面试日期：未明确；帖子显示：2025-02-17（已编辑）。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/592247f523b64d45bb0dd5f28bdfaf56) · [来源档案与限制](../../sources/S008.md)

## 参考回答提纲

依据通信范围选择共享 ViewModel、Fragment Result API 或明确的回调接口。共享 ViewModel 必须选对 Activity 或导航图作用域；一次性结果与长期状态应分开建模，避免通过静态字段持有页面。

## 易错点

共享 ViewModel 不等于整个 App 的全局单例，也不保证进程死亡后数据仍在。

## 延伸追问（整理者设计，不是原帖原题）

两个 Fragment 不在同一个导航图时如何定义状态所有者？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [Fragment 通信](https://developer.android.com/guide/fragments/communicate)（网页入口已核查）
- [ViewModel 概览](https://developer.android.com/topic/libraries/architecture/viewmodel)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

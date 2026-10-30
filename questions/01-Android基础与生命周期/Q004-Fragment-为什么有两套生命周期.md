---
id: Q004
title: "Fragment 为什么有两套生命周期"
category: "01-Android基础与生命周期"
kind: observed
priority: P0
updated_at: "2026-10-30"
---

# Q004 · Fragment 为什么有两套生命周期

类别：01-Android基础与生命周期　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S008 · 美团

提问线索：一面：Fragment 生命周期。

面试日期：未明确；帖子显示：2025-02-17（已编辑）。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/592247f523b64d45bb0dd5f28bdfaf56) · [来源档案与限制](../../sources/S008.md)

## 参考回答提纲

Fragment 实例和它创建的 View 生命周期不同，View 可以先被销毁而 Fragment 仍存在。与视图相关的绑定和观察使用 viewLifecycleOwner，在 onDestroyView 释放 ViewBinding；与 Fragment 自身相关的状态按其 owner 管理。

## 易错点

在 Fragment 生命周期内一直持有已销毁的 View，是常见泄漏来源；并非只有 onDestroy 才应清理。

## 延伸追问（整理者设计，不是原帖原题）

返回栈恢复 Fragment 时，哪些状态应保留，哪些视图应重新创建？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [Fragment 生命周期](https://developer.android.com/guide/fragments/lifecycle)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

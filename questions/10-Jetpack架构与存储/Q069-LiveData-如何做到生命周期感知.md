---
id: Q069
title: "LiveData 如何做到生命周期感知"
category: "10-Jetpack架构与存储"
kind: observed
priority: P0
updated_at: "2026-10-30"
---

# Q069 · LiveData 如何做到生命周期感知

类别：10-Jetpack架构与存储　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S010 · 京东

提问线索：一面：LiveData。

面试日期：未明确；帖子显示：2025-04-01。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/f87cbbe5bebd4949823a5a68dec04e52?sourceSSR=users) · [来源档案与限制](../../sources/S010.md)

## 参考回答提纲

观察者与 LifecycleOwner 关联，只在合适的活跃状态接收更新，销毁后解除关联。区分 setValue 与 postValue 的线程要求以及多次待投递值可能合并的行为，避免把状态容器当成无损事件队列。

## 易错点

observeForever 不自动受页面生命周期保护；postValue 不能被假设保留每一次中间值。

## 延伸追问（整理者设计，不是原帖原题）

为什么支付结果等一次性行为需要额外设计消费语义？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [LiveData 概览](https://developer.android.com/topic/libraries/architecture/livedata)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

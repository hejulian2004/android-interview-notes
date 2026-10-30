---
id: Q017
title: "View 的 measure、layout、draw 分别做什么"
category: "03-View绘制与触摸"
kind: observed
priority: P0
updated_at: "2026-10-30"
---

# Q017 · View 的 measure、layout、draw 分别做什么

类别：03-View绘制与触摸　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S002 · 美团

提问线索：一面：View 绘制。

面试日期：未明确；帖子显示：2023-11-02（已编辑）。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/6bce20c6f8f94b6397f13a4ac706dbbe) · [来源档案与限制](../../sources/S002.md)

### S007 · 腾讯

提问线索：View 渲染流程。

面试日期：2024-07-23；帖子显示：2024-09-05（已编辑）。
日期依据：**面试年份由上下文推定**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/2ff38936c23e48deba9eb28b63b87f2a?sourceSSR=dynamic) · [来源档案与限制](../../sources/S007.md)

### S020 · 小米

提问线索：View 绘制与自定义。

面试日期：2026-10-22；帖子显示：10-23（页面省略年份，已编辑）。
日期依据：**面试年份由上下文推定**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/27424c8609eb43c9aee0b0cbb57584eb) · [来源档案与限制](../../sources/S020.md)

## 参考回答提纲

measure 解决期望尺寸和父约束的协商；layout 确定最终位置；draw 产生视觉内容。父容器负责测量和放置子节点，自定义控件应正确处理 padding、最小尺寸与文本基线。硬件加速下还需区分 UI 线程记录绘制与后续渲染。

## 易错点

一次界面更新不必完整经历三阶段；onDraw 也不是所有子 View 的绘制入口。

## 延伸追问（整理者设计，不是原帖原题）

同一帧中为什么可能出现多次测量？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [自定义 View 绘制](https://developer.android.com/develop/ui/views/layout/custom-views/custom-drawing)（网页入口已核查）
- [AOSP 图形系统](https://source.android.com/docs/core/graphics)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

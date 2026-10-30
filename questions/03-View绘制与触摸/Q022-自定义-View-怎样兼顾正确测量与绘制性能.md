---
id: Q022
title: "自定义 View 怎样兼顾正确测量与绘制性能"
category: "03-View绘制与触摸"
kind: observed
priority: P1
updated_at: "2026-10-30"
---

# Q022 · 自定义 View 怎样兼顾正确测量与绘制性能

类别：03-View绘制与触摸　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S020 · 小米

提问线索：一面：自定义 View。

面试日期：2026-10-22；帖子显示：10-23（页面省略年份，已编辑）。
日期依据：**面试年份由上下文推定**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/27424c8609eb43c9aee0b0cbb57584eb) · [来源档案与限制](../../sources/S020.md)

## 参考回答提纲

先给出控件的期望尺寸，再结合 EXACTLY、AT_MOST、UNSPECIFIED 计算测量结果。把可复用 Paint、Path 等移出高频绘制路径，按尺寸变化重建必要缓存；测试 wrap_content、字体放大、RTL 与无障碍。

## 易错点

不要只画得正确却忽略测量约束，也不要每帧无条件创建大量临时对象。

## 延伸追问（整理者设计，不是原帖原题）

为什么缓存路径时必须处理尺寸和密度变化？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [自定义 View 绘制](https://developer.android.com/develop/ui/views/layout/custom-views/custom-drawing)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

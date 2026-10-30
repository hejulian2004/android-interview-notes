---
id: Q021
title: "怎样实现一个可拖动的自定义 View"
category: "03-View绘制与触摸"
kind: observed
priority: P1
updated_at: "2026-10-30"
---

# Q021 · 怎样实现一个可拖动的自定义 View

类别：03-View绘制与触摸　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S010 · 京东

提问线索：一面：可拖拽 View。

面试日期：未明确；帖子显示：2025-04-01。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/f87cbbe5bebd4949823a5a68dec04e52?sourceSSR=users) · [来源档案与限制](../../sources/S010.md)

## 参考回答提纲

记录活动 pointer、按下位置与控件初始偏移，超过 touch slop 后进入拖动；在 MOVE 更新位置，在 UP/CANCEL 结束。约束可移动边界，处理多指切换、父滚动冲突和点击可访问性。

## 易错点

raw 坐标、局部坐标与父容器坐标不能混用；只处理单指路径不等于手势实现完整。

## 延伸追问（整理者设计，不是原帖原题）

拖动过程中父布局尺寸改变，位置应该怎样修正？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [ViewGroup 触摸分发](https://developer.android.com/develop/ui/views/touch-and-input/gestures/viewgroup)（网页入口已核查）
- [自定义 View 绘制](https://developer.android.com/develop/ui/views/layout/custom-views/custom-drawing)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

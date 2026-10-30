---
id: Q020
title: "父容器中途拦截手势时子 View 会发生什么"
category: "03-View绘制与触摸"
kind: observed
priority: P0
updated_at: "2026-10-30"
---

# Q020 · 父容器中途拦截手势时子 View 会发生什么

类别：03-View绘制与触摸　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S016 · 蔚来

提问线索：嵌套 RecyclerView 与事件拦截。

面试日期：未明确；帖子显示：2025-09-15。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/discuss/797066691023736832?sourceSSR=enterprise) · [来源档案与限制](../../sources/S016.md)

## 参考回答提纲

父容器在 MOVE 阶段接管时，原触摸目标会收到取消事件，子控件应清理按压、拖拽等状态。是否拦截应依据方向、触摸阈值和剩余可滚动距离，而不是一开始无条件抢占。

## 易错点

忽略 ACTION_CANCEL 容易导致按压态不恢复或拖拽状态残留。

## 延伸追问（整理者设计，不是原帖原题）

requestDisallowInterceptTouchEvent 与 NestedScrolling 分别解决什么层次的问题？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [ViewGroup 触摸分发](https://developer.android.com/develop/ui/views/touch-and-input/gestures/viewgroup)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

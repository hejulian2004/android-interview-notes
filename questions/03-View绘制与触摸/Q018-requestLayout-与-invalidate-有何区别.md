---
id: Q018
title: "requestLayout 与 invalidate 有何区别"
category: "03-View绘制与触摸"
kind: observed
priority: P0
updated_at: "2026-10-30"
---

# Q018 · requestLayout 与 invalidate 有何区别

类别：03-View绘制与触摸　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S007 · 腾讯

提问线索：社招：requestLayout 和 invalidate。

面试日期：2024-07-23；帖子显示：2024-09-05（已编辑）。
日期依据：**面试年份由上下文推定**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/2ff38936c23e48deba9eb28b63b87f2a?sourceSSR=dynamic) · [来源档案与限制](../../sources/S007.md)

## 参考回答提纲

尺寸或布局规则改变时请求重新布局；仅颜色、进度等视觉内容变化时请求重绘。requestLayout 会让布局相关流程在后续遍历中重新处理，invalidate 主要标记绘制失效。两者都不是立即同步绘制。

## 易错点

不要把每次动画进度变化都升级为整棵树的重新测量。

## 延伸追问（整理者设计，不是原帖原题）

改变自定义 View 的描边宽度，什么时候还需要 requestLayout？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [View API](https://developer.android.com/reference/android/view/View)（网页入口已核查）
- [自定义 View 绘制](https://developer.android.com/develop/ui/views/layout/custom-views/custom-drawing)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

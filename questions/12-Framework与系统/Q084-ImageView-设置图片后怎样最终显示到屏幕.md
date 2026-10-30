---
id: Q084
title: "ImageView 设置图片后怎样最终显示到屏幕"
category: "12-Framework与系统"
kind: observed
priority: P2
updated_at: "2026-10-30"
---

# Q084 · ImageView 设置图片后怎样最终显示到屏幕

类别：12-Framework与系统　｜　方向：Framework/系统岗位　｜　学习优先级：P2（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S024 · 东莞拓久柘电子科技

提问线索：系统一面：Bitmap 到屏幕。

面试日期：2026-10-27；帖子显示：10-27（已编辑，页面省略年份）。
日期依据：**面试日期明确**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/discuss/944628400897933312?sourceSSR=%E5%85%B6%E4%BB%96) · [来源档案与限制](../../sources/S024.md)

## 参考回答提纲

从 Drawable 和视图失效开始，连接 UI 遍历、绘制命令、RenderThread/GPU、缓冲队列、SurfaceFlinger 与显示合成。不同渲染路径会有差异，重点区分应用画内容和系统合成多个窗口。

## 易错点

setImageBitmap 不等于立即把整张图同步复制到显示屏。

## 延伸追问（整理者设计，不是原帖原题）

CPU 帧耗时正常但画面掉帧，还应该查看哪些阶段？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [AOSP 图形系统](https://source.android.com/docs/core/graphics)（网页入口已核查）
- [Bitmap API](https://developer.android.com/reference/android/graphics/Bitmap)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

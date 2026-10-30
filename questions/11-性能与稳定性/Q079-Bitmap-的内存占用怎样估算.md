---
id: Q079
title: "Bitmap 的内存占用怎样估算"
category: "11-性能与稳定性"
kind: observed
priority: P1
updated_at: "2026-10-30"
---

# Q079 · Bitmap 的内存占用怎样估算

类别：11-性能与稳定性　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S010 · 京东

提问线索：一面：Bitmap 占用计算。

面试日期：未明确；帖子显示：2025-04-01。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/f87cbbe5bebd4949823a5a68dec04e52?sourceSSR=users) · [来源档案与限制](../../sources/S010.md)

## 参考回答提纲

先用像素宽高和每像素字节数估算，再考虑行对齐、配置、分配复用与 GPU 副本。例如无额外对齐的 1080×1920 ARGB_8888 像素数据约 8294400 字节；最终用 API 和分析工具验证实际分配。

## 易错点

JPEG 文件大小不是解码后内存大小；硬件位图与不同系统版本的内存归属也有差异。

## 延伸追问（整理者设计，不是原帖原题）

只显示缩略图时，应在哪个阶段缩小尺寸？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [Bitmap API](https://developer.android.com/reference/android/graphics/Bitmap)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

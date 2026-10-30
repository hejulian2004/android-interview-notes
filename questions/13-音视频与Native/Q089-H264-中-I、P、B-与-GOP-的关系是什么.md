---
id: Q089
title: "H264 中 I、P、B 与 GOP 的关系是什么"
category: "13-音视频与Native"
kind: observed
priority: P2
updated_at: "2026-10-30"
---

# Q089 · H264 中 I、P、B 与 GOP 的关系是什么

类别：13-音视频与Native　｜　方向：应用开发　｜　学习优先级：P2（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S023 · 保伦电子

提问线索：二面：H264、B/P 帧和 GOP。

面试日期：2026-09-23；帖子显示：09-23（页面省略年份）。
日期依据：**面试日期明确**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/discuss/932243541143670784?sourceSSR=%E5%85%B6%E4%BB%96) · [来源档案与限制](../../sources/S023.md)

## 参考回答提纲

从帧内与帧间预测理解 I、P、B 类型，再说明随机访问、参考关系、码率和延迟的权衡。GOP 设置会影响压缩效率与恢复能力；I 图像与 IDR 的语义不应混为一谈。

## 易错点

有 I 帧不一定表示后续解码完全不依赖更早参考；低延迟不只由 GOP 一个参数决定。

## 延伸追问（整理者设计，不是原帖原题）

直播更重视低延迟还是压缩率，如何影响编码参数？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [RFC 6184：H264 RTP 载荷与参数集](https://www.rfc-editor.org/rfc/rfc6184.html)（网页入口已核查）
- [MediaCodec API](https://developer.android.com/reference/android/media/MediaCodec)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

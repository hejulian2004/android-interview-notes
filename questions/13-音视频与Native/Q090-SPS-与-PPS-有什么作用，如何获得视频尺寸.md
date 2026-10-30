---
id: Q090
title: "SPS 与 PPS 有什么作用，如何获得视频尺寸"
category: "13-音视频与Native"
kind: observed
priority: P2
updated_at: "2026-10-30"
---

# Q090 · SPS 与 PPS 有什么作用，如何获得视频尺寸

类别：13-音视频与Native　｜　方向：应用开发　｜　学习优先级：P2（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S023 · 保伦电子

提问线索：二面：SPS/PPS 与编码尺寸。

面试日期：2026-09-23；帖子显示：09-23（页面省略年份）。
日期依据：**面试日期明确**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/discuss/932243541143670784?sourceSSR=%E5%85%B6%E4%BB%96) · [来源档案与限制](../../sources/S023.md)

## 参考回答提纲

参数集提供解码所需的序列、图像级配置；解析时要识别 NAL 封装格式并处理转义。尺寸可能由宏块信息、帧结构与裁剪共同决定，优先使用可靠解析库或解码器输出格式。

## 易错点

不能在字节流中硬取固定偏移当作宽高；Annex B 与长度前缀格式也不能混读。

## 延伸追问（整理者设计，不是原帖原题）

分辨率切换后，接收端如何更新解码器与显示布局？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [RFC 6184：H264 RTP 载荷与参数集](https://www.rfc-editor.org/rfc/rfc6184.html)（网页入口已核查）
- [MediaCodec API](https://developer.android.com/reference/android/media/MediaCodec)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

---
id: Q074
title: "内存泄漏与 OOM 是什么关系"
category: "11-性能与稳定性"
kind: observed
priority: P0
updated_at: "2026-10-30"
---

# Q074 · 内存泄漏与 OOM 是什么关系

类别：11-性能与稳定性　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S008 · 美团

提问线索：内存泄漏与检测。

面试日期：未明确；帖子显示：2025-02-17（已编辑）。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/592247f523b64d45bb0dd5f28bdfaf56) · [来源档案与限制](../../sources/S008.md)

### S011 · 百度

提问线索：泄漏和 OOM。

面试日期：未明确；帖子显示：2025-04-08。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/6c2b6b3c15bc40e2b25fef6662c77988) · [来源档案与限制](../../sources/S011.md)

### S016 · 蔚来

提问线索：内存问题。

面试日期：未明确；帖子显示：2025-09-15。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/discuss/797066691023736832?sourceSSR=enterprise) · [来源档案与限制](../../sources/S016.md)

## 参考回答提纲

泄漏是对象已无业务用途却仍被引用；OOM 是分配不能满足的结果。泄漏可能最终导致 OOM，但单次过大分配、峰值和 native 资源也可能触发内存失败。先确认内存类别，再看保留路径与增长趋势。

## 易错点

没有 OOM 不代表没有泄漏，出现 OOM 也不能直接认定是 Activity 泄漏。

## 延伸追问（整理者设计，不是原帖原题）

重复打开关闭页面时，如何证明对象数量或保留内存持续增长？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [LeakCanary 基础](https://square.github.io/leakcanary/fundamentals/)（网页入口已核查）
- [ART 垃圾回收调试](https://source.android.com/docs/core/runtime/gc-debug)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

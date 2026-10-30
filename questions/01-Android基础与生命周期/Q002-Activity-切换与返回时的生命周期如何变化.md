---
id: Q002
title: "Activity 切换与返回时的生命周期如何变化"
category: "01-Android基础与生命周期"
kind: observed
priority: P0
updated_at: "2026-10-30"
---

# Q002 · Activity 切换与返回时的生命周期如何变化

类别：01-Android基础与生命周期　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S005 · 哔哩哔哩

提问线索：Activity A 到 B 再返回。

面试日期：2024-04-12；帖子显示：2024-04-25（已编辑）。
日期依据：**面试日期明确**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/10da7a46c08d42c99c1655cfee0c1b08?sourceSSR=subject) · [来源档案与限制](../../sources/S005.md)

### S008 · 美团

提问线索：一面：A、B 页面生命周期。

面试日期：未明确；帖子显示：2025-02-17（已编辑）。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/592247f523b64d45bb0dd5f28bdfaf56) · [来源档案与限制](../../sources/S008.md)

### S006 · 字节跳动

提问线索：透明 Activity 对生命周期的影响。

面试日期：2024-07-08；帖子显示：2024-07-08。
日期依据：**面试年份由上下文推定**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/ccc1fe43cdd341ce9317578eb8fa44e9) · [来源档案与限制](../../sources/S006.md)

## 参考回答提纲

先声明 B 是否全屏不透明以及 A 是否 finish。常见全屏跳转是 A 暂停，B 创建、启动、恢复，随后 A 停止；返回时 B 暂停、A 重启并恢复，B 停止并销毁。透明页面可能使 A 保持可见而不进入停止状态。实际以生命周期日志验证。

## 易错点

不要把所有弹窗、透明页面、分屏场景套用同一固定序列。

## 延伸追问（整理者设计，不是原帖原题）

系统回收后台进程后，再返回 A 与正常返回有什么差别？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [Activity 生命周期](https://developer.android.com/guide/components/activities/activity-lifecycle)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

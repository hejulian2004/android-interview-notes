---
id: Q003
title: "Activity 启动模式与 onNewIntent 如何配合"
category: "01-Android基础与生命周期"
kind: observed
priority: P0
updated_at: "2026-10-30"
---

# Q003 · Activity 启动模式与 onNewIntent 如何配合

类别：01-Android基础与生命周期　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S005 · 哔哩哔哩

提问线索：启动模式与 onNewIntent。

面试日期：2024-04-12；帖子显示：2024-04-25（已编辑）。
日期依据：**面试日期明确**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/10da7a46c08d42c99c1655cfee0c1b08?sourceSSR=subject) · [来源档案与限制](../../sources/S005.md)

### S006 · 字节跳动

提问线索：启动模式。

面试日期：2024-07-08；帖子显示：2024-07-08。
日期依据：**面试年份由上下文推定**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/ccc1fe43cdd341ce9317578eb8fa44e9) · [来源档案与限制](../../sources/S006.md)

### S010 · 京东

提问线索：一面：onNewIntent。

面试日期：未明确；帖子显示：2025-04-01。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/f87cbbe5bebd4949823a5a68dec04e52?sourceSSR=users) · [来源档案与限制](../../sources/S010.md)

## 参考回答提纲

从任务栈、目标实例是否存在、是否位于栈顶三个维度解释 standard、singleTop、singleTask、singleInstance。实例被复用时可能收到 onNewIntent，而不是再次 onCreate；需要审视 Intent flags、taskAffinity 和入口类型。较新平台还有 singleInstancePerTask，回答应注明版本。

## 易错点

onNewIntent 收到新 Intent 后，getIntent 不会自动替换成新对象；按业务需要调用 setIntent。

## 延伸追问（整理者设计，不是原帖原题）

通知连续点击两次怎样避免重复打开详情页？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [任务与返回栈](https://developer.android.com/guide/components/activities/tasks-and-back-stack)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

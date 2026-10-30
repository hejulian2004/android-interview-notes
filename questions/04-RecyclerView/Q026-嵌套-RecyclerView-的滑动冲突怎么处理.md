---
id: Q026
title: "嵌套 RecyclerView 的滑动冲突怎么处理"
category: "04-RecyclerView"
kind: observed
priority: P1
updated_at: "2026-10-30"
---

# Q026 · 嵌套 RecyclerView 的滑动冲突怎么处理

类别：04-RecyclerView　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S016 · 蔚来

提问线索：两个 RecyclerView 嵌套滑动。

面试日期：未明确；帖子显示：2025-09-15。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/discuss/797066691023736832?sourceSSR=enterprise) · [来源档案与限制](../../sources/S016.md)

## 参考回答提纲

先区分同方向或交叉方向、父子谁消费剩余距离，再检查测量约束、触摸拦截与嵌套滚动协议。能用单列表的多类型布局表达时可简化结构；保留嵌套时要分别测试拖动、fling 和边界交接。

## 易错点

统一禁用某个 nestedScrolling 开关并不是所有嵌套冲突的通用解法。

## 延伸追问（整理者设计，不是原帖原题）

同方向父子列表都能滚动时，怎样设计符合预期的优先级？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [RecyclerView API](https://developer.android.com/reference/androidx/recyclerview/widget/RecyclerView)（网页入口已核查）
- [ViewGroup 触摸分发](https://developer.android.com/develop/ui/views/touch-and-input/gestures/viewgroup)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

---
id: Q072
title: "Room 怎样表达一对多关系与联合查询"
category: "10-Jetpack架构与存储"
kind: observed
priority: P1
updated_at: "2026-10-30"
---

# Q072 · Room 怎样表达一对多关系与联合查询

类别：10-Jetpack架构与存储　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S009 · 快手

提问线索：一面和二面：Room 与表关系。

面试日期：2025-03-06 / 2025-03-10；帖子显示：2025-03-13（已编辑）。
日期依据：**面试年份由上下文推定**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/9b9f932f60a345afb0f20162a0374e50) · [来源档案与限制](../../sources/S009.md)

## 参考回答提纲

先设计实体、主键、外键和索引，再根据需求选择显式 JOIN 或关系查询。@Embedded 用于列结构映射，不自动建立独立表关系；多步读取关联数据时要考虑事务快照的一致性。

## 易错点

不要把 Room 当成任意对象图自动持久化的黑箱。

## 延伸追问（整理者设计，不是原帖原题）

分页查询订单与明细时，如何避免 N+1 查询或重复行？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [Room 关系建模](https://developer.android.com/training/data-storage/room/relationships)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

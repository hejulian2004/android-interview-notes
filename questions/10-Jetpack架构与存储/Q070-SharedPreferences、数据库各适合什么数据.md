---
id: Q070
title: "SharedPreferences、数据库各适合什么数据"
category: "10-Jetpack架构与存储"
kind: observed
priority: P1
updated_at: "2026-10-30"
---

# Q070 · SharedPreferences、数据库各适合什么数据

类别：10-Jetpack架构与存储　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S009 · 快手

提问线索：二面：偏好存储与数据库。

面试日期：2025-03-06 / 2025-03-10；帖子显示：2025-03-13（已编辑）。
日期依据：**面试年份由上下文推定**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/9b9f932f60a345afb0f20162a0374e50) · [来源档案与限制](../../sources/S009.md)

## 参考回答提纲

少量配置适合键值存储；需要查询、关系、一致更新与迁移的数据更适合数据库。还要根据一致性、数据量、多进程和损坏恢复要求评估 DataStore 等方案，而非仅比较 API 行数。

## 易错点

把一整份不断增长的业务列表编码为一个字符串，并不会因此获得数据库能力。

## 延伸追问（整理者设计，不是原帖原题）

用户切换账号时，怎样避免配置与业务缓存互相串用？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [SharedPreferences API](https://developer.android.com/reference/android/content/SharedPreferences)（网页入口已核查）
- [Room 关系建模](https://developer.android.com/training/data-storage/room/relationships)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

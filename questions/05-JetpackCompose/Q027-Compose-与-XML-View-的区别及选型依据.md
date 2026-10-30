---
id: Q027
title: "Compose 与 XML-View 的区别及选型依据"
category: "05-JetpackCompose"
kind: observed
priority: P0
updated_at: "2026-10-30"
---

# Q027 · Compose 与 XML-View 的区别及选型依据

类别：05-JetpackCompose　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S020 · 小米

提问线索：Kotlin 与 Compose。

面试日期：2026-10-22；帖子显示：10-23（页面省略年份，已编辑）。
日期依据：**面试年份由上下文推定**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/27424c8609eb43c9aee0b0cbb57584eb) · [来源档案与限制](../../sources/S020.md)

### S021 · 武汉精臣智慧标识科技

提问线索：客户端一面：Compose、XML、View 的选择。

面试日期：2026-09-21；帖子显示：09-21（页面省略年份）。
日期依据：**面试日期明确**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/3e696bd0719c4463acb77969c80f0fd4?sourceSSR=dynamic&weFlow=true) · [来源档案与限制](../../sources/S021.md)

## 参考回答提纲

Compose 通过状态描述 UI；传统 View 常通过对象方法更新属性。比较状态管理、布局绘制、工具链、已有组件复用和团队维护成本，而非只比较代码量。现有 View 可通过互操作嵌入 Compose，迁移可以按页面或控件逐步进行。

## 易错点

XML 只是布局描述方式；RecyclerView 可以不用 XML。Compose 也不能无条件保证比 View 快。

## 延伸追问（整理者设计，不是原帖原题）

既有复杂 Custom View，为什么不必为引入 Compose 立即重写？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [Compose 与 View 互操作](https://developer.android.com/develop/ui/compose/migrate/interoperability-apis)（网页入口已核查）
- [Compose 三个阶段](https://developer.android.com/develop/ui/compose/phases)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

---
id: Q043
title: "String 常量池与对象创建有什么区别"
category: "07-Java集合与JVM"
kind: observed
priority: P1
updated_at: "2026-10-30"
---

# Q043 · String 常量池与对象创建有什么区别

类别：07-Java集合与JVM　｜　方向：应用开发　｜　学习优先级：P1（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S005 · 哔哩哔哩

提问线索：String 常量池。

面试日期：2024-04-12；帖子显示：2024-04-25（已编辑）。
日期依据：**面试日期明确**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/10da7a46c08d42c99c1655cfee0c1b08?sourceSSR=subject) · [来源档案与限制](../../sources/S005.md)

### S017 · vivo

提问线索：String 相关问题。

面试日期：2025-09-23；帖子显示：2025-11-11。
日期依据：**面试年份由上下文推定**；访问状态：检索索引可见。

[原始面经](https://www.nowcoder.com/feed/main/detail/237d9f1418df4f0d9ceb7d542fbb09e4) · [来源档案与限制](../../sources/S017.md)

## 参考回答提纲

区分字面量、编译期常量拼接、运行期拼接和显式 new 的语义。intern 返回规范化代表；比较文本内容通常使用 equals。具体存储布局和优化方式应注明运行时版本。

## 易错点

不要仅凭一段字符串代码就断言所有版本都分配固定数量对象；常量折叠和优化会改变实现。

## 延伸追问（整理者设计，不是原帖原题）

变量参与拼接与纯字面量拼接，为什么引用比较结果可能不同？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [String API（Java 8）](https://docs.oracle.com/javase/8/docs/api/java/lang/String.html)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

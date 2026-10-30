---
id: Q049
title: "sleep 与 wait 的区别是什么"
category: "08-并发与线程安全"
kind: observed
priority: P0
updated_at: "2026-10-30"
---

# Q049 · sleep 与 wait 的区别是什么

类别：08-并发与线程安全　｜　方向：应用开发　｜　学习优先级：P0（编辑建议，不是统计频率）

## 公开面经证据

以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。

### S002 · 美团

提问线索：一面：sleep 和 wait。

面试日期：未明确；帖子显示：2023-11-02（已编辑）。
日期依据：**仅帖子日期**；访问状态：正文已读取。

[原始面经](https://www.nowcoder.com/feed/main/detail/6bce20c6f8f94b6397f13a4ac706dbbe) · [来源档案与限制](../../sources/S002.md)

## 参考回答提纲

sleep 暂停当前线程但不释放已持有的监视器；wait 必须在持有相应监视器时调用，并释放该监视器等待通知或超时。条件检查放在 while 中以处理竞争与虚假唤醒。

## 易错点

notify 不代表被唤醒线程马上得到锁，也不意味着条件一定成立。

## 延伸追问（整理者设计，不是原帖原题）

生产者消费者为什么不能用 if 检查条件后直接 wait？

## 技术参考与验证边界

整理者独立撰写的复习提纲；下列技术参考用于学习核查，不代表企业官方答案。

- [Object API（Java 8）](https://docs.oracle.com/javase/8/docs/api/java/lang/Object.html)（网页入口已核查）
- [JLS 17：线程与锁](https://docs.oracle.com/javase/specs/jls/se17/html/jls-17.html)（网页入口已核查）

复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。

[按类别复习](../../indexes/by-category.md) · [按公司查证](../../indexes/by-company.md) · [收录规则](../../METHODOLOGY.md)

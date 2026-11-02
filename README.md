# 中国大陆公司 Android 开发面经整理

检索截止：**2026-10-30**　｜　滚动窗口：**2023-10-30—2026-10-30**

**116 道有公开来源的归纳题 + 16 道明确标识的补充练习**，每题一个 Markdown，按 **16 类**组织。覆盖 **27 篇去重来源、20 家公司或招聘品牌**，另存 **2 篇日期待核候选**。

这是一批可追溯的检索样本，不是近三年全网穷尽结果、企业官方题库或招聘频率统计。主要样本来自牛客，补充 CSDN 及掘金同内容页面；跨平台重复文章合并计数。

## 开始阅读

[个人项目与实习面试问答手册（129 组问答）](docs/android-interview-handbook.md) · 基于个人项目与实习经历的准备材料，独立于下方公开来源题库。

源码导读：[Rust SDK 与跨语言边界](docs/sdk-source-deep-dive.md) · [QUIC 与可靠文件传输](docs/quic-source-deep-dive.md) · [AI 辅助代码接管练习册](docs/ai-code-takeover-workbook.md)。源码链接固定到核对版本，私有仓库链接需要访问权限。

建议顺序：先填写练习册的“贡献与理解程度模板” → 阅读 SDK 导读 → 阅读 QUIC 导读 → 回到练习册完成实践与验证；原 129 题手册作为概念参考。

核对边界：SDK 与 QUIC 导读基于提交 `5aba1d8` 的静态源码阅读，不代表已完成运行、安全或性能验证；通用回答需要更精确的实现边界时，请以对应源码导读为参考。

原生 Android：[FeedLine 与 Compose 源码学习指南](docs/feedline-android-deep-dive.md)。建议先读原手册 C01—C48 的概念，再对照本篇查看实现边界与练习。基于公开仓库 `testDemo` 的固定提交 `8aa963a945176f8d5903b0b706423fd95cc011ff` 静态核对，未编译 APK 或执行真机、性能测试；原手册保留，具体实现以本篇核对版本为准。

历史 Java/XML：[Word Crush Android XML 与 View 面试问答指南](docs/word-crush-android-xml-guide.md)。固定到历史提交 `2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d`；核对时最新 main 已是 Kotlin/Compose，不混用两个版本。先读事实表与三条调用链，再练习问答；AIDL、MVVM 等未在该历史版核实的内容仅作为扩展题。

Flutter 与 Dart：[52 道面试问答及 SSH Mobile 实践指南](docs/flutter-interview-guide.md)。先掌握 P0 语言、状态、生命周期、异步与性能问题，再结合固定提交 `5aba1d8` 的源码例子和 6 个练习；底层网络细节继续参考 SDK 与 QUIC 导读。项目核对为静态阅读，不代表已完成真机或性能验证，私有源码链接需要访问权限。

基础深化：[Java 与 ART（40 题）](docs/java-core-interview-guide.md) · [Kotlin 与协程（40 题）](docs/kotlin-coroutines-interview-guide.md) · [Android 平台机制（40 题）](docs/android-platform-interview-guide.md)。这 120 题为整理者设计的通用练习，独立于有公开面经来源的 Q 系列；不归属于任何公司的已证实面试记录，不进入来源题、公司或招聘频率统计。每题提供官方依据与版本边界，不代表个人项目经历或已经完成编译、真机及性能验证。

[按类别复习](indexes/by-category.md) · [按公司查证](indexes/by-company.md) · [按年份查看](indexes/by-year.md) · [来源总表](sources/README.md) · [建议学习顺序](indexes/study-order.md)

[只看面试时间明确的子集](indexes/strict-interview-window.md) · [补充练习](supplements/README.md) · [技术参考](references/README.md)

## 日期与真实性边界

| 日期依据 | 来源篇数 | 能证明什么 |
|---|---:|---|
| 面试日期明确 | 6 | 原帖直接写明面试年月日 |
| 面试年份明确 | 4 | 标题/正文明确面试年份，具体月日未知 |
| 面试年份由上下文推定 | 5 | 年份来自帖子年份、校招届别等上下文，仍有不确定性 |
| 仅帖子日期 | 12 | 只确认公开帖显示在窗口内，不能证明面试也在窗口内 |

作者自述未经企业或其他独立证据认证。检索索引可见、正文已读和仅公开预览三类证据分别标记。**S001 的窗口外一面未收录；S018、S025 因日期未核实，不进入正式题目。** 完整规则见 [收录方法](METHODOLOGY.md)。

## 每题结构

每份文档包含：题意归纳、公司和轮次线索、面试/帖子日期、访问范围、原文链接、独立编写的参考回答提纲、易错点、编辑性延伸追问、技术参考。

回答不是面试官标准答案，也没有声称逐题编译或完成真机测试。算法部分提供解法和复杂度推导，不冒充已运行的代码；P0/P1/P2 仅是复习建议。

## 目录

```text
questions/       # Q 系列：有来源的题目，一题一文档
supplements/     # E 系列：补充练习，无公司真题归属
sources/         # 每篇面经的证据档案、日期和访问限制
indexes/         # 类别、公司、年份和学习顺序索引
references/      # 官方文档、源码和标准学习入口
data/            # 可维护的结构化题目与来源数据
scripts/         # 生成、校验、搜索和安全发布脚本
```

## 本地使用

Python 3.10 或更高版本，无第三方 Python 依赖。

```bash
python scripts/validate.py
python scripts/search.py RecyclerView
python scripts/search.py --company 腾讯
```

编辑 `data/questions.json` 或 `data/sources.json` 后，运行：

```bash
python scripts/build.py
python scripts/validate.py
```

Markdown 由数据生成；直接编辑生成文件可能在下次生成时被覆盖。新增规范见 [贡献指南](CONTRIBUTING.md)。

`docs/` 中的专题指南为人工维护的独立资料，不由上述 Q/E 数据生成。修改时保留已有文档路径、题号和显式锚点，新增题沿用原编号格式，避免重新排序编号导致收藏与学习进度失配。

## GitHub 仓库与后续更新

仓库：[hejulian2004/android-interview-notes](https://github.com/hejulian2004/android-interview-notes)。由仓库所有者创建，公开可见。

克隆后可按上文命令校验、搜索和生成文档。更新题库时，先修改结构化数据、重新生成并通过校验，再正常提交；不要强制覆盖远端历史。

`scripts/publish.py` 仅用于**新建另一个仓库**，默认 private，并拒绝覆盖已有同名仓库。不要把它当作本仓库的日常更新命令。[维护与发布说明](PUBLISH.md)。

## 手机复习网站

网站：[安卓复习室](https://txy.hejulian.org/android-study/)。支持专题、全文搜索、先答后看、收藏和掌握程度；题目与完整导读按 GitHub 资料更新，保留各题库独立来源与事实边界，实际内容数量以网站载入的版本为准。

网站源码、维护和部署说明位于 [web/](web/README.md)。题库仍维护在原来的 `docs/`、`questions/` 和 `supplements/`；浏览器打开时按 30 分钟缓存期限检查 GitHub main，也可手动更新。更新失败保留成功缓存或带日期的快照。学习进度只保存在当前浏览器，可导入导出，不跨设备同步。

## 内容与权利

不收录付费墙后的隐藏内容，不转载整篇面经，不把推荐文章日期当面试日期。外部原文与公开署名保留在来源档案中，详见 [引用与权利说明](NOTICE.md)。

来源与答案都可能存在遗漏或版本偏差；发现问题请附原文位置与目标 SDK/依赖版本进行修订。

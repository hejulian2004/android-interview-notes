# Android 复习台

手机优先的中文安卓面试复习网站，正式题库内容来自 [hejulian2004/android-interview-notes](https://github.com/hejulian2004/android-interview-notes)。项目位置约定为 txy 登录用户的 `~/coding/android-study-site/`。

> [线上复习室](https://txy.hejulian.org/android-study/)现已启用登录。学习记录仍保存在当前浏览器；维护界面或认证代码时，应验证后端与前端的配套版本。

## 使用与维护

- 保留专题浏览、全文搜索、先答后看、上一题/下一题/随机、收藏、掌握程度和待复习。
- 单管理员登录后，题库读取/刷新、手动编辑、源码查询和 AI 请求全部走同源受认证后端；浏览器不直接请求 GitHub 或模型供应商。
- 手动增改删支持本机草稿、Markdown 编辑、diff 与删除确认；点击“保存到 GitHub”直接提交。Agent 只能提出修改，用户检查差异并确认后才提交。
- GitHub 是正式内容唯一来源，服务器检查 main、按不可变版本读取并缓存完整题库；GitHub 失败保留成功缓存且明确显示警告，不能使用陈旧缓存写回。新公开 dist 不含旧题库快照。
- 内容支持 `docs/**/*.md` 中 `### N01 标题` 形式的编号题，以及 `questions/**/Q001-标题.md`、`supplements/**/E001-标题.md`。目录链接和代码围栏内的标题不计题；源码导读保持阅读资料形式。编辑器分别处理手维护文档与规范数据生成文档，保留编号/路径及证据边界。
- 收藏、掌握程度和最后位置仍在当前浏览器 localStorage，**不跨设备同步**。登录只控制后台访问，不自动上传学习进度。支持进度导入/导出，删除题目留下可恢复的孤立进度。
- 模型未配置时 AI 禁用，手动编辑仍可使用。key 不返回页面或写入浏览器存储；模型设置仅进程内保存。源码默认只注册公开题库仓库，可按服务器明确授权注册三个项目；未配置不会读取私有项目。外发资料每次需要明确授权并绑定展示的供应商配置版本。

认证、编辑冲突、生成数据一致性、Agent 安全边界和限制见 [后端说明](server/README.md)。生产账号、密钥、持久访问与服务变更需要单独批准，见 [新版部署准备](server/DEPLOYMENT.md)。

## Markdown 内容组件

答案、来源说明与完整导读均通过 `src/markdown.mjs` 渲染，使用 **Marked 18.1.2 + DOMPurify 3.4.17 + Highlight.js 11.12.0**。这是一套适合现有静态站的成熟 Markdown 渲染管线，无需引入新前端框架或服务器运行时。

支持 GFM 标题、粗体/强调/删除线、嵌套列表、表格、引用、链接、分隔线与围栏代码块。代码显示语言标签并高亮 Kotlin、Java、Dart、Rust、XML/HTML、Bash、JSON、JavaScript、TypeScript、SQL、YAML、C、C++；未标明或未知语言显示纯文本，不自动猜测语言、不执行代码。超过 100KB 的单个代码块保持纯文本，避免高亮阻塞。

代码和表格的横向滚动限制在组件内部。原始 HTML 作为文字显示；只将原笔记中的独立空 `<a id="...栏位"></a>` 标记转换成无行为的锚点，其他标签和事件属性不被放行。资料图片保留替代文字，不自动加载远程图片。

目录和题号锚点在当前内容中跳转；已加载导读的相对 Markdown 链接可站内打开，链接 URL 保留可直接打开的阅读路由。未纳入本站的来源档案、代码链接继续打开原文，并带安全外链属性。原文排版仍遵循 Markdown 语法；不会重写题库文字或将代码示例当作 HTML。

高亮资源来自官方 `@highlightjs/cdn-assets` 的浏览器 ESM 发行包，随源码自托管，不请求第三方 CDN。jsdom 只用于开发期安全与 DOM 回归测试，不随公开站点运行。测试：`npm test`（先 `npm ci --ignore-scripts`）；生产构建只需 `node scripts/build.mjs`。

中文标点兼容：CommonMark 会把部分 `**面试回答：**正文` 当作普通文字。组件只在 Marked 行内词法阶段识别包含汉字、以标点结束、与后续文字紧邻的有界双星号内容，并生成标准 strong token；不对原文全局替换或删除星号。围栏代码、行内代码、转义星号、乘法和通配符保留。该兼容也适用于缓存与打包快照；编辑新文档时推荐规范写法 `**面试回答：** 正文`。参见 [CommonMark 强调边界](https://spec.commonmark.org/0.31.2/#emphasis-and-strong-emphasis)。

## 源码、本地检查与构建

`src/` 是界面，`engine/parser.mjs` 是纯内容解析器，`server/` 是 Python 3.10+ 标准库后端，`scripts/` 是构建工具。Markdown 依赖固定版本并随源码自托管。`engine/index.mjs` 和旧快照只保留用于迁移回归，不随新公开构建分发。

```bash
python3 -m unittest discover -s web/server -t . -p 'tests_*.py'
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/build.py --check
python3 scripts/validate.py
cd web
npm ci --ignore-scripts
npm test
npm run build
```

前后端本地测试注入模拟 GitHub 和模型供应商，不使用生产凭据或真实写入。`dist/` 仅为公开静态资源，不能把服务器代码、Git checkout、配置、.env 或凭据目录作为 Web 根。新版本实际预览需显式配置的 loopback 后端，单独的静态开发服务器不能代替登录与 API。

仅更新已发布 GitHub 题库仍无需重新部署 UI；修改生成器、认证或前端代码需要先验证并部署一致版本。[原部署记录](DEPLOYMENT.md) 与 [验证记录](VALIDATION.md) 保留历史上线和回滚依据，新认证版本须遵循新增后端部署准备，不自动改变线上服务。

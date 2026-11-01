# Android 复习台

手机优先的静态面试复习网站，唯一内容来源为公开仓库 [hejulian2004/android-interview-notes](https://github.com/hejulian2004/android-interview-notes)。源码应存放在 txy 登录用户的 `~/coding/android-study-site/`，与其他项目隔离。

## 使用与资料更新

- 按专题浏览、全文搜索、先答后看、上一题/下一题/随机、收藏与掌握程度、待复习列表。
- 题库每次打开时按 30 分钟缓存期限检查 GitHub main；“刷新题库”立即检查。相同提交只检查一次版本，变更后只下载变更的兼容 Markdown。没有 token、服务器定时任务或私有仓库读取。
- 支持 `docs/**/*.md` 中形如 `### N01 标题` 的编号题；`questions/**/Q001-标题.md` 和 `supplements/**/E001-标题.md` 为一题一文档。目录链接不计题。SDK、QUIC 源码导读及 AI 接管练习册以阅读资料呈现。新格式需同步调整解析器。
- GitHub 不可用、限流或解析失败时保留上次成功题库；首次访问使用标明版本日期的打包快照。站点本身仍需要从服务器载入，不承诺完整离线应用。
- 收藏、学习状态和最后位置保存在当前浏览器 localStorage，**不跨设备/浏览器同步**。可导出 JSON 备份并在另一设备导入；删除题目的进度保留为暂不可用记录，题目恢复后可继续使用。
- Markdown 原始 HTML 不执行，内容通过 DOMPurify 清洗；外链只允许 HTTP(S)，新窗口带 `noopener noreferrer`；不加载资料中的远程图片。
- 保留笔记事实边界、源码版本和“通用原理/实际实现/待确认”说明。网站并不证明项目已运行或完成真机、性能测试。

## 源码与本地构建

`src/` 是界面，`engine/` 是内容解析、GitHub 更新和快照，`scripts/` 是构建和静态服务工具。`src/vendor/` 已包含固定版本的 marked 和 DOMPurify，以及相应许可，服务器无需 npm 安装或 Node 运行时。

维护界面后运行：

```bash
npm ci --ignore-scripts
node scripts/build.mjs
python3 scripts/serve.py --host 127.0.0.1 --port 8182
```

日常**只更新 GitHub 题库**无需重建网站。若需要更换打包回退快照，先将公开资料仓库克隆到 `content/`，再按 `engine/README.md` 操作。`dist/` 是唯一需要公开的静态目录，不能把项目根目录、原始 Git 目录或服务器其他文件作为 Web 根目录。

部署/回滚和验证记录见 `DEPLOYMENT.md`、`VALIDATION.md`。部署前必须遵守现有在线服务不变的约束；已有 Web 服务配置调整或新增公网端口须先获得用户确认。

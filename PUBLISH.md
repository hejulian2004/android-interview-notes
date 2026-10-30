# GitHub 维护与发布说明

## 当前仓库

正式仓库：[hejulian2004/android-interview-notes](https://github.com/hejulian2004/android-interview-notes)。仓库由所有者创建，公开可见；本批内容按所有者要求导入。检索快照仍为 2026-10-30，发布不代表重新核查了所有外链。

## 克隆与本地检查

需要 Python 3.10+ 和 Git。Windows 中可把 `python` 替换为 `py -3`。

```bash
git clone https://github.com/hejulian2004/android-interview-notes.git
cd android-interview-notes
python scripts/validate.py
python -m unittest discover -s tests -v
```

## 更新已有题库

编辑 `data/questions.json`、`data/sources.json` 或 `data/references.json`。生成文件不宜直接编辑，README 的模板位于 `scripts/build.py`。

```bash
git pull --ff-only
# 编辑结构化数据或维护脚本后执行：
python scripts/build.py
python scripts/validate.py
python -m unittest discover -s tests -v
git status
git diff
# 检查无误后，仅暂存本次修改的预期文件，再提交和推送：
git add data questions supplements sources indexes references README.md scripts
# 有其他确实需要提交的文件时，按实际改动明确添加。
git commit -m "docs: update Android interview notes"
git push origin main
```

如果 `git pull --ff-only` 失败，先检查分支和提交历史再合并；不要 force push。对已有仓库的日常维护不需要运行 `scripts/publish.py`。

## 发布到另一个新仓库（可选）

`scripts/publish.py` 是先前整理包附带的**新建仓库**辅助脚本。默认私有、核对 GitHub 登录账号、拒绝覆盖同名仓库，不支持更新已有仓库。请在没有 Git 历史和 remote 的独立副本中使用，并选一个尚不存在的名字。

安装 GitHub CLI 后：

```bash
gh auth login
python scripts/publish.py --repo hejulian2004/android-interview-study --dry-run
python scripts/publish.py --repo hejulian2004/android-interview-study
```

只有明确需要公开另一个新仓库时才附加 `--public`。不要把 Token 放进聊天、代码、提交或仓库。新建成功但推送失败时，先核对 `git remote -v`、`git status` 和远端历史，再普通推送，不要删除重建或强推。

## 验证边界

内容校验检查结构化数据、题目归属、生成一致性和本地链接；工具测试覆盖 9 项行为。这些检查不证明所有外部文章持续可访问，也不等于每道技术答案都已编译或完成真机测试。

新建仓库辅助脚本的 GitHub CLI 创建路径没有在本次导入中执行；不要将本次仓库导入成功理解为该脚本所有联网分支都已验证。

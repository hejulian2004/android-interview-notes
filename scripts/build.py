#!/usr/bin/env python3
"""从 data/*.json 生成 Markdown；--check 仅检查，不写文件。Python 3.10+。"""
from __future__ import annotations
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
TODAY = '2026-10-30'

def read_data(root: Path = ROOT):
    return tuple(json.loads((root/'data'/f'{n}.json').read_text(encoding='utf-8'))
                 for n in ('sources', 'questions', 'references'))

def slug(value: str) -> str:
    value = re.sub(r'[\\/:*?"<>|#\[\]()]', '-', value)
    return re.sub(r'\s+', '-', value).strip(' .-')

def question_path(q: dict) -> str:
    directory = 'questions' if q['kind'] == 'observed' else 'supplements'
    # An explicitly persisted source path keeps browser progress IDs stable when
    # an editor changes a title. Never permit this metadata to escape the bank.
    source_path = q.get('source_path')
    if source_path is not None:
        prefix = 'Q' if q['kind'] == 'observed' else 'E'
        if (not isinstance(source_path, str) or '\\' in source_path
                or '..' in source_path.split('/')
                or not re.fullmatch(rf'{directory}/[^/]+/{re.escape(q["id"])}-[^/]+\.md', source_path)
                or not re.fullmatch(rf'{prefix}\d+', q['id'])):
            raise ValueError('Invalid stable source_path for question')
        return source_path
    return f"{directory}/{q['category']}/{q['id']}-{slug(q['title'])}.md"

def link(from_path: str, to_path: str, label: str) -> str:
    rel = os.path.relpath(to_path, str(Path(from_path).parent)).replace(os.sep, '/')
    return f'[{label}]({rel})'

def collect_files(root: Path = ROOT) -> tuple[dict[str, str], dict]:
    sources, questions, refs = read_data(root)
    smap = {s['id']: s for s in sources}
    admitted = [s for s in sources if s['status'] == 'admitted']
    main = [q for q in questions if q['kind'] == 'observed']
    extra = [q for q in questions if q['kind'] == 'supplement']
    companies = sorted({s['company'] for s in admitted})
    categories = sorted({q['category'] for q in questions})
    source_q = {s['id']: [q for q in main if any(e['source_id'] == s['id'] for e in q['evidence'])] for s in sources}
    stats = dict(as_of=TODAY,window_start='2023-10-30',window_end=TODAY,
                 observed_questions=len(main),supplement_questions=len(extra),
                 admitted_sources=len(admitted),pending_sources=len(sources)-len(admitted),
                 companies=len(companies),categories=len(categories),
                 date_basis=dict(Counter(s['date_basis'] for s in admitted)),
                 access=dict(Counter(s['access'] for s in admitted)),
                 technical_references=len(refs))
    out = {}
    def put(path, text): out[path] = text.rstrip()+'\n'
    def qrows(path, qs):
        rows=['| 题号 | 题目 | 学习优先级 | 类型 |','|---|---|---|---|']
        for q in qs:
            rows.append(f"| {q['id']} | {link(path,question_path(q),q['title'])} | {q['priority']} | {'来源题' if q['kind']=='observed' else '补充练习'} |")
        return '\n'.join(rows)
    for q in questions:
        p=question_path(q)
        companies_q=sorted({smap[e['source_id']]['company'] for e in q['evidence']})
        lines=['---',f'id: {q["id"]}',f'title: {json.dumps(q["title"],ensure_ascii=False)}',
               f'category: {json.dumps(q["category"],ensure_ascii=False)}',f'kind: {q["kind"]}',
               f'priority: {q["priority"]}',f'updated_at: "{TODAY}"','---','',
               f'# {q["id"]} · {q["title"]}','',
               f"类别：{q['category']}　｜　方向：{q['scope']}　｜　学习优先级：{q['priority']}（编辑建议，不是统计频率）",'']
        if q['kind']=='observed':
            lines += ['## 公开面经证据','',
                '以下为题意归纳，不是逐字引语。各来源只证明其对应变体；作者自述未经独立核验。','']
            for e in q['evidence']:
                s=smap[e['source_id']]
                lines += [f"### {s['id']} · {s['company']}",'',
                    f"提问线索：{e['observed_variant']}。",'',
                    f"面试日期：{s['interview_date'] or '未明确'}；帖子显示：{s['displayed_date']}。",
                    f"日期依据：**{s['date_basis']}**；访问状态：{s['access']}。",'',
                    f"[原始面经]({s['url']}) · {link(p,'sources/'+s['id']+'.md','来源档案与限制')}",'']
        else:
            lines += ['## 题目性质','', '**补充练习，不计入来源题数量，也不归属于任何公司的确定面试记录。** 本题用于补齐复习主题，不能写成“某公司近三年问过”。','']
        lines += ['## 参考回答提纲','',q['answer'],'','## 易错点','',q['pitfall'],'',
                  '## 延伸追问（整理者设计，不是原帖原题）','',q['followup'],'',
                  '## 技术参考与验证边界','',q['answer_provenance'],'']
        for k in q['references']:
            r=refs[k]
            checked='网页入口已核查' if r['access_checked'] else '本次未成功核查页面，仅保留学习入口'
            lines += [f"- [{r['title']}]({r['url']})（{checked}）"]
        lines += ['', '复习时需结合目标 Android API、AndroidX、Kotlin、JDK 或协议版本。本文是回答提纲，不是企业标准答案，也不是已完成的性能实验。','',
                  link(p,'indexes/by-category.md','按类别复习')+' · '+link(p,'indexes/by-company.md','按公司查证')+' · '+link(p,'METHODOLOGY.md','收录规则')]
        put(p,'\n'.join(lines))
    for s in sources:
        p=f"sources/{s['id']}.md"
        lines=[f"# {s['id']} · {s['title']}",'',
               f"公司或招聘品牌：{s['company']}　｜　平台：{s['platform']}　｜　检索日期：{TODAY}",'',
               f"状态：**{'正式来源记录' if s['status']=='admitted' else '待核实候选，不进入题库统计'}**",'',
               f"[原始页面]({s['url']})",'',
               '## 日期与证据','',f"- 面试日期或年份：{s['interview_date'] or '原帖未明确'}",
               f"- 帖子显示日期：{s['displayed_date']}",f"- 日期依据：{s['date_basis']}",
               f"- 阅读范围：{s['access']}",f"- 作者署名：{s['author'] or '本轮未稳定核取，保留原页面署名'}",'',
               f"真实性边界：{s['authenticity']}。",'',
               '## 收录限制','',s['notes'] or '不把发帖时间直接当作面试发生时间；未转录原文全文或评论。','']
        if s.get('metadata_url'): lines += [f"[作者专栏日期核对入口]({s['metadata_url']})",'']
        if s.get('copyright_note'): lines += [s['copyright_note'],'']
        if s['mirrors']:
            lines += ['## 同内容页面（合并去重，不新增面经数量）','']+[f'- [镜像或同内容页面]({u})' for u in s['mirrors']]+['']
        lines += ['## 本来源对应的去重题','']
        lines += [qrows(p,source_q[s['id']])] if source_q[s['id']] else ['暂无正式题目；等待补充日期或正文证据。']
        lines += ['',link(p,'sources/README.md','返回来源总表')]
        put(p,'\n'.join(lines))
    p='sources/README.md'
    lines=['# 来源总表','',f"正式记录 {len(admitted)} 篇；日期待核 {len(sources)-len(admitted)} 篇。同内容跨站页面不重复计数。",'',
           '“来源存在”不等于企业确认题目，也不等于已确认面试年月日。仅检索索引可见的记录有单独标签。','',
           '| ID | 公司 | 面试日期/年份 | 帖子显示日期 | 日期依据 | 阅读范围 | 题数 |','|---|---|---|---|---|---|---|']
    for s in admitted:
        lines.append(f"| {link(p,'sources/'+s['id']+'.md',s['id'])} | {s['company']} | {s['interview_date'] or '未明确'} | {s['displayed_date']} | {s['date_basis']} | {s['access']} | {len(source_q[s['id']])} |")
    lines += ['', '## 待核实候选','']
    for s in sources:
        if s['status']=='pending': lines += [f"- {link(p,'sources/'+s['id']+'.md',s['title'])}：{s['notes']}"]
    put(p,'\n'.join(lines))
    p='indexes/by-category.md'
    lines=['# 按知识类别复习','', 'Q 为有公开面经来源的归纳题；E 为无公司归属的补充练习。P0/P1/P2 是编辑学习建议，不是实际提问频率。','']
    for cat in categories:
        qs=[q for q in questions if q['category']==cat]
        lines += [f'## {cat}', '', qrows(p,qs),'']
        for base in ('questions','supplements'):
            group=[q for q in qs if question_path(q).startswith(base+'/')]
            if group:
                cp=f'{base}/{cat}/README.md'
                put(cp,f'# {cat}\n\n'+qrows(cp,group)+'\n\n'+link(cp,p,'返回类别总索引'))
    put(p,'\n'.join(lines))
    p='indexes/by-company.md'
    lines=['# 按公司与招聘品牌查证','', '用于按来源复习，不是公司题库或提问概率排名。阿里钉钉与夸克归在阿里巴巴；蚂蚁集团单列。','',
           '| 公司/招聘品牌 | 来源篇数 | 去重题数 | 入口 |','|---|---|---|---|']
    for company in companies:
        ss=[s for s in admitted if s['company']==company]
        sids={s['id'] for s in ss}
        qs=[q for q in main if any(e['source_id'] in sids for e in q['evidence'])]
        cp=f'indexes/companies/{slug(company)}.md'
        lines += [f"| {company} | {len(ss)} | {len(qs)} | {link(p,cp,'查看')} |"]
        body=[f'# {company}','', '这是一组公开记录的索引，不代表该公司的完整或固定面试要求。','', '## 来源','']
        for s in ss:
            body += [f"- {link(cp,'sources/'+s['id']+'.md',s['id']+' · '+s['title'])}：{s['date_basis']}；{s['interview_date'] or s['displayed_date']}"]
        body += ['', '## 归纳题','',qrows(cp,qs),'',link(cp,p,'返回公司索引')]
        put(cp,'\n'.join(body))
    put(p,'\n'.join(lines))
    p='indexes/by-year.md'
    lines=['# 按年份与日期依据查看','', '**不要把下表所有年份解读为面试发生年份。** 每年分为面试时间明确、上下文推定、仅帖子日期三组。窗口为 2023-10-30 至 2026-10-30；两端年份不是全年。','']
    for year in (2023,2024,2025,2026):
        lines += [f'## {year}','']
        for group,bases in [('面试日期或年份明确',{'面试日期明确','面试年份明确'}),('面试年份由上下文推定',{'面试年份由上下文推定'}),('仅帖子显示日期，面试日期不明',{'仅帖子日期'})]:
            ss=[s for s in admitted if s['index_year']==year and s['date_basis'] in bases]
            lines += [f'### {group}','']
            lines += [f"- {link(p,'sources/'+s['id']+'.md',s['id']+' · '+s['company'])}：面试 {s['interview_date'] or '未明确'}；帖子 {s['displayed_date']}" for s in ss] or ['本轮未收录。']
            lines += ['']
    put(p,'\n'.join(lines))
    p='indexes/strict-interview-window.md'
    strict={s['id'] for s in admitted if s['date_basis'] in {'面试日期明确','面试年份明确'}}
    strictq=[q for q in main if any(e['source_id'] in strict for e in q['evidence'])]
    put(p,'# 面试日期或年份明确的严格子集\n\n排除仅发帖日期及上下文推定年份的记录。年份明确的 2024 年记录整体落在窗口内；不将源帖真实性视为已独立认证。\n\n'+f'{len(strict)} 篇来源支持 {len(strictq)} 道去重题。\n\n'+qrows(p,strictq))
    p='indexes/study-order.md'
    lines=['# 建议复习顺序','', '先按 P0 建立基础，再选择目标岗位需要的 P1/P2。优先级是学习安排，不是招聘市场统计。','']
    for pri in ('P0','P1','P2'):
        lines += [f'## {pri}','',qrows(p,[q for q in questions if q['priority']==pri]),'']
    put(p,'\n'.join(lines))
    p='supplements/README.md'
    put(p,'# 补充练习（不冒充公司真题）\n\n此处题目用于补齐 RecyclerView、Compose 与协程知识；没有可靠的逐题公司来源，不进入来源题或公司统计。\n\n'+qrows(p,extra))
    p='references/README.md'
    lines=['# 技术学习参考','', '这些资料用于核查技术概念，不是面试发生的证据。API 文档持续更新，Java SE 实现细节不能无条件套用到 ART。未成功打开的入口明确标注。','',
           '| 键 | 资料 | 网页入口核查 |','|---|---|---|']
    for key,r in refs.items():
        lines += [f"| {key} | [{r['title']}]({r['url']}) | {r['access_checked'] or '未成功直读'} |"]
    put(p,'\n'.join(lines))
    p='README.md'
    put(p,f'''# 中国大陆公司 Android 开发面经整理

检索截止：**{TODAY}**　｜　滚动窗口：**2023-10-30—2026-10-30**

**{len(main)} 道有公开来源的归纳题 + {len(extra)} 道明确标识的补充练习**，每题一个 Markdown，按 **{len(categories)} 类**组织。覆盖 **{len(admitted)} 篇去重来源、{len(companies)} 家公司或招聘品牌**，另存 **{len(sources)-len(admitted)} 篇日期待核候选**。

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
| 面试日期明确 | {stats['date_basis'].get('面试日期明确',0)} | 原帖直接写明面试年月日 |
| 面试年份明确 | {stats['date_basis'].get('面试年份明确',0)} | 标题/正文明确面试年份，具体月日未知 |
| 面试年份由上下文推定 | {stats['date_basis'].get('面试年份由上下文推定',0)} | 年份来自帖子年份、校招届别等上下文，仍有不确定性 |
| 仅帖子日期 | {stats['date_basis'].get('仅帖子日期',0)} | 只确认公开帖显示在窗口内，不能证明面试也在窗口内 |

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
''')
    put('data/stats.json',json.dumps(stats,ensure_ascii=False,indent=2))
    manifest=sorted(out)
    put('data/generated-files.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    return out,stats

def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check',action='store_true')
    args=ap.parse_args()
    out,stats=collect_files()
    changes=[]
    for path,content in out.items():
        dst=ROOT/path
        if not dst.exists() or dst.read_text(encoding='utf-8')!=content:
            changes.append(path)
            if not args.check:
                dst.parent.mkdir(parents=True,exist_ok=True)
                dst.write_text(content,encoding='utf-8',newline='\n')
    old_manifest=ROOT/'data/generated-files.json'
    # 不删除用户文件；孤立题目由 validator 报告后人工处理。
    print(json.dumps(stats,ensure_ascii=False,indent=2))
    print(('待更新' if args.check else '已更新')+f' {len(changes)} 个生成文件')
    if args.check and changes:
        print('\n'.join(changes[:20]))
        return 1
    return 0
if __name__=='__main__':
    sys.exit(main())

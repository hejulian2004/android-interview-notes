#!/usr/bin/env python3
"""离线校验数据、归属、生成一致性和站内链接；不声称外部链接持续有效。"""
from __future__ import annotations
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit
from build import ROOT, read_data, collect_files, question_path

def validate_data(sources: list, questions: list, refs: dict) -> list[str]:
    errors=[]
    smap={s['id']:s for s in sources}
    if len(smap)!=len(sources): errors.append('来源 ID 重复')
    ids=[q['id'] for q in questions]
    if len(ids)!=len(set(ids)): errors.append('题目 ID 重复')
    names=[question_path(q).casefold() for q in questions]
    if len(names)!=len(set(names)): errors.append('题目路径冲突')
    used=set()
    for q in questions:
        if not all(q.get(k) for k in ('title','category','answer','pitfall','followup')):
            errors.append(q['id']+': 必要内容为空')
        if q['kind']=='observed' and not q['evidence']: errors.append(q['id']+': 来源题缺少来源')
        if q['kind']=='supplement' and q['evidence']: errors.append(q['id']+': 补充题不得归属公司')
        if q['priority'] not in {'P0','P1','P2'}: errors.append(q['id']+': 优先级非法')
        seen=set()
        for e in q['evidence']:
            sid=e['source_id'];used.add(sid)
            if sid in seen: errors.append(q['id']+': 重复来源 '+sid)
            seen.add(sid)
            if sid not in smap: errors.append(q['id']+': 未知来源 '+sid)
            elif smap[sid]['status']!='admitted': errors.append(q['id']+': 使用了待核来源 '+sid)
            if not e.get('observed_variant'): errors.append(q['id']+': 缺少提问定位线索')
        for key in q['references']:
            if key not in refs: errors.append(q['id']+': 未知技术参考 '+key)
    for s in sources:
        if s['status']=='admitted' and s['id'] not in used: errors.append(s['id']+': 正式来源没有对应题目')
        if s['status']=='pending' and s['index_year'] is not None: errors.append(s['id']+': 候选不得进入年份统计')
        if s['date_basis']=='面试日期明确':
            date=s['interview_date']
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',date or '') or not ('2023-10-30'<=date<='2026-10-30'):
                errors.append(s['id']+': 明确面试日期不在窗口内或格式不符')
        if s['date_basis']=='仅帖子日期' and s['interview_date']:
            errors.append(s['id']+': 帖子日期被错误写成面试日期')
    return errors

def check_links(root: Path) -> list[str]:
    errors=[]
    pattern=re.compile(r'\[[^\]\n]+\]\(([^)\n]+)\)')
    for p in sorted(root.rglob('*.md')):
        if '.git' in p.parts: continue
        for raw in pattern.findall(p.read_text(encoding='utf-8')):
            dest=raw.strip().split(' "',1)[0]
            u=urlsplit(dest)
            if u.scheme or dest.startswith('#'): continue
            target=(p.parent/unquote(u.path)).resolve()
            try: target.relative_to(root.resolve())
            except ValueError:
                errors.append(f'{p.relative_to(root)}: 链接逃逸仓库 {dest}');continue
            if not target.exists(): errors.append(f'{p.relative_to(root)}: 本地链接不存在 {dest}')
    return errors

def validate(root: Path=ROOT) -> list[str]:
    sources,questions,refs=read_data(root)
    errors=validate_data(sources,questions,refs)
    expected,stats=collect_files(root)
    for path,content in expected.items():
        p=root/path
        if not p.is_file(): errors.append('缺少生成文件: '+path)
        elif p.read_text(encoding='utf-8')!=content: errors.append('生成文件与 data 不一致: '+path)
    expected_questions={question_path(q) for q in questions}
    actual={p.relative_to(root).as_posix() for base in ('questions','supplements') for p in (root/base).rglob('*.md') if p.name!='README.md'}
    if expected_questions!=actual: errors.append('磁盘题目与题目清单不一致')
    errors.extend(check_links(root))
    return errors

def main() -> int:
    try: errors=validate()
    except (ValueError,KeyError,OSError) as e:
        print(f'校验无法完成: {e}',file=sys.stderr);return 2
    if errors:
        print('\n'.join('ERROR '+e for e in errors),file=sys.stderr);return 1
    sources,questions,_=read_data()
    print(f'PASS: {len(questions)} 份题目文档、{len(sources)} 份来源档案；数据、归属、索引与本地链接一致。')
    print('边界：未在线重新请求全部外链，未逐题编译 Kotlin/Java，也未完成真机性能测量。')
    return 0
if __name__=='__main__': sys.exit(main())

#!/usr/bin/env python3
"""Build/check the user-submitted intake report independently of dated Q/S statistics."""
from __future__ import annotations
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import unicodedata
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = 'data/intakes/20261102.json'
REPORT = 'docs/interview-intake-coverage-20261102.md'


def slug(value):
    value = re.sub(r'[`*_]', '', value).lower()
    return ''.join(c for c in value if unicodedata.category(c)[0] in 'LMN' or c in ' _-').replace(' ', '-')


def anchors(text):
    found = set(re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)["\']', text))
    fence = None
    for line in text.splitlines():
        m = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if m:
            token = m[1]
            if fence is None:
                fence = (token[0], len(token))
            elif token[0] == fence[0] and len(token) >= fence[1]:
                fence = None
        elif fence is None:
            h = re.match(r'^#{1,6}\s+(.+?)\s*#*$', line)
            if h:
                found.add(slug(h[1]))
    return found


def validate(data):
    errors = []
    sources = data['sources']
    ids = {s['id'] for s in sources}
    if len(ids) != len(sources) or len(ids) != data['deduplicated_source_groups']:
        errors.append('来源组数量或ID不一致')
    if data['text_materials'] != 9 or data['physical_images'] != 13 or data['unique_images'] != 12:
        errors.append('输入素材基线不一致')
    if any(s['original_url'] is not None or s['interview_date'] is not None or s['post_date'] is not None for s in sources):
        errors.append('本批未知原帖/日期不可伪造为已核取')
    if sum(g['image_count'] for g in data['image_groups']) != data['physical_images']:
        errors.append('截图组数量不一致')
    if set(s['id'] for s in sources) != {x['source_id'] for x in data['items']}:
        errors.append('素材来源组未被完整映射')
    item_ids = set()
    targeted = set()
    for item in data['items']:
        if item['id'] in item_ids or item['source_id'] not in ids:
            errors.append('重复议题或未知来源：' + item['id'])
        item_ids.add(item['id'])
        if not item['topic'] or not item['targets'] or item['disposition'] not in {'新题深化', '扩充已有', '既有导航', '准备框架', '待澄清'}:
            errors.append('议题映射不完整：' + item['id'])
        for target in item['targets']:
            value = target['path']
            url = urlsplit(value)
            path = ROOT / unquote(url.path)
            if url.scheme or not path.resolve().is_relative_to(ROOT.resolve()) or not path.is_file():
                errors.append('目标不存在或越界：' + value)
                continue
            if url.fragment and unquote(url.fragment) not in anchors(path.read_text()):
                errors.append('目标锚点不存在：' + value)
            targeted.add(value)
    for guide in data['new_guides']:
        path = ROOT / guide['path']
        if not path.is_file():
            errors.append('新指南不存在：' + guide['path'])
            continue
        codes = re.findall(r'^### (' + guide['prefix'] + r'\d+)\s', path.read_text(), re.M)
        if len(codes) != guide['question_count'] or len(set(codes)) != len(codes):
            errors.append('新指南题号数量有误：' + guide['path'])
        for code in codes:
            if guide['path'] + '#' + code.lower() not in targeted:
                errors.append('新题没有素材或深化映射：' + code)
    return errors


def link(path, label):
    parts = urlsplit(path)
    target = os.path.relpath(parts.path, 'docs').replace(os.sep, '/')
    return f'[{label}]({target}' + ('#' + parts.fragment if parts.fragment else '') + ')'


def render(data):
    counts = Counter(x['disposition'] for x in data['items'])
    new_count = sum(g['question_count'] for g in data['new_guides'])
    lines = [
        '# 用户面经补充：收录、去重与逐项覆盖记录', '',
        '整理日期：2026-11-02。' + data['evidence_boundary'] + '。', '',
        f'本批新增 **{new_count} 道深化练习**，补充 **{len(data["enriched_ids"])} 道既有答案**，原491道题的路径与题号保留；网站解析后的总题数为 **{491 + new_count} 道**。数量是内容规模，不是招聘频率、命中率或真实公司原题数量。', '',
        '## 学习入口', '',
    ]
    for g in data['new_guides']:
        lines.append('- ' + link(g['path'], g['label']) + f'：{g["question_count"]}题。')
    lines += ['', '每道新题均有口述答案、原理边界、带答案的追问、易错点与官方/原始依据；算法另有Java示例、复杂度与边界验证。重复基础概念链接旧题，不再制造同义题。', '',
        '## 素材与统计边界', '',
        '- 九份文字面经和十三张截图均已检查题意。截图中一张与另一张完全相同，独立图片十二张。',
        '- 腾讯地图的文字与两张截图合为同一个来源组；字节生服的文字与两张截图也合为一组；两张相同截图合为一组。最终十五个来源组。连续多页截图作为同一篇线索，而非多份独立面经。',
        '- 原帖URL、可靠面试日期、发帖日期均未取得；公司/轮次只是用户所提供材料中的自述。百度图的2026/4/8、字节图的2025/7/24为笔记时间，小鹏的标签#24也不作为面试年份。',
        '- 小米截图来自面试服务类账号的二手整理，不是已认证亲历，不用于企业原题背书。字节MVVM文本带转载整理口吻，亦未独立认证。',
        '- 原有Q/S三年检索统计保持116道来源归纳题、27份正式来源、20家公司/招聘品牌；本批U编号只在本收录记录内使用，不作为已核S来源。',
        '- 未上传截图、账号水印或原帖全文。只保存题意归纳、原创参考答案和学习导航；编辑性追问不冒充原面试追问。', '',
        '## 准备框架', '',
        '自我介绍用约60秒说明真实教育背景、目标岗位、最熟悉项目、一个可验证的个人贡献。可到岗日期、每周天数和持续月数由本人填写，不从“研一”推定。反问聚焦业务、导师与技术栈、实习任务及工作安排。', '',
        '共享屏幕前准备“入口→状态/业务→数据/网络→结果回传”的调用链，能解释包职责、异常出口、资源释放和一个设计取舍。AI辅助代码按自己提出需求、核查、调试、修改与验证的真实参与边界说明；不把生成代码等同于独立设计底层协议。可继续练习' + link('docs/ai-code-takeover-workbook.md', 'AI代码接管练习册') + '。', '',
        '演示前在目标设备验证登录、接口和弱网失败；准备明确标识的可控测试数据或录屏作为补充，接口失效时展示错误处理与恢复过程，不把mock演示冒充真实服务端成功。', '',
        '秒杀、短链、新闻App、智能音量、机器人硬件、论文和原帖实习，均是分享者的背景。没有对应用户源码与事实时，只按“需求/约束→数据与状态→并发/失败→验证”练习设计。秒杀框架要说明库存扣减的一致性、幂等、限流、支付/取消及补偿；论文要由本人补题目、方法、贡献、实验和局限，不能代写个人经历。', '',
        '## 待澄清清单', '',
        '- “MVP模板代码是指”原文残缺，不能生成确定原答。',
        '- “ViewModel直接get值”未给代码：已有Q069只解释快照读取、订阅、线程和postValue时机，不宣称直接get一律错误。',
        '- “实习节假日三级数据源”未说明哪三级，不擅自回答成内存/磁盘/网络。',
        '- 论文题目、多线程应用题的条件、未知的原生路由插件名称均缺失；保留通用练习或核对框架，不还原未知题。',
        '- “C调用堆栈/Java调用更快或更慢”需先分清分配、访问与函数调用；“Flutter没有动态化能力”须先限定平台和运行模式。',
        '- iOS掌握程度、行业前景与业务路线属于能力边界或观点，不编项目和确定行业预测。', '',
        '## 覆盖口径', '',
        f'共 **{len(data["items"])} 条归纳议题记录**。一条可能合并原材料中连续的同一追问；多个来源的同一知识点仍各有映射，但不重复新建题目。', '',
        '| 处理方式 | 议题记录数 | 含义 |', '|---|---:|---|',
    ]
    meanings = {'新题深化':'指向至少一道本批深化题，必要时同时关联旧题', '扩充已有':'指向本批补充过的原有Q/E题', '既有导航':'现有内容已覆盖，保留学习路径', '准备框架':'个人事实、演示或观点准备，不虚构经历', '待澄清':'原材料缺必要上下文；可能另给通用练习'}
    for name, meaning in meanings.items():
        lines.append(f'| {name} | {counts[name]} | {meaning} |')
    lines += ['', '## 来源组总表', '', '| ID | 材料题名线索 | 输入 | 议题数 | 说明 |', '|---|---|---|---:|---|']
    for source in data['sources']:
        n = sum(x['source_id'] == source['id'] for x in data['items'])
        lines.append(f'| {source["id"]} | {source["label"]} | {"、".join(source["materials"])} | {n} | {source["note"] or "原帖URL、日期及真实性未核"} |')
    lines += ['', '## 每份材料的逐项学习映射', '']
    for source in data['sources']:
        lines += ['## ' + source['id'] + ' ' + source['label'], '', '| 议题ID | 归纳议题 | 处理 | 答案或准备入口 | 边界/缺失说明 |', '|---|---|---|---|---|']
        for item in (x for x in data['items'] if x['source_id'] == source['id']):
            links = '、'.join(link(t['path'], t['key']) for t in item['targets'])
            lines.append(f'| {item["id"]} | {item["topic"]} | {item["disposition"]} | {links} | {item["note"] or "—"} |')
        lines.append('')
    lines += ['## 校验与实际限制', '',
        '结构化题库已重新生成并检查数据、归属和本地链接；本批清单另检查252条议题目标文件与锚点、新题全部有映射、未知日期隔离。浏览器与服务端的实际解析器读取548个一致题目ID，原491个ID完整保留。', '',
        '算法在2026-11-02使用临时Temurin JDK 21.0.13+9编译，Python两项检查通过，Java输出 `PASS: 61162 algorithm checks`；代码与Markdown示例一致，包含随机/枚举对照和长链边界。四专题及既有答案增量经过独立静态技术复核。', '',
        '这不是Android APK构建、真机、抓包、音频/代理/硬件测试或线上性能测量，也未对原面试发生事实认证。官方页面与主分支源码会变，不能把OpenJDK细节无条件套到所有Android版本；少数官方入口访问失败已在对应题注明。', '',
        '复查命令（仓库根目录）：', '', '```bash',
        'python3 scripts/build.py --check', 'python3 scripts/validate.py',
        'python3 scripts/build_intake_report.py --check',
        "python3 -m unittest discover -s tests -p 'test_repository.py' -v",
        "python3 -m unittest discover -s tests -p 'test_interview_algorithms.py' -v", '```', '',
        '网站按现有服务器缓存读取GitHub更新；手动点“更新题库”即可请求更新。本次资料更新不要求重新部署，不更改服务器或其他在线服务。', '',
        '机器可读清单：' + link(MANIFEST, '20261102.json') + '；维护题号与路径，避免破坏收藏和学习进度。',
    ]
    return '\n'.join(lines).rstrip() + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = json.loads((ROOT / MANIFEST).read_text())
    content = render(data)
    if not args.check:
        (ROOT / REPORT).write_text(content)
    errors = validate(data)
    if not (ROOT / REPORT).is_file() or (ROOT / REPORT).read_text() != content:
        errors.append('覆盖报告与机器清单不一致')
    if errors:
        print('\n'.join('ERROR ' + e for e in errors))
        return 1
    print(f'PASS: {len(data["sources"])}来源组，{len(data["items"])}条议题映射，{sum(g["question_count"] for g in data["new_guides"])}道新题。')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

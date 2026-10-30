#!/usr/bin/env python3
"""离线搜索题目；不需要联网、依赖库或 GitHub Token。"""
import argparse
from build import read_data, question_path

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('query',nargs='?',default='')
    ap.add_argument('--company',default='')
    ap.add_argument('--priority',choices=['P0','P1','P2'])
    ap.add_argument('--kind',choices=['observed','supplement'])
    args=ap.parse_args()
    sources,questions,_=read_data()
    smap={s['id']:s for s in sources}
    count=0
    for q in questions:
        cs=sorted({smap[e['source_id']]['company'] for e in q['evidence']})
        hay=' '.join([q['title'],q['category'],q['answer'],q['pitfall'],' '.join(cs)]).casefold()
        if args.query.casefold() not in hay: continue
        if args.company and not any(args.company.casefold() in c.casefold() for c in cs): continue
        if args.priority and args.priority!=q['priority']: continue
        if args.kind and args.kind!=q['kind']: continue
        print(f"{q['id']} [{q['priority']}] {q['title']}\n  公司：{', '.join(cs) or '补充练习，无公司归属'}\n  {question_path(q)}")
        count+=1
    print(f'共 {count} 项')
if __name__=='__main__': main()

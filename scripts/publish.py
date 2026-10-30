#!/usr/bin/env python3
"""在用户本机通过 GitHub CLI 创建新仓库并上传；默认 private，无强制推送。"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from build import ROOT
from validate import validate

DEFAULT_REPO='hejulian2004/android-interview-notes'
ALLOWLIST=('README.md','METHODOLOGY.md','CONTRIBUTING.md','PUBLISH.md','NOTICE.md',
           'SEARCH_LOG.md','DELIVERY.md','.gitignore','.gitattributes',
           'data','questions','supplements','sources','indexes','references','scripts','tests','templates')

class PublishError(RuntimeError): pass

def run(args: list[str],check=True) -> subprocess.CompletedProcess:
    result=subprocess.run(args,cwd=ROOT,text=True,encoding='utf-8',errors='replace',
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180)
    if check and result.returncode:
        raise PublishError(f"命令失败：{' '.join(args)}\n{result.stderr.strip() or result.stdout.strip()}")
    return result

def parse_args(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo',default=DEFAULT_REPO,help='个人账号/新仓库名称')
    ap.add_argument('--public',action='store_true',help='显式改为公开；默认私有')
    ap.add_argument('--dry-run',action='store_true',help='只打印计划，不联网、不修改 Git')
    args=ap.parse_args(argv)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9][A-Za-z0-9._-]*',args.repo):
        ap.error('--repo 必须是 owner/new-repository，不能包含 URL 或命令参数')
    return args

def main(argv=None) -> int:
    args=parse_args(argv)
    errors=validate()
    if errors:
        print('请先修复内容校验：\n'+'\n'.join(errors),file=sys.stderr);return 1
    visibility='public' if args.public else 'private'
    print(f'目标：{args.repo}；可见性：{visibility}；目录：{ROOT}')
    if args.dry_run:
        print('DRY RUN：核对 gh 登录账号 → 检查当前目录没有其他仓库边界/远端 → 初始化 main')
        print('仅提交 ALLOWLIST 内文件 → gh repo create（名称已存在则失败，不覆盖）→ 普通 git push')
        print('不会创建远端、不会联网、不会读取或输出 Token。')
        return 0
    created=False
    try:
        for tool in ('git','gh'):
            if not shutil.which(tool): raise PublishError(f'缺少 {tool}；请按 PUBLISH.md 安装后重试。')
        run(['gh','auth','status','--hostname','github.com'])
        user=json.loads(run(['gh','api','user']).stdout)
        owner=args.repo.split('/')[0]
        if user['login'].casefold()!=owner.casefold():
            raise PublishError(f"当前账号为 {user['login']}，目标为 {owner}；请自行切换账号后重试。")
        top=run(['git','rev-parse','--show-toplevel'],check=False)
        if top.returncode==0:
            if Path(top.stdout.strip()).resolve()!=ROOT:
                raise PublishError('此目录位于其他 Git 仓库内，拒绝修改父仓库。请解压到独立目录。')
            if run(['git','remote']).stdout.strip():
                raise PublishError('此目录已有 Git remote；脚本拒绝修改远端。请按 PUBLISH.md 手工确认。')
            if run(['git','diff','--cached','--name-only']).stdout.strip():
                raise PublishError('当前仓库已有暂存改动；请先人工处理，脚本不会混入已有暂存内容。')
            branch=run(['git','symbolic-ref','--short','HEAD'],check=False)
            if branch.returncode or branch.stdout.strip()!='main':
                raise PublishError('现有仓库不是 main 分支；脚本不自动改写分支。')
        else:
            run(['git','init','-b','main'])
        paths=[p for p in ALLOWLIST if (ROOT/p).exists()]
        run(['git','add','--',*paths])
        has_changes=run(['git','diff','--cached','--quiet'],check=False)
        if has_changes.returncode not in (0,1): raise PublishError('无法检查暂存区状态。')
        if has_changes.returncode==1:
            noreply=f"{user['id']}+{user['login']}@users.noreply.github.com"
            run(['git','-c',f"user.name={user['login']}",'-c',f'user.email={noreply}',
                 'commit','-m','docs: add sourced Android interview notes (2023-2026)'])
        run(['git','rev-parse','--verify','HEAD'])
        # GitHub 的创建 API 在重名时失败；此处不做更新、删除或强制覆盖。
        run(['gh','repo','create',args.repo,'--'+visibility,'--description',
             '中国大陆公司 Android 面经：可追溯来源、一题一文档、按知识类别整理'])
        created=True
        url=f'https://github.com/{args.repo}.git'
        run(['git','remote','add','origin',url])
        # 临时使用 gh 作为凭证助手，不修改全局 Git 配置，不输出凭证。
        run(['git','-c','credential.helper=','-c','credential.helper=!gh auth git-credential',
             'push','-u','origin','main'])
        print(f'已创建并上传：https://github.com/{args.repo}')
        return 0
    except (PublishError,subprocess.TimeoutExpired,OSError,ValueError,KeyError) as e:
        print(str(e),file=sys.stderr)
        if created:
            print('远端已创建，但后续步骤未全部成功。不要删除仓库或 force push；按 PUBLISH.md 的恢复步骤检查。',file=sys.stderr)
        else:
            print('没有确认新远端创建成功；本地可能已经产生提交。脚本不会覆盖已有 GitHub 仓库。',file=sys.stderr)
        return 1
if __name__=='__main__': sys.exit(main())

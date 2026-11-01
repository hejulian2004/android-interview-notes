#!/usr/bin/env python3
"""Rebuild the offline public Markdown snapshot from a local public repo checkout."""
from pathlib import Path
import argparse
import datetime
import json
import re
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('checkout', nargs='?', default='content')
parser.add_argument('--output', default='engine/snapshot.json')
args = parser.parse_args()
root = Path(args.checkout).resolve()

def git(*arguments):
    return subprocess.check_output(['git', '-C', str(root), *arguments], text=True).strip()

if git('remote', 'get-url', 'origin').removesuffix('.git') != 'https://github.com/hejulian2004/android-interview-notes':
    raise SystemExit('Snapshot must use the authorized public android-interview-notes repository.')
if git('status', '--porcelain'):
    raise SystemExit('Snapshot requires a clean checkout so revision matches content.')
files = []
for path in sorted(root.rglob('*.md')):
    rel = path.relative_to(root).as_posix()
    if rel.startswith('docs/') or re.match(r'^(questions|supplements)/(?:[^/]+/)*[QE]\d+[-·][^/]+\.md$', rel):
        content = path.read_text()
        if re.search(r'\b[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}\b|(?<!\d)1[3-9]\d{9}(?!\d)', content):
            raise SystemExit(f'Contact-like data needs review before publishing: {rel}')
        files.append(dict(path=rel, sha=git('rev-parse', 'HEAD:' + rel), content=content))
value = dict(version=1, revision=git('rev-parse', 'HEAD'), generatedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(), fetchedAt=None, checkedAt=None, files=files)
Path(args.output).write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')))
print(f'Wrote {len(files)} public Markdown files at {value["revision"]}')

#!/usr/bin/env python3
"""Repository-level autonomous audit. Fails closed; never edits evidence to pass."""
import json, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
state=json.loads((ROOT/'STATE.json').read_text(encoding='utf-8'))
queue=json.loads((ROOT/'FREE_QUEUE.json').read_text(encoding='utf-8'))
errors=[]
if state.get('project')!='كتاب': errors.append('wrong project identity')
if state.get('scholarly_status')!='exploratory_unverified': errors.append('scholarly status escalated without sovereign gate')
if state.get('autonomy_contract') not in {'v3','v4'}: errors.append('unexpected autonomy contract')
ids=[x.get('id') for x in queue]
if len(ids)!=len(set(ids)): errors.append('duplicate task ids')
for item in queue:
    if item.get('status')=='processed':
        p=ROOT/'research'/'runs'
        if not list(p.glob(f"*-{item['id']}.md")): errors.append(f"missing artifact for {item['id']}")
for p in (ROOT/'corpus').glob('*.json'):
    if p.name=='quran-uthmani.json':
        raw=p.read_bytes(); hashlib.sha256(raw).hexdigest()
if errors:
    print('SELF_AUDIT_FAIL')
    for e in errors: print('-',e)
    raise SystemExit(1)
print('SELF_AUDIT_PASS')
print('pending=',sum(x.get('status')=='pending' for x in queue),'processed=',sum(x.get('status')=='processed' for x in queue))

#!/usr/bin/env python3
"""Deterministic quality gate for autonomous book research.
Never upgrades exploratory machine output into a scholarly claim.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = json.loads((ROOT / 'STATE.json').read_text(encoding='utf-8'))
QUEUE = json.loads((ROOT / 'FREE_QUEUE.json').read_text(encoding='utf-8'))
errors=[]
required_state={'project','status','next_task'}
missing=required_state-set(STATE)
if missing: errors.append(f'missing STATE fields: {sorted(missing)}')
if not isinstance(QUEUE,list) or not QUEUE: errors.append('queue empty or invalid')
allowed={'pending','processed'}
for item in QUEUE:
    if item.get('status') not in allowed: errors.append(f"invalid queue status: {item.get('id')}")
    for k in ('id','title','question','keywords'):
        if k not in item: errors.append(f"missing {k}: {item.get('id')}")
# Every processed task must have an artifact and a machine synthesis section.
runs=ROOT/'research'/'runs'
for item in QUEUE:
    if item.get('status')!='processed': continue
    matches=sorted(runs.glob(f"*-{item['id']}.md"))
    if not matches: errors.append(f"processed task without artifact: {item['id']}"); continue
    text=matches[-1].read_text(encoding='utf-8')
    if '## Evidence' not in text: errors.append(f"missing evidence section: {item['id']}")
    if '## Machine synthesis' not in text: errors.append(f"missing synthesis section: {item['id']}")
    if 'Primary text source:' not in text: errors.append(f"missing provenance: {item['id']}")
    # Require at least one explicit Quran citation in the evidence artifact.
    if not re.search(r'\*\*\d{1,3}:\d{1,3}\*\*', text): errors.append(f"no explicit verse citation: {item['id']}")
# Never allow final scholarly status to be implied by this exploratory gate.
if STATE.get('scholarly_status') not in (None,'exploratory_unverified'):
    errors.append('unexpected scholarly_status escalation')
if errors:
    print('QUALITY_GATE_FAIL')
    for e in errors: print('-',e)
    sys.exit(1)
print('QUALITY_GATE_PASS')
print('processed=',sum(x.get('status')=='processed' for x in QUEUE),'total=',len(QUEUE))

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

runs=ROOT/'research'/'runs'
corpus=ROOT/'corpus'
for item in QUEUE:
    if item.get('status')!='processed': continue
    matches=sorted(runs.glob(f"*-{item['id']}.md"))
    if not matches:
        errors.append(f"processed task without artifact: {item['id']}"); continue
    text=matches[-1].read_text(encoding='utf-8')
    if '## Evidence' not in text: errors.append(f"missing evidence section: {item['id']}")
    if '## Machine synthesis' not in text: errors.append(f"missing synthesis section: {item['id']}")
    if 'Primary text source:' not in text: errors.append(f"missing provenance: {item['id']}")
    evidence_cites=set(re.findall(r'\*\*(\d{1,3}:\d{1,3})\*\*', text.split('## Machine synthesis',1)[0]))
    if not evidence_cites: errors.append(f"no explicit verse citation: {item['id']}")
    synthesis=text.split('## Machine synthesis',1)[1] if '## Machine synthesis' in text else ''
    # Any citation emitted by the local model must already exist in the retrieved evidence.
    cited=set(re.findall(r'(?<!\d)(\d{1,3}:\d{1,3})(?!\d)', synthesis))
    unknown=sorted(cited-evidence_cites)
    if unknown: errors.append(f"model cited verses not in evidence for {item['id']}: {unknown[:10]}")
    # The free exploratory runner must not smuggle hadith/tafsir as verified evidence.
    provenance=text.split('## Provenance',1)[1] if '## Provenance' in text else ''
    if 'No hadith, tafsir, or historical claim was added' not in provenance:
        errors.append(f"exploratory provenance boundary missing: {item['id']}")

if STATE.get('scholarly_status') not in (None,'exploratory_unverified'):
    errors.append('unexpected scholarly_status escalation')
if errors:
    print('QUALITY_GATE_FAIL')
    for e in errors: print('-',e)
    sys.exit(1)
print('QUALITY_GATE_PASS')
print('processed=',sum(x.get('status')=='processed' for x in QUEUE),'total=',len(QUEUE))

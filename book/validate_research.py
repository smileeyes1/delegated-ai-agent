#!/usr/bin/env python3
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = json.loads((ROOT/'STATE.json').read_text(encoding='utf-8'))
QUEUE = json.loads((ROOT/'FREE_QUEUE.json').read_text(encoding='utf-8'))
errors=[]

if STATE.get('project') != 'كتاب': errors.append('wrong project identity')
if not isinstance(QUEUE,list) or not QUEUE: errors.append('empty queue')
for t in QUEUE:
    if t.get('status') not in {'pending','processed'}: errors.append(f"invalid task status: {t.get('id')}")

runs=ROOT/'research'/'runs'
for p in sorted(runs.glob('*.md')):
    text=p.read_text(encoding='utf-8')
    if '## Provenance' not in text: errors.append(f'missing provenance: {p.name}')
    # Every explicit Qur'an reference in the memo must correspond to an evidence hit in the same artifact.
    refs=set(re.findall(r'\b(\d{1,3}:\d{1,3})\b', text))
    evidence_refs=set(re.findall(r'\*\*(\d{1,3}:\d{1,3})\*\*', text))
    machine=text.split('## Machine synthesis',1)[-1].split('## Provenance',1)[0]
    for ref in re.findall(r'\b(\d{1,3}:\d{1,3})\b', machine):
        if ref not in evidence_refs: errors.append(f'unbacked reference {ref} in {p.name}')

if errors:
    print('\n'.join('ERROR: '+e for e in errors))
    sys.exit(1)
print('Research integrity checks passed.')

#!/usr/bin/env python3
import json, sys
from pathlib import Path
from free_autonomous_research import TASK_STATUSES, VERSE_REFERENCE, evidence_refs_and_memo

ROOT = Path(__file__).resolve().parent
STATE = json.loads((ROOT/'STATE.json').read_text(encoding='utf-8'))
QUEUE = json.loads((ROOT/'FREE_QUEUE.json').read_text(encoding='utf-8'))
errors=[]

if STATE.get('project') != 'كتاب': errors.append('wrong project identity')
if not isinstance(QUEUE,list) or not QUEUE: errors.append('empty queue')
for t in QUEUE:
    if t.get('status') not in TASK_STATUSES: errors.append(f"invalid task status: {t.get('id')}")

runs=ROOT/'research'/'runs'
for p in sorted(runs.glob('*.md')):
    text=p.read_text(encoding='utf-8')
    if '## Provenance' not in text: errors.append(f'missing provenance: {p.name}')
    # Every explicit Qur'an reference in the memo must correspond to an evidence hit in the same artifact.
    evidence_refs, machine = evidence_refs_and_memo(text)
    for ref in VERSE_REFERENCE.findall(machine):
        if ref not in evidence_refs: errors.append(f'unbacked reference {ref} in {p.name}')

if errors:
    print('\n'.join('ERROR: '+e for e in errors))
    sys.exit(1)
print('Research integrity checks passed.')

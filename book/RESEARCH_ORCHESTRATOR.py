#!/usr/bin/env python3
"""Cheap deterministic controller: choose the next useful task without an LLM."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
state = json.loads((ROOT/'STATE.json').read_text(encoding='utf-8'))
queue = json.loads((ROOT/'FREE_QUEUE.json').read_text(encoding='utf-8'))

# Prefer foundational concepts, then downstream synthesis. Never run Q020 until its inputs exist.
priority = {f'Q{i:03d}': i for i in range(1, 21)}
processed = {x['id'] for x in queue if x.get('status') == 'processed'}
for item in queue:
    if item.get('status') != 'pending':
        continue
    if item['id'] == 'Q020' and len(processed) < 10:
        continue
    item['_score'] = priority.get(item['id'], 999)

candidates = [x for x in queue if x.get('status') == 'pending' and '_score' in x]
candidates.sort(key=lambda x: (x['_score'], x['id']))
chosen = candidates[0] if candidates else next((x for x in queue if x.get('status') == 'pending'), None)

for x in queue:
    x.pop('_score', None)
if chosen:
    state['next_task'] = chosen['id']
    state['scheduler_decision'] = {'task': chosen['id'], 'reason': 'deterministic_priority_with_dependency_guard'}
else:
    state['status'] = 'queue_complete'
    state['next_task'] = None

(ROOT/'STATE.json').write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
(ROOT/'FREE_QUEUE.json').write_text(json.dumps(queue, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print('NEXT_TASK=', state.get('next_task'))

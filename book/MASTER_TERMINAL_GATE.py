from pathlib import Path
import json, sys

ROOT = Path(__file__).parent
DIRECTIVE = ROOT / 'MASTER_TERMINAL_DIRECTIVE.md'
STATE = ROOT / 'STATE.json'
QUEUE = ROOT / 'FREE_QUEUE.json'

required = [DIRECTIVE, STATE, QUEUE]
missing = [str(p) for p in required if not p.exists()]
if missing:
    print('MASTER_GATE_FAIL: missing=' + ','.join(missing))
    raise SystemExit(1)

state = json.loads(STATE.read_text(encoding='utf-8'))
queue = json.loads(QUEUE.read_text(encoding='utf-8'))

assert state.get('project') == 'كتاب'
assert isinstance(queue, list) and queue

# The gate is intentionally conservative: it verifies governance prerequisites,
# but never fabricates intellectual completion metrics.
text = DIRECTIVE.read_text(encoding='utf-8')
for marker in ('Do not assume the conclusion', 'Evidence integrity', 'Intellectual honesty', 'Terminal condition', 'single canonical writer'):
    assert marker in text, f'MASTER_GATE_FAIL: missing directive marker: {marker}'

print('MASTER_TERMINAL_GATE=PASS')
print('PROJECT=' + str(state.get('project')))
print('QUEUE_ITEMS=' + str(len(queue)))
print('COMPLETION_NOT_ASSERTED=True')

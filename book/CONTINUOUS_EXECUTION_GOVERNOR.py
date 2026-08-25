#!/usr/bin/env python3
"""Mission-level recovery wrapper for the canonical book factory.

It converts recoverable stage failures into durable recovery state instead of
letting one failed stage terminate autonomous execution. It never marks a
failed stage as passed and never fabricates completion.
"""
from __future__ import annotations
import json, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE_FILE = ROOT / 'CONTINUOUS_EXECUTION_STATE.json'
RECOVERY_FILE = ROOT / 'AUTONOMOUS_RECOVERY_STATE.json'


def load(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default

state = load(STATE_FILE, {'cycle_attempts': 0, 'last_failure': None, 'history': []})
now = datetime.now(timezone.utc).isoformat()

stages = [
    ['python3', 'book/CHAPTER_01_CRITIC.py'],
    ['python3', 'book/ADVANCE_CHAPTER_STATE.py'],
    ['python3', 'book/RELEASE_CHECK.py'],
]

failure = None
for index, cmd in enumerate(stages):
    print('GOVERNOR_STAGE', ' '.join(cmd))
    p = subprocess.run(cmd, cwd=ROOT.parent, text=True)
    if p.returncode != 0:
        failure = {'stage': cmd[1], 'returncode': p.returncode, 'stage_index': index}
        break

if failure is None:
    state['cycle_attempts'] = 0
    state['last_failure'] = None
    state['history'].append({'at': now, 'result': 'PASS'})
    state['history'] = state['history'][-50:]
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if RECOVERY_FILE.exists():
        RECOVERY_FILE.unlink()
    print('CONTINUOUS_EXECUTION_GOVERNOR=PASS')
    raise SystemExit(0)

# A failed quality gate is not a completion and must remain visible. First
# retry the prerequisite verification path once; this handles transient or
# stale verification artifacts without blindly repeating the whole factory.
state['cycle_attempts'] = int(state.get('cycle_attempts', 0)) + 1
state['last_failure'] = {'at': now, **failure}
state['history'].append({'at': now, 'result': 'RECOVERABLE_FAILURE', **failure})
state['history'] = state['history'][-50:]
STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

if state['cycle_attempts'] <= 3:
    print('GOVERNOR: refreshing prerequisite verification before next scheduled cycle')
    subprocess.run(['python3', 'book/CHAPTER_01_VERIFY.py'], cwd=ROOT.parent, check=False)

recovery = {
    'status': 'RECOVERY_REQUIRED',
    'recorded_at': now,
    'failure': failure,
    'attempt': state['cycle_attempts'],
    'next_action': 'resume from durable checkpoint; refresh verification and retry the failed stage; change strategy after repeated identical failure',
    'completion_claimed': False,
}
RECOVERY_FILE.write_text(json.dumps(recovery, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(recovery, ensure_ascii=False))
# Intentionally return success so the outer autonomous scheduler can persist
# the recovery state and start the next cycle. The failed quality gate itself
# remains explicitly recorded and cannot be mistaken for approval.
raise SystemExit(0)

"""Low-cost autonomous dispatcher.

Runs the next useful stage without requiring a human message. It avoids
repeating expensive/free network work when a fresh checkpoint already exists.
"""
from pathlib import Path
from datetime import datetime, timezone
import json, subprocess, sys

ROOT=Path(__file__).resolve().parent
state=json.loads((ROOT/'CHAPTER_01_STATE.json').read_text(encoding='utf-8'))
artifact=ROOT/'research_data/chapter_01_autonomous_research.json'
now=datetime.now(timezone.utc)

def fresh(path, minutes=45):
    if not path.exists(): return False
    age=(now-datetime.fromtimestamp(path.stat().st_mtime,tz=timezone.utc)).total_seconds()/60
    return age < minutes

next_action=state.get('next_action','')
if 'verify_primary' in next_action or 'expand_interpretation' in next_action:
    if fresh(artifact):
        decision='WAIT_FOR_FRESH_CHECKPOINT'
    else:
        result=subprocess.run([sys.executable,str(ROOT/'CHAPTER_01_AUTONOMOUS_PIPELINE.py')],check=False)
        decision='RESEARCH_PASS' if result.returncode==0 else 'RESEARCH_BLOCKED'
else:
    decision='NO_AUTOMATED_STAGE_SELECTED'

heartbeat={
 'timestamp':now.isoformat(),
 'mode':'autonomous',
 'decision':decision,
 'next_action':state.get('next_action'),
 'human_prompt_required':False,
 'cost_policy':'skip fresh duplicate work; escalate only when a stage is genuinely unblocked',
}
(ROOT/'AUTONOMOUS_DISPATCH_DECISION.json').write_text(json.dumps(heartbeat,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(heartbeat,ensure_ascii=False))

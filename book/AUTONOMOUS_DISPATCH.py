"""Low-cost autonomous dispatcher with evidence-aware freshness checks."""
from pathlib import Path
from datetime import datetime, timezone
import json, subprocess, sys

ROOT=Path(__file__).resolve().parent
state=json.loads((ROOT/'CHAPTER_01_STATE.json').read_text(encoding='utf-8'))
artifact=ROOT/'research_data/chapter_01_autonomous_research.json'
now=datetime.now(timezone.utc)

next_action=state.get('next_action','')
needs_research=('verify_primary' in next_action or 'expand_interpretation' in next_action or 'counter_evidence' in next_action)

needs_repair=False
if not artifact.exists():
    needs_repair=True
else:
    try:
        d=json.loads(artifact.read_text(encoding='utf-8'))
        records=d.get('records',[])
        verified=d.get('verified_text_count',0)
        refs=d.get('refs',[])
        mismatch=any(r.get('text_crosscheck')!='MATCH' for r in records)
        missing_boundary='لا يمثل حكمًا نهائيًا' not in d.get('draft','') or 'ما لم يُحسم' not in d.get('draft','')
        needs_repair=(verified < len(refs) or mismatch or missing_boundary or not d.get('counter_evidence_scan') or not d.get('argument_map'))
    except Exception:
        needs_repair=True

if needs_research and needs_repair:
    result=subprocess.run([sys.executable,str(ROOT/'CHAPTER_01_AUTONOMOUS_PIPELINE.py')],check=False)
    decision='RESEARCH_PASS' if result.returncode==0 else 'RESEARCH_BLOCKED'
elif needs_research:
    decision='WAIT_FOR_FRESH_CHECKPOINT'
else:
    decision='NO_AUTOMATED_STAGE_SELECTED'

heartbeat={
 'timestamp':now.isoformat(),
 'mode':'autonomous',
 'decision':decision,
 'next_action':next_action,
 'human_prompt_required':False,
 'repair_triggered':needs_repair,
 'cost_policy':'skip only genuinely fresh, valid research; rerun when evidence is incomplete or blocked',
}
(ROOT/'AUTONOMOUS_DISPATCH_DECISION.json').write_text(json.dumps(heartbeat,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(heartbeat,ensure_ascii=False))

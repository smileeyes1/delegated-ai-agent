import json, os
from datetime import datetime, timezone

ROOT='book'
STATE=f'{ROOT}/FACTORY_STATE.json'
CHAPTER=f'{ROOT}/CHAPTER_01_STATE.json'
OUT=f'{ROOT}/META_CONTROL_STATE.json'


def load(path):
    try:
        with open(path,encoding='utf-8') as f:return json.load(f)
    except Exception:return {}

factory=load(STATE); chapter=load(CHAPTER)
checks=[]
for p in [STATE,CHAPTER,f'{ROOT}/AUTONOMOUS_COMPLETION_MATRIX.md',f'{ROOT}/RELEASE_GATES.md']:
    checks.append({'path':p,'exists':os.path.exists(p)})

if not checks[0]['exists'] or not checks[1]['exists']:
    action='repair_durable_state'
elif chapter.get('next_action'):
    action=chapter['next_action']
elif factory.get('next_task'):
    action=factory['next_task']
else:
    action='gap_audit_and_generate_next_task'

state={
 'timestamp':datetime.now(timezone.utc).isoformat(),
 'mode':'autonomous_meta_control',
 'human_prompt_required':False,
 'factory_status':factory.get('status','UNKNOWN'),
 'chapter_status':chapter.get('status','UNKNOWN'),
 'next_action':action,
 'health_checks':checks,
 'rules':['no fabricated evidence','no silent uncertainty upgrade','no bypass of blocked gates','no blind infinite retries','checkpoint every completed stage'],
 'release_allowed':False,
 'release_reason':'real end-to-end scholarly production proof is still required'
}
with open(OUT,'w',encoding='utf-8') as f:json.dump(state,f,ensure_ascii=False,indent=2)
print(json.dumps(state,ensure_ascii=False,indent=2))

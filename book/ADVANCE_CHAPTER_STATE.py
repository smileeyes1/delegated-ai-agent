from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
state_path=ROOT/'CHAPTER_01_STATE.json'; art=ROOT/'research_data/chapter_01_autonomous_research.json'; crit=ROOT/'research_data/chapter_01_critique.json'
s=json.loads(state_path.read_text(encoding='utf-8')); a=json.loads(art.read_text(encoding='utf-8')); c=json.loads(crit.read_text(encoding='utf-8'))
if c.get('status')!='PASS':
    s['status']='BLOCKED'; s['draft_status']='BLOCKED'; s['blockers']=c.get('issues',[]); s['next_action']='repair_critic_findings';
else:
    s['status']='RESEARCH_VERIFIED'; s['evidence_count']=len(a.get('records',[])); s['verified_evidence_count']=a.get('verified_text_count',0); s['counter_evidence_pass']=len(a.get('counter_evidence_scan',[]))>0; s['argument_map']=a.get('argument_map'); s['draft_status']='BOUNDED_RESEARCH_DRAFT'; s['blockers']=[]; s['next_action']='expand_interpretation_comparison_and_independent_critique'
state_path.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(s,ensure_ascii=False))

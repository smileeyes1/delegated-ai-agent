from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
checks={}
checks['factory_state']= (ROOT/'FACTORY_STATE.json').exists()
checks['chapter_state']= (ROOT/'CHAPTER_01_STATE.json').exists()
art=ROOT/'research_data/chapter_01_autonomous_research.json'
crit=ROOT/'research_data/chapter_01_critique.json'
checks['research_artifact']=art.exists(); checks['critique']=crit.exists()
if art.exists():
    a=json.loads(art.read_text(encoding='utf-8')); checks['all_primary_text_verified']=a.get('verified_text_count')==len(a.get('refs',[])); checks['counter_evidence']=len(a.get('counter_evidence_scan',[]))>0
else: checks['all_primary_text_verified']=False; checks['counter_evidence']=False
if crit.exists(): checks['critic_pass']=json.loads(crit.read_text(encoding='utf-8')).get('status')=='PASS'
else: checks['critic_pass']=False
# A chapter is not releasable merely because a bounded draft exists.
checks['final_chapter_approved']=False
checks['release_ready']=all(checks.values())
print(json.dumps({'release_ready':checks['release_ready'],'checks':checks},ensure_ascii=False,indent=2))
if not checks['release_ready']: raise SystemExit(2)

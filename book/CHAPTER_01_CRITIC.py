"""Deterministic pre-publication critic for Chapter 01."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
p=ROOT/'research_data/chapter_01_autonomous_research.json'
if not p.exists(): raise SystemExit('research artifact missing')
d=json.loads(p.read_text(encoding='utf-8'))
issues=[]
records=d.get('records',[])
if not records: issues.append('NO_EVIDENCE_RECORDS')
if any(r.get('text_crosscheck')!='MATCH' for r in records): issues.append('TEXT_CROSSCHECK_FAILURE')
if d.get('verified_text_count') != len(d.get('refs',[])): issues.append('INCOMPLETE_PRIMARY_VERIFICATION')
if not d.get('counter_evidence_scan'): issues.append('NO_COUNTER_EVIDENCE_SCAN')
if not d.get('argument_map'): issues.append('NO_ARGUMENT_MAP')
draft=d.get('draft','')
for forbidden in ['يثبت نهائيا','يحسم نهائيا','لا خلاف','أجمع العلماء']:
    if forbidden in draft: issues.append('OVERCLAIM:'+forbidden)
if 'لا يمثل حكمًا نهائيًا' not in draft: issues.append('MISSING_DRAFT_BOUNDARY')
if 'ما لم يُحسم' not in draft: issues.append('MISSING_UNCERTAINTY_SECTION')
result={'status':'PASS' if not issues else 'BLOCKED','issues':issues,'evidence_records':len(records),'verified_text_count':d.get('verified_text_count',0),'counter_evidence_count':len(d.get('counter_evidence_scan',[]))}
(ROOT/'research_data/chapter_01_critique.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
if issues: raise SystemExit(2)

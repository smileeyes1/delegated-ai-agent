"""Deterministic pre-publication critic for Chapter 01.

Primary-text verification is now live and separate from interpretation.
Orthographic comparison is Unicode-aware and conservative.
"""
from pathlib import Path
import json
import re
import unicodedata

ROOT = Path(__file__).resolve().parent
p = ROOT / 'research_data/chapter_01_autonomous_research.json'
live_p = ROOT / 'research_data/chapter_01_live_verification.json'
if not p.exists():
    raise SystemExit('research artifact missing')
if not live_p.exists():
    raise SystemExit('live primary verification artifact missing')
d = json.loads(p.read_text(encoding='utf-8'))
live = json.loads(live_p.read_text(encoding='utf-8'))
issues = []
records = d.get('records', [])
if not records:
    issues.append('NO_EVIDENCE_RECORDS')


def comparison_form(text: str) -> str:
    s = unicodedata.normalize('NFKC', text or '')
    s = ''.join(ch for ch in s if unicodedata.category(ch) not in {'Mn', 'Me', 'Cf'})
    s = s.replace('\u0640', '')
    s = s.replace('ٱ', 'ا').replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    s = s.replace('ى', 'ي').replace('ؤ', 'و').replace('ئ', 'ي')
    s = re.sub(r'\s+', ' ', s).strip()
    return s

crosscheck_failures = []
for r in records:
    a = comparison_form(r.get('primary_text', ''))
    b = comparison_form(r.get('quranpedia_text', ''))
    if a != b:
        crosscheck_failures.append(r.get('reference', r.get('id', 'UNKNOWN')))

if crosscheck_failures:
    issues.append('TEXT_CROSSCHECK_FAILURE:' + ','.join(crosscheck_failures))

if int(live.get('verified_count', 0)) != int(live.get('required_count', 0)):
    issues.append('INCOMPLETE_PRIMARY_VERIFICATION')

# Do not inherit old counter-evidence as if it were freshly verified.
if not d.get('counter_evidence_scan'):
    issues.append('NO_COUNTER_EVIDENCE_SCAN')
if not d.get('argument_map'):
    issues.append('NO_ARGUMENT_MAP')

draft = d.get('draft', '')
for forbidden in ['يثبت نهائيا', 'يحسم نهائيا', 'لا خلاف', 'أجمع العلماء']:
    if forbidden in draft:
        issues.append('OVERCLAIM:' + forbidden)
if 'لا يمثل حكمًا نهائيًا' not in draft:
    issues.append('MISSING_DRAFT_BOUNDARY')
if 'ما لم يُحسم' not in draft:
    issues.append('MISSING_UNCERTAINTY_SECTION')

result = {
    'status': 'PASS' if not issues else 'BLOCKED',
    'issues': issues,
    'evidence_records': len(records),
    'live_verified_text_count': int(live.get('verified_count', 0)),
    'required_text_count': int(live.get('required_count', 0)),
    'counter_evidence_count': len(d.get('counter_evidence_scan', [])),
    'comparison_method': 'Unicode NFKC + conservative Arabic orthographic normalization',
    'original_source_text_preserved': True,
}
(ROOT / 'research_data/chapter_01_critique.json').write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
)
print(json.dumps(result, ensure_ascii=False))
if issues:
    raise SystemExit(2)

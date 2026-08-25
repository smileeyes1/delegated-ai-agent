"""Deterministic pre-publication critic for Chapter 01.

Cross-source Quran checks must distinguish orthographic presentation differences
from substantive text differences. Normalization is used only for comparison;
original source text is never overwritten or promoted by normalization alone.
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parent
p = ROOT / 'research_data/chapter_01_autonomous_research.json'
if not p.exists():
    raise SystemExit('research artifact missing')
d = json.loads(p.read_text(encoding='utf-8'))
issues = []
records = d.get('records', [])
if not records:
    issues.append('NO_EVIDENCE_RECORDS')


def comparison_form(text: str) -> str:
    """Conservative comparison form for orthographic/script rendering variance."""
    s = text or ''
    s = s.replace('\ufeff', '').replace('\u0640', '')
    # Remove Quranic/Arabic combining marks and presentation-only marks.
    s = re.sub(r'[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]', '', s)
    # Normalize common Arabic letter variants used by different editions/APIs.
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

# The research artifact may report zero verified texts until the primary-source
# verifier itself records successful verification. Never infer verification from
# a normalized cross-check.
verified_count = int(d.get('verified_text_count', 0) or 0)
required_count = len(d.get('refs', []))
if verified_count != required_count:
    issues.append('INCOMPLETE_PRIMARY_VERIFICATION')

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
    'verified_text_count': verified_count,
    'required_text_count': required_count,
    'counter_evidence_count': len(d.get('counter_evidence_scan', [])),
    'comparison_method': 'conservative_orthographic_normalization_only',
    'original_source_text_preserved': True,
}
(ROOT / 'research_data/chapter_01_critique.json').write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
)
print(json.dumps(result, ensure_ascii=False))
if issues:
    raise SystemExit(2)

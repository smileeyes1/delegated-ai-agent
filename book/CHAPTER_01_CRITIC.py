"""Challenge Chapter 01's source comparison and bounded research claims."""

import argparse
import hashlib
import json
from pathlib import Path

if __package__:
    from .chapter_sources import COMPARISON_METHOD, verify_verse
else:
    from chapter_sources import COMPARISON_METHOD, verify_verse


ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'research_data'


def review(research, live):
    issues = []
    records = research.get('records', [])
    if (
        not records
        or [r.get('reference') for r in records] != research.get('refs')
        or research.get('verified_text_count') != len(records)
    ):
        issues.append('INCOMPLETE_EVIDENCE_RECORDS')

    basmalah = research.get('crosscheck_basmalah', '')
    crosscheck_failures = []
    for record in records:
        ref = record.get('reference', 'UNKNOWN')
        primary = record.get('primary_text', '')
        secondary = record.get('quranpedia_text', '')
        if (
            record.get('crosscheck_method') != COMPARISON_METHOD
            or record.get('status') != 'verified_text'
            or record.get('text_crosscheck') != 'MATCH'
            or not isinstance(primary, str)
            or not isinstance(secondary, str)
            or not isinstance(basmalah, str)
            or not verify_verse(ref, primary, secondary, basmalah)
        ):
            crosscheck_failures.append(ref)
    if crosscheck_failures:
        issues.append('TEXT_CROSSCHECK_FAILURE:' + ','.join(crosscheck_failures))

    verified = live.get('verified_count', 0)
    required = live.get('required_count', 0)
    if type(required) is not int or type(verified) is not int or required <= 0 or verified != required:
        issues.append('INCOMPLETE_PRIMARY_VERIFICATION')

    if not research.get('counter_evidence_scan'):
        issues.append('NO_COUNTER_EVIDENCE_SCAN')
    if not research.get('argument_map'):
        issues.append('NO_ARGUMENT_MAP')

    draft = research.get('draft', '')
    for forbidden in ['يثبت نهائيا', 'يحسم نهائيا', 'لا خلاف', 'أجمع العلماء']:
        if forbidden in draft:
            issues.append('OVERCLAIM:' + forbidden)
    if 'لا تمثل حكمًا نهائيًا' not in draft:
        issues.append('MISSING_DRAFT_BOUNDARY')
    if 'ما لم يُحسم' not in draft:
        issues.append('MISSING_UNCERTAINTY_SECTION')

    return {
        'status': 'PASS' if not issues else 'BLOCKED',
        'issues': issues,
        'evidence_records': len(records),
        'live_verified_text_count': verified,
        'required_text_count': required,
        'counter_evidence_count': len(research.get('counter_evidence_scan', [])),
        'comparison_method': COMPARISON_METHOD,
        'original_source_text_preserved': True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=DATA)
    data_dir = parser.parse_args().output_dir
    research = (data_dir / 'chapter_01_autonomous_research.json').read_bytes()
    live = (data_dir / 'chapter_01_live_verification.json').read_bytes()
    result = review(json.loads(research), json.loads(live))
    result['research_sha256'] = hashlib.sha256(research).hexdigest()
    result['live_verification_sha256'] = hashlib.sha256(live).hexdigest()
    text = json.dumps(result, ensure_ascii=False, indent=2)
    (data_dir / 'chapter_01_critique.json').write_text(text + '\n', encoding='utf-8')
    print(text)
    raise SystemExit(0 if result['status'] == 'PASS' else 2)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Live primary-text verifier for Chapter 01.

This adapter verifies the chapter's candidate references against a freshly
retrieved Uthmani Quran corpus. It records provenance and exact returned text;
it never promotes tafsir, inference, or machine synthesis to primary evidence.
"""
import hashlib, json, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / 'CHAPTER_01_EVIDENCE_LEDGER.json'
OUT = ROOT / 'research_data' / 'chapter_01_live_verification.json'
OUT.parent.mkdir(parents=True, exist_ok=True)

ledger = json.loads(LEDGER.read_text(encoding='utf-8'))
refs = [r['reference'] for r in ledger['records']]
url = 'https://api.alquran.cloud/v1/quran/quran-uthmani'
with urllib.request.urlopen(url, timeout=90) as response:
    raw = response.read()

payload_hash = hashlib.sha256(raw).hexdigest()
data = json.loads(raw.decode('utf-8'))['data']['surahs']
by_ref = {}
for surah in data:
    for ayah in surah['ayahs']:
        by_ref[f"{surah['number']}:{ayah['numberInSurah']}"] = {
            'reference': f"{surah['number']}:{ayah['numberInSurah']}",
            'surah': surah['name'],
            'text': ayah['text'],
        }

records = []
verified = 0
for ref in refs:
    if '-' in ref:
        start, end = ref.split(':', 1)[1].split('-')
        surah = int(ref.split(':', 1)[0])
        keys = [f'{surah}:{n}' for n in range(int(start), int(end)+1)]
    else:
        keys = [ref]
    verses = [by_ref[k] for k in keys if k in by_ref]
    ok = len(verses) == len(keys)
    if ok:
        verified += 1
    records.append({
        'reference': ref,
        'status': 'verified_primary_text' if ok else 'missing_from_live_source',
        'verses': verses,
    })

result = {
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'source': {'name': 'alQuran.cloud quran-uthmani', 'url': url, 'sha256': payload_hash},
    'verification_scope': 'primary Quran text only',
    'records': records,
    'verified_count': verified,
    'required_count': len(refs),
    'counter_evidence_verified': False,
    'interpretation_verified': False,
    'note': 'Primary-text retrieval is verified here; this does not verify tafsir, hadith, inference, or scholarly interpretation.',
}
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status':'PASS' if verified == len(refs) else 'BLOCKED', 'verified_count':verified, 'required_count':len(refs), 'artifact':str(OUT)}, ensure_ascii=False))
if verified != len(refs):
    raise SystemExit(2)

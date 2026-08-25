import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
ledger = ROOT / 'CHAPTER_01_EVIDENCE_LEDGER.json'
assert ledger.exists()
d = json.loads(ledger.read_text(encoding='utf-8'))
records = d['records']
assert records and all(r['status'] == 'candidate' for r in records)

# Replace the old fixture-only verification with a live primary-source check.
p = ROOT / 'LIVE_PRIMARY_TEXT_VERIFY.py'
subprocess.run(['python3', str(p)], check=True)
live = json.loads((ROOT / 'research_data' / 'chapter_01_live_verification.json').read_text(encoding='utf-8'))
assert live['verified_count'] == live['required_count']

print('PASS: live primary Quran text verification')
print('verified_count=', live['verified_count'])
print('counter_evidence_verified=', live['counter_evidence_verified'])
print('interpretation_verified=', live['interpretation_verified'])

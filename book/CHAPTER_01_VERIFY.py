import json
from pathlib import Path

p = Path(__file__).with_name('CHAPTER_01_EVIDENCE_LEDGER.json')
d = json.loads(p.read_text(encoding='utf-8'))
records = d['records']
assert len(records) == 12
assert all(r['status'] == 'candidate' for r in records)
assert d['verification']['verified_count'] == 0
assert d['verification']['counter_evidence_complete'] is False
print('PASS: ledger integrity; no candidate promoted to verified')

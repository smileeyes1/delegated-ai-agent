from pathlib import Path
from urllib.request import Request, urlopen
import hashlib, json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "research_data"
DATA.mkdir(exist_ok=True)
URL = "https://tanzil.net/pub/download/index.php?quranType=uthmani&outType=txt-2&agree=true&marks=true&sajdah=true&rub=true&stanween=true"
refs = ["2:2","2:185","5:15","5:16","10:57","14:1","16:89","17:9","29:45","39:23","57:16","62:2"]
raw = urlopen(Request(URL, headers={"User-Agent":"BOOK_FACTORY/1.0"}), timeout=30).read()
text = raw.decode("utf-8-sig")
sha = hashlib.sha256(raw).hexdigest()
(DATA / "tanzil-uthmani.txt").write_text(text, encoding="utf-8")
passages = {}
for line in text.splitlines():
    parts = line.split("|", 2)
    if len(parts) == 3 and f"{parts[0]}:{parts[1]}" in refs:
        passages[f"{parts[0]}:{parts[1]}"] = parts[2].strip()
missing = [r for r in refs if r not in passages]
record = {"run_at":datetime.now(timezone.utc).isoformat(),"source":"Tanzil Project","source_url":URL,"text_type":"Uthmani","sha256_raw_download":sha,"references_requested":refs,"references_found":sorted(passages),"missing":missing,"status":"VERIFIED_ACQUISITION" if not missing else "BLOCKED_MISSING_PASSAGES","interpretation_status":"NOT_INTERPRETED","license_note":"Tanzil Quran text is CC BY 3.0; preserve attribution and no-modification terms.","passages":passages}
(DATA / "chapter_01_primary_evidence.json").write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"status":record["status"],"sha256":sha,"found":len(passages),"missing":missing},ensure_ascii=False))
if missing: raise SystemExit(2)

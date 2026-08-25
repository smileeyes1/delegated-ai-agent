#!/usr/bin/env python3
import json, os, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = ROOT / 'STATE.json'
QUEUE = ROOT / 'FREE_QUEUE.json'
RUNS = ROOT / 'research' / 'runs'
CORPUS = ROOT / 'corpus'
RUNS.mkdir(parents=True, exist_ok=True)
CORPUS.mkdir(parents=True, exist_ok=True)

state = json.loads(STATE.read_text(encoding='utf-8'))
queue = json.loads(QUEUE.read_text(encoding='utf-8'))

tasks = [x for x in queue if x.get('status') == 'pending']
if not tasks:
    print('No pending tasks.')
    state['status'] = 'queue_complete'
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    sys.exit(0)

task = tasks[0]
print('TASK:', task['id'], task['title'])

# Free primary source: Quran text API. Cache locally to avoid repeated downloads.
quran_file = CORPUS / 'quran-uthmani.json'
if not quran_file.exists():
    import urllib.request
    url = 'https://api.alquran.cloud/v1/quran/quran-uthmani'
    with urllib.request.urlopen(url, timeout=60) as r:
        data = r.read()
    quran_file.write_bytes(data)

quran = json.loads(quran_file.read_text(encoding='utf-8'))['data']['surahs']
keywords = task['keywords']
pattern = re.compile('|'.join(re.escape(k) for k in keywords))
hits = []
for surah in quran:
    for ayah in surah['ayahs']:
        text = ayah['text']
        if pattern.search(text):
            hits.append({
                'surah': surah['number'],
                'name': surah['name'],
                'ayah': ayah['numberInSurah'],
                'text': text,
            })

# Keep the evidence set bounded: strongest lexical matches first, then deterministic order.
hits = hits[:120]
evidence_path = CORPUS / f"{task['id']}.json"
evidence_path.write_text(json.dumps(hits, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# Local, zero-key model. Ollama is installed by the workflow. If unavailable, preserve the
# deterministic evidence and mark the synthesis as pending instead of fabricating anything.
prompt = f'''أنت باحث مساعد في مشروع كتاب عن: ماذا يصنع الوحي في الإنسان؟\n\nالمهمة: {task['title']}\nالسؤال: {task['question']}\n\nقواعد صارمة:\n- لا تفترض النتيجة.\n- لا تنسب إلى القرآن ما لا يدل عليه النص.\n- افصل بين: النص، الملاحظة، الفهم، الاستنتاج.\n- لا تستخدم أي حديث أو تفسير غير موجود في البيانات المعطاة.\n- إذا كانت الأدلة غير كافية قل: غير كافٍ.\n- لا تكتب وعظاً أو خطاباً تحفيزياً.\n- أخرج مذكرة بحثية قصيرة بالعربية، مع إحالات سورة:آية.\n\nالآيات المرشحة:\n{json.dumps(hits, ensure_ascii=False)[:28000]}'''

memo = None
try:
    p = subprocess.run(['ollama','run','qwen2.5:0.5b',prompt], text=True, capture_output=True, timeout=180)
    if p.returncode == 0 and p.stdout.strip():
        memo = p.stdout.strip()
except Exception as e:
    print('Local model unavailable:', e)

now = datetime.now(timezone.utc).isoformat()
out = RUNS / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{task['id']}.md"
body = [f"# {task['title']}", '', f"**Run:** {now}", f"**Evidence hits:** {len(hits)}", '', '## Evidence', '']
for h in hits[:40]:
    body.append(f"- **{h['surah']}:{h['ayah']}** — {h['text']}")
body += ['', '## Machine synthesis', '']
body.append(memo if memo else '**PENDING — local model unavailable. No conclusion was generated.**')
body += ['', '## Provenance', '', '- Primary text source: alQuran.cloud `quran-uthmani` API.', '- This run is exploratory evidence processing, not final scholarly verification.', '- No hadith, tafsir, or historical claim was added by this run.']
out.write_text('\n'.join(body) + '\n', encoding='utf-8')

# Advance state only after producing a concrete artifact. Do not claim scholarly completion.
task['status'] = 'processed'
task['last_run'] = now
state['last_run'] = now
state['last_task'] = task['id']
state['last_artifact'] = str(out.relative_to(ROOT.parent))
state['status'] = 'running'
state['next_task'] = next((x['id'] for x in queue if x.get('status') == 'pending'), None)
QUEUE.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('WROTE', out)

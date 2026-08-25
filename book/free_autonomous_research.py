#!/usr/bin/env python3
import json, re, subprocess, sys
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
    state['status'] = 'queue_complete'
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    sys.exit(0)

task = tasks[0]
print('TASK:', task['id'], task['title'])

quran_file = CORPUS / 'quran-uthmani.json'
if not quran_file.exists():
    import urllib.request
    url = 'https://api.alquran.cloud/v1/quran/quran-uthmani'
    with urllib.request.urlopen(url, timeout=60) as r:
        quran_file.write_bytes(r.read())

quran = json.loads(quran_file.read_text(encoding='utf-8'))['data']['surahs']
keywords = task['keywords']
pattern = re.compile('|'.join(re.escape(k) for k in keywords))
hits = []
for surah in quran:
    for ayah in surah['ayahs']:
        if pattern.search(ayah['text']):
            hits.append({'surah': surah['number'], 'name': surah['name'], 'ayah': ayah['numberInSurah'], 'text': ayah['text']})
hits = hits[:120]

timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
now = datetime.now(timezone.utc).isoformat()
evidence_path = CORPUS / f"{task['id']}.json"
evidence_path.write_text(json.dumps(hits, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

prompt = f'''أنت باحث مساعد في مشروع كتاب عن: ماذا يصنع الوحي في الإنسان؟\nالمهمة: {task['title']}\nالسؤال: {task['question']}\nقواعد: لا تفترض النتيجة؛ افصل النص والملاحظة والفهم والاستنتاج؛ لا تستخدم حديثًا أو تفسيرًا غير معطى؛ إذا لم تكف الأدلة فقل غير كافٍ؛ لا تختلق إحالات. أخرج مذكرة قصيرة بالعربية مع إحالات سورة:آية.\nالآيات المرشحة:\n{json.dumps(hits, ensure_ascii=False)[:28000]}'''

memo = None
model_error = None
try:
    p = subprocess.run(['ollama', 'run', 'qwen2.5:0.5b', prompt], text=True, capture_output=True, timeout=180)
    if p.returncode == 0 and p.stdout.strip():
        memo = p.stdout.strip()
    else:
        model_error = (p.stderr or 'model returned no output').strip()[-1000:]
except Exception as e:
    model_error = str(e)

out = RUNS / f"{timestamp}-{task['id']}.md"
body = [f"# {task['title']}", '', f"**Run:** {now}", f"**Evidence hits:** {len(hits)}", '', '## Evidence', '']
for h in hits[:40]:
    body.append(f"- **{h['surah']}:{h['ayah']}** — {h['text']}")
body += ['', '## Machine synthesis', '']
body.append(memo if memo else '**PENDING — local model unavailable. No conclusion was generated.**')
body += ['', '## Provenance', '', '- Primary text source: alQuran.cloud `quran-uthmani` API.', '- Exploratory evidence processing only; not final scholarly verification.', '- No hadith, tafsir, or historical claim was added by this run.']
if model_error:
    body += ['', '## Runtime note', '', f'- Local synthesis failed: `{model_error}`']
out.write_text('\n'.join(body) + '\n', encoding='utf-8')

# Critical recovery rule: raw evidence is saved, but a failed synthesis never advances the queue.
if memo:
    task['status'] = 'processed'
    task['last_run'] = now
    state['last_run'] = now
    state['last_task'] = task['id']
    state['last_artifact'] = str(out.relative_to(ROOT.parent))
    state['status'] = 'running'
    state['next_task'] = next((x['id'] for x in queue if x.get('status') == 'pending'), None)
    queue_changed = True
else:
    task['status'] = 'pending'
    task['last_attempt'] = now
    task['failure'] = 'local_model_unavailable'
    state['status'] = 'blocked_retryable'
    state['last_attempt'] = now
    state['last_task'] = task['id']
    state['last_artifact'] = str(out.relative_to(ROOT.parent))
    state['next_task'] = task['id']
    queue_changed = True

if queue_changed:
    QUEUE.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('WROTE', out)
print('ADVANCED' if memo else 'RETRY_REQUIRED')

#!/usr/bin/env python3
"""Collect exploratory evidence from the tracked Uthmani Quran corpus."""

import argparse
import hashlib
import json
import re
import subprocess
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

ROOT = Path(__file__).resolve().parent
QURAN_SOURCE = 'quran_uthmani'
QURAN_URL = 'https://api.alquran.cloud/v1/quran/quran-uthmani'
QURAN_PATH = Path('corpus/quran-uthmani.json')
CATALOG_SOURCES = {
    **{f'Q{number:03d}': QURAN_SOURCE for number in range(1, 20)},
    'Q020': 'verified_project_artifacts',
    'H001': 'hadith',
    'T001': 'tafsir',
    'C001': 'verified_project_artifacts',
    'X001': 'verified_project_artifacts',
    'M001': 'verified_project_artifacts',
    'B001': 'verified_project_artifacts',
    'QF001': 'verified_project_artifacts',
    'RF001': 'verified_project_artifacts',
}
TASK_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}')
TASK_STATUSES = {'pending', 'evidence_collected', 'processed', 'blocked'}
VERSE_REFERENCE = re.compile(r'(?<!\d)(\d{1,3}:\d{1,3})(?!\d)')
EVIDENCE_LINE = re.compile(r'^- \*\*(\d{1,3}:\d{1,3})\*\* — ', re.MULTILINE)
RESERVED_HEADING = re.compile(
    r'^## (Evidence|Machine synthesis|Provenance|Runtime note)\s*$', re.MULTILINE
)
DISCOVERY_LETTERS = str.maketrans({'ٱ': 'ا', 'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ى': 'ي'})
DISCOVERY_MARKS = set('ـ۞۩ۥۦ')
MODELS = ('qwen2.5:3b', 'qwen2.5:1.5b', 'qwen2.5:0.5b')


def required_source(task):
    return CATALOG_SOURCES.get(task['id'], task.get('evidence_source') or 'unspecified')


def research_audit(queue):
    return {
        'legacy_repair_required': [
            {'id': task['id'], 'required_source': required_source(task)}
            for task in queue
            if task['status'] == 'processed'
            and (type(task.get('evidence_count')) is not int or task['evidence_count'] < 1)
        ],
        'blocked': [
            {'id': task['id'], 'reason': task.get('failure'), 'required_source': required_source(task)}
            for task in queue
            if task['status'] == 'blocked'
        ],
    }


def discovery_text(text):
    """Ignore vocalization and ornamental marks for lexical discovery only."""
    normalized = unicodedata.normalize('NFC', text).translate(DISCOVERY_LETTERS)
    letters = (
        char for char in normalized
        if char not in DISCOVERY_MARKS and unicodedata.category(char) not in {'Mn', 'Me', 'Cf'}
    )
    return ' '.join(''.join(letters).split())


def acquire_candidates(path, keywords):
    if not isinstance(keywords, list):
        raise ValueError('research keywords must be a list')
    terms = [discovery_text(keyword) for keyword in keywords]
    terms = [term for term in terms if term]
    if not terms:
        raise ValueError('research requires at least one non-empty keyword')
    pattern = re.compile('|'.join(re.escape(term) for term in terms))

    raw = path.read_bytes()
    surahs = json.loads(raw)['data']['surahs']
    if not isinstance(surahs, list) or not surahs:
        raise ValueError('Quran corpus contains no surahs')
    hits = []
    seen = set()
    for surah in surahs:
        for ayah in surah['ayahs']:
            ref = surah['number'], ayah['numberInSurah']
            if not all(type(number) is int and number > 0 for number in ref) or ref in seen:
                raise ValueError('invalid or duplicate Quran verse reference')
            seen.add(ref)
            source_text = ayah['text']
            if pattern.search(discovery_text(source_text)) and len(hits) < 160:
                hits.append({
                    'surah': surah['number'],
                    'name': surah['name'],
                    'ayah': ayah['numberInSurah'],
                    'text': source_text,
                })
    if not seen:
        raise ValueError('Quran corpus contains no verses')
    return hits, hashlib.sha256(raw).hexdigest()


def evidence_refs_and_memo(artifact):
    evidence, _, synthesis = artifact.partition('\n## Machine synthesis\n')
    _, _, evidence = evidence.partition('\n## Evidence\n')
    memo, _, _ = synthesis.partition('\n## Provenance\n')
    return set(EVIDENCE_LINE.findall(evidence)), memo


def synthesize(task, candidates):
    prompt = (
        'أنت باحث مساعد في مشروع كتاب عن: ماذا يصنع الوحي في الإنسان؟\n'
        f"المهمة: {task['title']}\nالسؤال: {task['question']}\n"
        'افصل النص عن الملاحظة والفهم والاستنتاج، وبيّن حدود الأدلة. '
        'استخدم الآيات المرشحة فقط وأحل إليها بصيغة سورة:آية بأرقام 0–9. '
        'أحل إلى أرقام الآيات دون إعادة كتابة نصها فالنص موجود في الأدلة. '
        'اذكر ما يحتاج مصادر أخرى دون اختلاق إحالات أو إضافة حديث أو تفسير.\n'
        f'الآيات المرشحة:\n{json.dumps(candidates, ensure_ascii=False)}'
    )
    allowed_refs = {f"{item['surah']}:{item['ayah']}" for item in candidates}
    failure = 'local_model_unavailable'
    for model in MODELS:
        try:
            result = subprocess.run(
                ['ollama', 'run', model, prompt], text=True, capture_output=True, timeout=300
            )
        except FileNotFoundError:
            break
        except (OSError, subprocess.TimeoutExpired):
            continue
        memo = result.stdout.strip()
        if result.returncode or not memo:
            continue
        refs = set(VERSE_REFERENCE.findall(memo))
        if refs and refs <= allowed_refs and '\x1b' not in memo and not RESERVED_HEADING.search(memo):
            return memo, model, None
        failure = 'memo_citations_unverified'
    return None, None, failure


def write_text(path, content):
    with NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as output:
        staged = Path(output.name)
        try:
            output.write(content)
            output.close()
            staged.replace(path)
        finally:
            staged.unlink(missing_ok=True)


def write_json(path, value):
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def run_cycle(root, evidence_only=False, audit_only=False):
    queue_path = root / 'FREE_QUEUE.json'
    queue = json.loads(queue_path.read_text(encoding='utf-8'))
    if audit_only:
        print(json.dumps(research_audit(queue), ensure_ascii=False))
        return
    task = next((item for item in queue if item['status'] == 'pending'), None)
    if task is None and not evidence_only:
        task = next((item for item in queue if item['status'] == 'evidence_collected'), None)
    if task is None:
        print('No pending or evidence-collected tasks' if not evidence_only else 'No pending tasks')
        print(json.dumps(research_audit(queue), ensure_ascii=False))
        return

    task_id = task['id']
    if not TASK_ID.fullmatch(task_id):
        raise ValueError('invalid research task ID')
    print('TASK:', task_id, task['title'])
    state_path = root / 'STATE.json'
    state = json.loads(state_path.read_text(encoding='utf-8'))
    source = required_source(task)
    hits, corpus_hash, memo, model = [], None, None, None
    if source != QURAN_SOURCE:
        failure = 'required_source_unavailable'
    else:
        try:
            hits, corpus_hash = acquire_candidates(root / QURAN_PATH, task['keywords'])
        except OSError:
            failure = 'tracked_corpus_unavailable'
        except (KeyError, TypeError, ValueError):
            failure = 'corpus_or_query_invalid'
        else:
            failure = None if hits else 'no_candidate_evidence'

    visible_hits = hits[:60]
    if failure:
        task_status, synthesis_status = 'blocked', 'blocked'
        project_status, outcome = 'research_blocked', 'RESEARCH_BLOCKED'
    else:
        evidence_path = root / 'corpus' / f'{task_id}.json'
        write_json(evidence_path, hits)
        if not evidence_only:
            memo, model, failure = synthesize(task, visible_hits)
        if memo is not None:
            task_status, synthesis_status = 'processed', 'complete'
            project_status, outcome = 'running', 'ADVANCED'
        else:
            task_status = 'evidence_collected'
            synthesis_status = 'retryable' if failure else 'pending'
            project_status, outcome = 'synthesis_pending', 'EVIDENCE_COLLECTED_RETRYABLE'

    now = datetime.now(timezone.utc)
    runs = root / 'research' / 'runs'
    runs.mkdir(parents=True, exist_ok=True)
    artifact = runs / f"{now.strftime('%Y%m%dT%H%M%S%fZ')}-{task_id}.md"
    body = [f"# {task['title']}", '', f'**Run:** {now.isoformat()}', '',
            f'**Evidence hits:** {len(hits)}', '', '## Evidence', '']
    for hit in visible_hits:
        body.append(f"- **{hit['surah']}:{hit['ayah']}** — {hit['text']}")
    body.extend(['', '## Machine synthesis', ''])
    body.append(memo if memo is not None else f'Pending. No synthesis recorded. Status: `{failure or "evidence_only"}`.')
    body.extend(['', '## Provenance', '', f'- Required evidence source: `{source}`.'])
    if corpus_hash is not None:
        body.extend([
            f'- Primary text source: alQuran.cloud Uthmani corpus ({QURAN_URL}).',
            f'- Tracked corpus: `book/{QURAN_PATH.as_posix()}`. SHA-256: `{corpus_hash}`.',
            '- Normalized forms were used only for matching. Evidence preserves the original text.',
        ])
    body.extend([
        '- No hadith, tafsir, or historical claim was added as verified evidence.',
        '- Candidate evidence and machine synthesis require downstream scholarly verification.',
    ])
    write_text(artifact, '\n'.join(body) + '\n')

    relative_artifact = artifact.relative_to(root.parent).as_posix()
    task.update({
        'last_attempt': now.isoformat(),
        'last_artifact': relative_artifact,
        'required_evidence_source': source,
        'evidence_count': len(hits),
        'status': task_status,
        'synthesis_status': synthesis_status,
    })
    if corpus_hash is not None:
        task['source_sha256'] = corpus_hash
    else:
        task.pop('source_sha256', None)
    if failure:
        task['failure'] = failure
    else:
        task.pop('failure', None)
    if model is not None:
        state['last_model'] = model
    next_task = next(
        (item['id'] for status in ('pending', 'evidence_collected')
         for item in queue if item['status'] == status),
        None,
    )
    state.update({
        'status': project_status,
        'last_run': now.isoformat(),
        'last_task': task_id,
        'last_artifact': relative_artifact,
        'next_task': next_task,
    })
    write_json(state_path, state)
    write_json(queue_path, queue)
    print('WROTE', artifact)
    print(f'{outcome}: {failure}' if failure else outcome)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--audit', action='store_true', help='report legacy and blocked tasks without writes')
    mode.add_argument(
        '--evidence-only', action='store_true', help='checkpoint one pending task without a model'
    )
    args = parser.parse_args()
    run_cycle(ROOT, evidence_only=args.evidence_only, audit_only=args.audit)


if __name__ == '__main__':
    main()

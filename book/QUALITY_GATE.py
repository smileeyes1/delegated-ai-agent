#!/usr/bin/env python3
"""Check active research checkpoints against the selected artifact and source."""

import json
import re
from pathlib import Path, PurePosixPath

if __package__:
    from . import free_autonomous_research as research
else:
    import free_autonomous_research as research

ROOT = Path(__file__).resolve().parent
CHECKPOINT_STATES = {'evidence_collected', 'processed'}
ARTIFACT_HEADINGS = ('## Evidence', '## Machine synthesis', '## Provenance')


def local_file(root, relative):
    path = root / relative
    if path.resolve(strict=True) != root / relative or not path.is_file():
        raise ValueError('checkpoint path must select a regular file inside the book')
    return path


def selected_artifact(root, task):
    artifact = task.get('last_artifact')
    if not isinstance(artifact, str):
        raise ValueError('checkpoint has no selected artifact')
    relative = PurePosixPath(artifact)
    filename = r'[0-9]{8}T[0-9]{6}(?:[0-9]{6})?Z-' + re.escape(task['id']) + r'\.md'
    if (
        relative.parent != PurePosixPath(root.name, 'research', 'runs')
        or relative.as_posix() != artifact
        or not re.fullmatch(filename, relative.name)
    ):
        raise ValueError('selected artifact path does not belong to this task')
    return local_file(root, Path('research', 'runs', relative.name))


def verify_checkpoint(root, task):
    count = task.get('evidence_count')
    if type(count) is not int or count < 1:
        raise ValueError('checkpoint lacks a positive evidence count')
    if research.required_source(task) != research.QURAN_SOURCE:
        raise ValueError('this source has no verified checkpoint adapter')
    if task.get('required_evidence_source') != research.QURAN_SOURCE:
        raise ValueError('checkpoint lacks the required Quran source identity')

    artifact = selected_artifact(root, task).read_text(encoding='utf-8')
    candidate_path = local_file(root, Path('corpus', task['id'] + '.json'))
    candidates = json.loads(candidate_path.read_text(encoding='utf-8'))
    if not isinstance(candidates, list) or len(candidates) != count:
        raise ValueError('candidate file count differs from the checkpoint')
    canonical_path = local_file(root, research.QURAN_PATH)
    expected, digest = research.acquire_candidates(
        canonical_path, task['keywords'], task.get('context_references', ()),
    )
    if candidates != expected or any(
        type(row[key]) is not int for row in candidates for key in ('surah', 'ayah')
    ):
        raise ValueError('candidate rows differ from the tracked corpus query')
    if task.get('source_sha256') != digest:
        raise ValueError('checkpoint source fingerprint differs from the tracked corpus')

    lines = artifact.splitlines()
    headings = [line for line in lines if line in ARTIFACT_HEADINGS]
    if tuple(headings) != ARTIFACT_HEADINGS:
        raise ValueError('artifact has missing, repeated, or unordered sections')
    evidence_at, synthesis_at, provenance_at = (lines.index(heading) for heading in ARTIFACT_HEADINGS)
    displayed_counts = [line for line in lines[:evidence_at] if line.startswith('**Evidence hits:**')]
    if displayed_counts != [f'**Evidence hits:** {count}']:
        raise ValueError('artifact evidence count differs from the checkpoint')
    visible = candidates[:60]
    expected_lines = [f"- **{row['surah']}:{row['ayah']}** — {row['text']}" for row in visible]
    visible_lines = [line for line in lines[evidence_at + 1:synthesis_at] if line.strip()]
    if visible_lines != expected_lines:
        raise ValueError('visible evidence differs from the first 60 candidate rows')

    provenance = [line for line in lines[provenance_at + 1:] if line.strip()]
    required_provenance = [
        f'- Required evidence source: `{research.QURAN_SOURCE}`.',
        f'- Primary text source: alQuran.cloud Uthmani corpus ({research.QURAN_URL}).',
        f'- Tracked corpus: `book/{research.QURAN_PATH.as_posix()}`. SHA-256: `{digest}`.',
        '- Normalized forms were used only for matching. Evidence preserves the original text.',
    ]
    if task.get('context_references'):
        required_provenance.append(
            '- The opening passages are the explicitly selected context references for this question.'
        )
    required_provenance.extend([
        '- No hadith, tafsir, or historical claim was added as verified evidence.',
        '- Candidate evidence and machine synthesis require downstream scholarly verification.',
    ])
    if provenance != required_provenance:
        raise ValueError('artifact lacks its exact source and exploratory provenance')

    refs, memo = research.evidence_refs_and_memo(artifact)
    cited = set(research.VERSE_REFERENCE.findall(memo))
    if cited - refs:
        raise ValueError('model cited references outside the visible evidence')
    status = task.get('synthesis_status')
    failure = task.get('failure')
    if task['status'] == 'processed':
        if status != 'complete' or failure or not memo.strip() or not cited or '\x1b' in memo:
            raise ValueError('processed task requires a completed memo with backed citations')
    else:
        if status == 'pending' and failure is None:
            reason = 'evidence_only'
        elif status == 'retryable' and isinstance(failure, str) and failure.strip():
            reason = failure
        else:
            raise ValueError('evidence checkpoint requires an explicit synthesis status')
        if memo.strip() != f'Pending. No synthesis recorded. Status: `{reason}`.':
            raise ValueError('evidence checkpoint must contain the recorded pending status')


def validate_quality(root):
    root = root.resolve(strict=True)
    state = json.loads((root / 'STATE.json').read_text(encoding='utf-8'))
    queue = json.loads((root / 'FREE_QUEUE.json').read_text(encoding='utf-8'))
    errors = []
    if not isinstance(state, dict) or not {'project', 'status', 'next_task'} <= state.keys():
        errors.append('invalid project state')
    elif state.get('scholarly_status') not in (None, 'exploratory_unverified'):
        errors.append('unexpected scholarly status escalation')
    if not isinstance(queue, list) or not queue:
        return errors + ['queue is empty or invalid']

    seen = set()
    for task in queue:
        if not isinstance(task, dict):
            errors.append('queue entry must be an object')
            continue
        task_id = task.get('id')
        if not isinstance(task_id, str) or not research.TASK_ID.fullmatch(task_id):
            errors.append('invalid queue task ID')
            continue
        if task_id in seen:
            errors.append(f'{task_id}: duplicate queue task ID')
            continue
        seen.add(task_id)
        status = task.get('status')
        keywords = task.get('keywords')
        if (
            not isinstance(status, str) or status not in research.TASK_STATUSES
            or not all(isinstance(task.get(key), str) and task[key].strip() for key in ('title', 'question'))
            or not isinstance(keywords, list) or not keywords
            or not all(isinstance(keyword, str) and keyword.strip() for keyword in keywords)
        ):
            errors.append(f'{task_id}: invalid queue fields')
            continue
        if status == 'blocked':
            reason = task.get('failure')
            if not isinstance(reason, str) or not reason.strip():
                errors.append(f'{task_id}: blocked task lacks a reason')
        if status in CHECKPOINT_STATES:
            try:
                verify_checkpoint(root, task)
            except (OSError, KeyError, TypeError, ValueError) as error:
                errors.append(f'{task_id}: {error}')
    return errors


def main():
    try:
        errors = validate_quality(ROOT)
    except (OSError, ValueError) as error:
        errors = [str(error)]
    if errors:
        print('QUALITY_GATE_FAIL')
        for error in errors:
            print('-', error)
        return 1
    print('QUALITY_GATE_PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

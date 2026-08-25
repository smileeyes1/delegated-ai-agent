"""Generate the next actionable knowledge task from durable project state.

This deterministic layer proves task autonomy/orchestration. It does not
fabricate research; research acquisition remains an explicit adapter.
"""
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
factory = json.loads((ROOT / 'FACTORY_STATE.json').read_text(encoding='utf-8'))
chapter = json.loads((ROOT / 'CHAPTER_01_STATE.json').read_text(encoding='utf-8'))

if chapter.get('verified_evidence_count', 0) == 0:
    task = {
        'id': 'research.chapter01.verify_primary_evidence',
        'kind': 'research',
        'priority': 'highest',
        'reason': 'Chapter 01 has candidate evidence but no verified evidence.',
        'action': 'collect_and_verify_primary_source_records',
    }
elif not chapter.get('counter_evidence_pass'):
    task = {
        'id': 'research.chapter01.counter_evidence',
        'kind': 'adversarial_research',
        'priority': 'highest',
        'reason': 'Verified evidence exists but counter-evidence pass is incomplete.',
        'action': 'search_material_counter_evidence_and_alternative_interpretations',
    }
else:
    task = {
        'id': 'synthesis.chapter01.argument_map',
        'kind': 'synthesis',
        'priority': 'highest',
        'reason': 'Evidence and counter-evidence gates are complete.',
        'action': 'build_traceable_argument_map',
    }

state = {
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'mode': 'autonomous',
    'task': task,
    'human_prompt_required': False,
}
(ROOT / 'NEXT_TASK.json').write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(state, ensure_ascii=False))

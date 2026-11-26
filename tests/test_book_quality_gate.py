import contextlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from book import QUALITY_GATE as gate
from book import free_autonomous_research as research


class ResearchQualityGateTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'book'
        self.queue = self.root / 'FREE_QUEUE.json'
        self.corpus = self.root / research.QURAN_PATH
        self.candidates = self.corpus.with_name('Q001.json')
        self.corpus.parent.mkdir(parents=True)
        self.task = {
            'id': 'Q001', 'status': 'pending', 'title': 'الهداية',
            'question': 'كيف يصف القرآن الهداية؟', 'keywords': ['هدى'],
        }
        self.verse = 'هُدًۭى لِّلْمُتَّقِينَ'
        research.write_json(self.queue, [self.task])
        research.write_json(self.root / 'STATE.json', {
            'project': 'كتاب', 'status': 'running', 'next_task': 'Q001',
            'scholarly_status': 'exploratory_unverified',
        })
        research.write_json(self.corpus, {
            'data': {'surahs': [{
                'number': 2, 'name': 'البقرة', 'ayahs': [
                    {'numberInSurah': number, 'text': self.verse} for number in range(1, 62)
                ],
            }]},
        })

    def finish_checkpoint(self, *, evidence_only=True):
        response = subprocess.CompletedProcess([], 0, 'ملاحظة مرتبطة بالشاهد 2:2', '')
        with contextlib.redirect_stdout(io.StringIO()):
            with patch.object(research.subprocess, 'run', return_value=response):
                research.run_cycle(self.root, evidence_only=evidence_only)
        self.task = json.loads(self.queue.read_text(encoding='utf-8'))[0]
        return self.root.parent / self.task['last_artifact']

    def test_accepts_evidence_checkpoint_and_citation_backed_processed_task(self):
        artifact = self.finish_checkpoint()
        self.assertEqual(self.task['evidence_count'], 61)
        self.assertIn('**2:60**', artifact.read_text(encoding='utf-8'))
        self.assertNotIn('**2:61**', artifact.read_text(encoding='utf-8'))
        self.assertEqual(gate.validate_quality(self.root), [])
        self.finish_checkpoint(evidence_only=False)
        self.assertEqual(self.task['status'], 'processed')
        self.assertEqual(gate.validate_quality(self.root), [])

    def test_rejects_wrong_positive_count(self):
        self.finish_checkpoint()
        self.task['evidence_count'] += 1
        research.write_json(self.queue, [self.task])
        self.assertEqual(gate.validate_quality(self.root), [
            'Q001: candidate file count differs from the checkpoint',
        ])

    def test_rejects_forged_evidence_even_if_visible_text_and_json_agree(self):
        artifact = self.finish_checkpoint()
        raw = json.loads(self.candidates.read_text(encoding='utf-8'))
        raw[0]['text'] = 'نص معدل'
        research.write_json(self.candidates, raw)
        text = artifact.read_text(encoding='utf-8').replace(self.verse, 'نص معدل', 1)
        artifact.write_text(text, encoding='utf-8')
        self.assertEqual(gate.validate_quality(self.root), [
            'Q001: candidate rows differ from the tracked corpus query',
        ])

    def test_rejects_non_integer_reference_even_when_numerically_equal(self):
        self.finish_checkpoint()
        raw = json.loads(self.candidates.read_text(encoding='utf-8'))
        raw[-1]['ayah'] = float(raw[-1]['ayah'])
        research.write_json(self.candidates, raw)
        self.assertEqual(gate.validate_quality(self.root), [
            'Q001: candidate rows differ from the tracked corpus query',
        ])

    def test_rejects_source_digest_that_disagrees_with_tracked_corpus(self):
        artifact = self.finish_checkpoint()
        source_hash = self.task['source_sha256']
        self.task['source_sha256'] = 'a' * 64
        research.write_json(self.queue, [self.task])
        text = artifact.read_text(encoding='utf-8').replace(source_hash, 'a' * 64)
        artifact.write_text(text, encoding='utf-8')
        self.assertEqual(gate.validate_quality(self.root), [
            'Q001: checkpoint source fingerprint differs from the tracked corpus',
        ])

    def test_rejects_displayed_citation_outside_the_first_60_rows(self):
        artifact = self.finish_checkpoint()
        text = artifact.read_text(encoding='utf-8').replace('**2:60**', '**2:61**')
        artifact.write_text(text, encoding='utf-8')
        self.assertEqual(gate.validate_quality(self.root), [
            'Q001: visible evidence differs from the first 60 candidate rows',
        ])

    def test_rejects_prose_appended_after_the_memo_boundary(self):
        artifact = self.finish_checkpoint(evidence_only=False)
        initial = artifact.read_text(encoding='utf-8')
        artifact.write_text(initial + '\nإحالة خارجة عن الشواهد 2:61\n', encoding='utf-8')
        self.assertEqual(gate.validate_quality(self.root), [
            'Q001: artifact lacks its exact source and exploratory provenance',
        ])

    def test_rejects_memo_with_unbacked_citation_or_no_citation(self):
        artifact = self.finish_checkpoint(evidence_only=False)
        initial = artifact.read_text(encoding='utf-8')
        for replacement, error in (
            ('2:61', 'Q001: model cited references outside the visible evidence'),
            ('بلا إحالة', 'Q001: processed task requires a completed memo with backed citations'),
        ):
            with self.subTest(replacement=replacement):
                artifact.write_text(
                    initial.replace('بالشاهد 2:2', f'بالشاهد {replacement}'), encoding='utf-8',
                )
                self.assertEqual(gate.validate_quality(self.root), [error])

    def test_rejects_another_tasks_selected_artifact_without_glob_fallback(self):
        artifact = self.finish_checkpoint()
        unrelated = artifact.with_name(artifact.name.replace('Q001.md', 'Q002.md'))
        shutil.copyfile(artifact, unrelated)
        self.task['last_artifact'] = unrelated.relative_to(self.root.parent).as_posix()
        research.write_json(self.queue, [self.task])
        self.assertEqual(gate.validate_quality(self.root), [
            'Q001: selected artifact path does not belong to this task',
        ])

    def test_rejects_selected_artifact_symlink(self):
        artifact = self.finish_checkpoint()
        target = self.root.parent / 'unrelated.md'
        artifact.rename(target)
        artifact.symlink_to(target)
        self.assertEqual(gate.validate_quality(self.root), [
            'Q001: checkpoint path must select a regular file inside the book',
        ])

    def test_pending_legacy_metadata_is_preserved_and_blocked_needs_reason(self):
        self.task['last_artifact'] = 'old checkpoint'
        self.task['evidence_count'] = 0
        research.write_json(self.queue, [self.task])
        self.assertEqual(gate.validate_quality(self.root), [])
        self.task['status'] = 'blocked'
        research.write_json(self.queue, [self.task])
        self.assertEqual(gate.validate_quality(self.root), ['Q001: blocked task lacks a reason'])
        self.task['failure'] = 'required_source_unavailable'
        research.write_json(self.queue, [self.task])
        self.assertEqual(gate.validate_quality(self.root), [])

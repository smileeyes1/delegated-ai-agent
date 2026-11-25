import contextlib
import hashlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from book import free_autonomous_research as research


class ResearchIntakeTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.book = Path(temp.name) / 'book'
        self.corpus = self.book / research.QURAN_PATH
        self.corpus.parent.mkdir(parents=True)
        self.queue = self.book / 'FREE_QUEUE.json'
        self.state = self.book / 'STATE.json'
        self.verse = 'ذَٰلِكَ ٱلْكِتَٰبُ لَا رَيْبَ ۛ فِيهِ ۛ هُدًۭى لِّلْمُتَّقِينَ'
        research.write_json(self.corpus, {
            'data': {'surahs': [{
                'name': 'البقرة', 'number': 2,
                'ayahs': [{'numberInSurah': 2, 'text': self.verse}],
            }]},
        })
        research.write_json(self.state, {'project': 'كتاب', 'status': 'running'})

    def task(self, task_id='Q001', status='pending', keywords=None):
        return {
            'id': task_id, 'status': status,
            'title': 'الهداية', 'question': 'ما أثر هدى الوحي؟',
            'keywords': ['هدى'] if keywords is None else keywords,
        }

    def execute(self, **kwargs):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            research.run_cycle(self.book, **kwargs)
        return output.getvalue()

    def stored_task(self):
        return json.loads(self.queue.read_text(encoding='utf-8'))[0]

    def test_vocalized_verse_matches_unvocalized_probe_without_mutation(self):
        raw = self.corpus.read_bytes()
        hits, checksum = research.acquire_candidates(self.corpus, ['هدى'])
        self.assertEqual(hits, [{'surah': 2, 'name': 'البقرة', 'ayah': 2, 'text': self.verse}])
        self.assertEqual(checksum, hashlib.sha256(raw).hexdigest())
        self.assertEqual(self.corpus.read_bytes(), raw)

    def test_real_tracked_corpus_matches_legacy_purification_query(self):
        corpus = research.ROOT / research.QURAN_PATH
        queue = json.loads((research.ROOT / 'FREE_QUEUE.json').read_text(encoding='utf-8'))
        task = next(item for item in queue if item['id'] == 'Q002')
        hits, checksum = research.acquire_candidates(corpus, task['keywords'])
        self.assertIn((2, 129), {(item['surah'], item['ayah']) for item in hits})
        self.assertEqual(checksum, hashlib.sha256(corpus.read_bytes()).hexdigest())
        original = json.loads(corpus.read_bytes())['data']['surahs'][1]['ayahs'][128]['text']
        self.assertEqual(hits[0]['text'], original)

    def test_zero_candidates_stop_before_synthesis_and_preserve_last_evidence(self):
        research.write_json(self.queue, [self.task(keywords=['مسبار١'])])
        cached = self.corpus.parent / 'Q001.json'
        cached.write_text('previously verified bytes', encoding='utf-8')
        with patch.object(research, 'synthesize') as synthesize:
            result = self.execute()
        synthesize.assert_not_called()
        self.assertIn('RESEARCH_BLOCKED: no_candidate_evidence', result)
        self.assertEqual(self.stored_task()['status'], 'blocked')
        self.assertEqual(self.stored_task()['evidence_count'], 0)
        self.assertEqual(cached.read_text(encoding='utf-8'), 'previously verified bytes')

    def test_missing_tracked_corpus_reports_block_without_falling_back_to_network(self):
        research.write_json(self.queue, [self.task()])
        self.corpus.unlink()
        with patch.object(research, 'synthesize') as synthesize:
            result = self.execute()
        synthesize.assert_not_called()
        self.assertIn('RESEARCH_BLOCKED: tracked_corpus_unavailable', result)
        self.assertEqual(self.stored_task()['status'], 'blocked')
        self.assertFalse(self.corpus.exists())

    def test_failed_checkpoint_replacement_keeps_previous_bytes(self):
        before = self.state.read_bytes()
        with patch.object(Path, 'replace', side_effect=PermissionError):
            with self.assertRaises(PermissionError):
                research.write_json(self.state, {'status': 'new'})
        self.assertEqual(self.state.read_bytes(), before)
        self.assertEqual(set(self.book.iterdir()), {self.state, self.corpus.parent})

    def test_external_and_downstream_tasks_do_not_use_quran_hits_as_evidence(self):
        sources = {'H001': 'hadith', 'T001': 'tafsir', 'Q020': 'verified_project_artifacts'}
        for task_id, source in sources.items():
            with self.subTest(task=task_id):
                task = self.task(task_id)
                task['evidence_source'] = research.QURAN_SOURCE
                research.write_json(self.queue, [task])
                with patch.object(research, 'acquire_candidates') as acquire:
                    self.assertIn('RESEARCH_BLOCKED: required_source_unavailable', self.execute())
                acquire.assert_not_called()
                self.assertEqual(self.stored_task()['required_evidence_source'], source)

    def test_evidence_can_checkpoint_without_a_model(self):
        research.write_json(self.queue, [self.task()])
        with patch.object(research, 'synthesize') as synthesize:
            self.assertIn('EVIDENCE_COLLECTED_RETRYABLE', self.execute(evidence_only=True))
        synthesize.assert_not_called()
        task = self.stored_task()
        self.assertEqual(task['status'], 'evidence_collected')
        self.assertEqual(task['synthesis_status'], 'pending')
        self.assertEqual(task['evidence_count'], 1)
        artifact = (self.book.parent / task['last_artifact']).read_text(encoding='utf-8')
        refs, _ = research.evidence_refs_and_memo(artifact)
        self.assertEqual(refs, {'2:2'})
        self.assertIn(self.verse, artifact)
        self.assertIn(task['source_sha256'], artifact)

    def test_valid_citations_allow_exploratory_synthesis_after_evidence_checkpoint(self):
        research.write_json(self.queue, [self.task()])
        self.execute(evidence_only=True)
        reply = subprocess.CompletedProcess([], 0, 'ملاحظة أولية على 2:2', '')
        with patch.object(research.subprocess, 'run', return_value=reply) as model:
            self.assertIn('ADVANCED', self.execute())
        self.assertEqual(self.stored_task()['status'], 'processed')
        self.assertIn(self.verse, model.call_args.args[0][-1])

    def test_model_without_backed_citation_cannot_finish_task(self):
        for memo in ('مذكرة بلا إحالة', 'المثال 2:2 و**99:9**'):
            with self.subTest(memo=memo):
                research.write_json(self.queue, [self.task()])
                reply = subprocess.CompletedProcess([], 0, memo, '')
                with patch.object(research.subprocess, 'run', return_value=reply):
                    self.assertIn('EVIDENCE_COLLECTED_RETRYABLE: memo_citations_unverified',
                                  self.execute())
                task = self.stored_task()
                self.assertEqual(task['status'], 'evidence_collected')
                self.assertEqual(task['evidence_count'], 1)
                artifact = (self.book.parent / task['last_artifact']).read_text(encoding='utf-8')
                self.assertNotIn(memo, artifact)

    def test_legacy_audit_lists_affected_tasks_without_reopening_them(self):
        task = self.task(status='processed')
        task['evidence_count'] = 0
        research.write_json(self.queue, [task])
        before = self.queue.read_bytes(), self.state.read_bytes()
        report = json.loads(self.execute(audit_only=True))
        self.assertEqual(report['legacy_repair_required'],
                         [{'id': 'Q001', 'required_source': research.QURAN_SOURCE}])
        self.assertIn('No pending or evidence-collected tasks', self.execute())
        self.assertEqual(before, (self.queue.read_bytes(), self.state.read_bytes()))

    def test_archive_validator_does_not_count_bold_memo_references_as_evidence(self):
        artifact = (
            '# Draft\n\n## Evidence\n- **2:2** — original\n'
            '## Machine synthesis\n**99:9**\n## Provenance\n'
        )
        refs, memo = research.evidence_refs_and_memo(artifact)
        self.assertEqual(refs, {'2:2'})
        self.assertEqual(set(research.VERSE_REFERENCE.findall(memo)) - refs, {'99:9'})

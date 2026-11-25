import hashlib
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
from urllib.error import URLError

from book import CHAPTER_01_AUTONOMOUS_PIPELINE as pipeline
from book import CHAPTER_01_CRITIC as critic
from book.chapter_sources import quranpedia_text, verify_verse


BASMALAH = 'بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ'
# Exact 2:2 strings from the existing public Tanzil and Quranpedia endpoints.
TANZIL_VERSE = 'ذَٰلِكَ ٱلْكِتَٰبُ لَا رَيْبَ ۛ فِيهِ ۛ هُدًۭى لِّلْمُتَّقِينَ'
QURANPEDIA_VERSE = 'ذَٰلِكَ ٱلۡكِتَٰبُ لَا رَيۡبَۛ فِيهِۛ هُدࣰى لِّلۡمُتَّقِينَ'


class ChapterSourceTests(unittest.TestCase):
    def test_known_edition_variations(self):
        self.assertTrue(verify_verse('2:2', TANZIL_VERSE, QURANPEDIA_VERSE, BASMALAH))
        self.assertTrue(verify_verse('16:89', 'شَىْءٍۢ', 'شَيۡءࣲ', BASMALAH))
        self.assertTrue(verify_verse('2:185', 'لِتُكْمِلُوا۟', 'لِتُكۡمِلُواۡ', BASMALAH))
        self.assertTrue(verify_verse('14:1', BASMALAH + ' الٓر', 'الٓر', BASMALAH))
        self.assertFalse(verify_verse('14:2', BASMALAH + ' الٓر', 'الٓر', BASMALAH))
        self.assertFalse(verify_verse('1:1', BASMALAH, '', BASMALAH))

    def test_text_changes_are_not_normalized_away(self):
        for changed in (
            QURANPEDIA_VERSE.replace('رَي', 'رِي'),
            QURANPEDIA_VERSE.replace('لِّلۡمُتَّقِينَ', 'لِلۡمُتَّقِينَ'),
            QURANPEDIA_VERSE.replace('لَا رَ', 'لَارَ'),
            QURANPEDIA_VERSE.replace('هُدࣰى', 'هُدࣰي'),
            QURANPEDIA_VERSE.replace('لَا', 'لَأ'),
            QURANPEDIA_VERSE.replace('هُدࣰى', ''),
        ):
            with self.subTest(changed=changed):
                self.assertFalse(verify_verse('2:2', TANZIL_VERSE, changed, BASMALAH))

    def test_quranpedia_verse_identity(self):
        response = {'surah': '2', 'number': 2, 'number_in_hafs': [2], 'text': QURANPEDIA_VERSE}
        self.assertEqual(quranpedia_text('2:2', response), QURANPEDIA_VERSE)
        with self.assertRaisesRegex(ValueError, 'Unexpected Quranpedia verse response'):
            quranpedia_text('2:3', response)
        with self.assertRaisesRegex(ValueError, 'Unexpected Quranpedia verse response'):
            quranpedia_text('2:2', dict(response, number_in_hafs=[2, 3]))

    def test_tanzil_parser_checks_complete_export_and_retains_raw_text(self):
        raw = (pipeline.DATA / 'tanzil-uthmani.txt').read_bytes()
        with patch.object(pipeline, 'get', return_value=raw):
            verses, fetched = pipeline.load_tanzil()
        self.assertEqual(verses['2:2'], TANZIL_VERSE)
        self.assertEqual(fetched, raw)
        with patch.object(pipeline, 'get', return_value=b'1|1|partial source'):
            with self.assertRaisesRegex(ValueError, 'Incomplete Tanzil export'):
                pipeline.load_tanzil()

    def test_failed_research_does_not_replace_checkpoint(self):
        verses = {'1:1': BASMALAH, '2:2': TANZIL_VERSE, '2:3': 'ضَلَال'}
        raw = b'Tanzil source bytes'
        source = {'url': 'https://api.quranpedia.net/v1/mushafs/1/2/2', 'sha256': 'c' * 64}
        with (
            TemporaryDirectory() as temp,
            patch.object(pipeline, 'REFS', ['2:2']),
            patch.object(pipeline, 'load_tanzil', return_value=(verses, raw)),
            patch.object(pipeline, 'qpedia', return_value=(QURANPEDIA_VERSE, source)) as provider,
            patch.object(pipeline, 'tafsir', return_value={}) as fetch_tafsir,
        ):
            data_dir = Path(temp)
            with redirect_stdout(StringIO()):
                self.assertEqual(pipeline.run(data_dir), 0)
            checkpoint = {p.name: p.read_bytes() for p in data_dir.iterdir()}
            evidence = json.loads(checkpoint['chapter_01_autonomous_research.json'])
            self.assertEqual(evidence['source']['sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual(evidence['records'][0]['primary_text'], TANZIL_VERSE)
            self.assertEqual(evidence['records'][0]['quranpedia_text'], QURANPEDIA_VERSE)
            self.assertEqual(evidence['records'][0]['quranpedia_source'], source)
            self.assertEqual(critic.review(evidence, {'required_count': 1, 'verified_count': 1})['status'], 'PASS')
            self.assertEqual(critic.review(evidence, {})['status'], 'BLOCKED')

            damaged = QURANPEDIA_VERSE.replace('رَي', 'رِي')
            provider.return_value = (damaged, source)
            with redirect_stdout(StringIO()) as output:
                self.assertEqual(pipeline.run(data_dir), 2)
            self.assertEqual(json.loads(output.getvalue())['mismatches'], ['2:2'])
            self.assertEqual({p.name: p.read_bytes() for p in data_dir.iterdir()}, checkpoint)

            provider.side_effect = URLError('source unavailable')
            with redirect_stdout(StringIO()) as output:
                self.assertEqual(pipeline.run(data_dir), 2)
            self.assertEqual(json.loads(output.getvalue())['reason'], 'SOURCE_ACQUISITION')
            self.assertEqual({p.name: p.read_bytes() for p in data_dir.iterdir()}, checkpoint)
            fetch_tafsir.assert_called_once_with('2:2')

            evidence['records'][0]['quranpedia_text'] = damaged
            result = critic.review(evidence, {'required_count': 1, 'verified_count': 1})
            self.assertIn('TEXT_CROSSCHECK_FAILURE:2:2', result['issues'])


if __name__ == '__main__':
    unittest.main()

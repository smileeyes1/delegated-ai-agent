from hashlib import sha256
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'book' / 'research' / 'audits' / 'q003-20261126.json'


class Q003IncidentTests(unittest.TestCase):
    def test_withdrawn_memo_and_corrected_quotes_match_pinned_sources(self):
        report = json.loads(AUDIT.read_bytes())
        self.assertEqual(report['status'], 'legacy_synthesis_withdrawn')
        self.assertEqual(report['historical_evidence_hits'], 0)
        self.assertFalse(report['interpretation_verified'])
        self.assertFalse(report['release_eligible'])

        correction = (ROOT / report['correction']['path']).read_bytes()
        self.assertEqual(sha256(correction).hexdigest(), report['correction']['sha256'])
        text = correction.decode()
        self.assertIn('**Evidence hits:** 0', text)
        memo = text.split('\n## Machine synthesis\n', 1)[1].split('\n## Provenance\n', 1)[0]
        self.assertIn('سُحبت المذكرة الأصلية', memo)
        self.assertNotRegex(memo, r'\b\d{1,3}:\d{1,3}\b')
        self.assertNotIn('\\u001b', text)
        self.assertNotIn('\x1b', text)

        corpus = (ROOT / report['source']['path']).read_bytes()
        self.assertEqual(sha256(corpus).hexdigest(), report['source']['sha256'])
        verses = {
            f"{surah['number']}:{ayah['numberInSurah']}": ayah['text']
            for surah in json.loads(corpus)['data']['surahs'] for ayah in surah['ayahs']
        }
        quotes = dict(re.findall(r'^### (\d+:\d+)\n\n> (.+)$', text, re.MULTILINE))
        self.assertEqual(quotes, {ref: verses[ref] for ref in ('39:42', '57:28', '24:32')})
        self.assertEqual(quotes, {row['ref']: row['source_text'] for row in report['references']})
        self.assertTrue(all(not row['original_quote_matches_source'] for row in report['references']))
        self.assertEqual(
            {row['ref']: row['disposition'] for row in report['references']},
            {'39:42': 'reject_as_direct_candidate', '57:28': 'new_candidate_only',
             '24:32': 'reject_as_direct_candidate'},
        )


if __name__ == '__main__':
    unittest.main()

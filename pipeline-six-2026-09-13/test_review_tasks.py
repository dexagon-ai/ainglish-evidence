"""Offline tests for generated review/navigation and source-matched study artifacts."""
from collections import Counter
import csv
import json
from pathlib import Path
import re
import unittest

HERE = Path(__file__).resolve().parent


class ReviewArtifacts(unittest.TestCase):
    def test_sanction_complete_nonoverlapping_coverage_without_acceptance(self):
        plan = json.loads((HERE / 'sanction-review-coverage.json').read_text())
        ids = [i for c in plan['chunks'] for i in c['ids']]
        self.assertEqual((len(ids), len(set(ids))), (64, 64))
        self.assertEqual(len(plan['chunks']), 8)
        self.assertEqual(plan['accepted_items'], 0)
        self.assertTrue(plan['full_packet_hold'])
        for chunk in plan['chunks']:
            text = (HERE / chunk['file']).read_text()
            self.assertEqual(len(chunk['ids']), 8)
            self.assertTrue(all(f'## {i}' in text for i in chunk['ids']))

    def test_rent_all_scores_retained(self):
        with (HERE / 'rent-score-navigation.csv').open() as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 64)
        self.assertEqual(len({r['item_id'] for r in rows}), 64)
        counts = Counter(r['direction'] for r in rows if r['entry_loaded_correct'] == 'True')
        self.assertEqual(counts, {'rent-borrow': 31, 'rent-lend': 18})

    def test_source_census_and_no_complete_pair_reuse(self):
        directory = HERE / 'remain-source-matched'
        source = [r for r in json.loads((directory / 'remain-source-items.json').read_text()) if not r.get('calibration')]
        fresh = [r for r in json.loads((directory / 'remain-fresh-items.json').read_text()) if not r.get('calibration')]
        axes = ('domain', 'form', 'probe', 'pattern')
        self.assertEqual(Counter(tuple(r[a] for a in axes) for r in source),
                         Counter(tuple(r['strata'][a] for a in axes) for r in fresh))
        self.assertFalse({(r['english'], r['ainglish']) for r in source} &
                         {(r['english'], r['ainglish']) for r in fresh})
        self.assertEqual(len(fresh), 128)
        self.assertEqual(len({r['strata']['world_id'] for r in fresh}), 128)

    def test_fresh_keys_derived_from_visible_text(self):
        path = HERE / 'remain-source-matched/remain-fresh-items.json'
        for row in json.loads(path.read_text()):
            if row.get('calibration'):
                continue
            with self.subTest(item=row['id']):
                text, question = row['ainglish'], row['question']
                stock = ' remain-in(' in text
                count = int(re.search(r'Exactly (\d+) ', text).group(1))
                if 'blue access slot' in question:
                    expected = (f'Blue slots: {count}; amber cards: unknown.' if stock else
                                f'Blue slots: unknown; amber cards: {count}.')
                    self.assertIn(f'exactly {count} distinct ', row['english'].lower())
                else:
                    state = 'initially inside.' in question
                    distinct_exit = False
                    for hour, minute, verb in re.findall(r'At (\d\d):(\d\d) the individual (enters|exits)', question):
                        t = int(hour) * 60 + int(minute)
                        self.assertNotEqual(state, verb == 'enters')
                        if verb == 'exits' and 560 <= t < 605:
                            distinct_exit = True
                        if t <= 605:
                            state = verb == 'enters'
                    value = int(state if stock else distinct_exit)
                    expected = '1 member' if value else '0 members'
                self.assertEqual(row['answer'], expected)
                self.assertEqual(row['options'].count(expected), 1)


if __name__ == '__main__':
    unittest.main()

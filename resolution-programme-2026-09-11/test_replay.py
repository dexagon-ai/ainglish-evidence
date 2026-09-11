import copy
import unittest
from ainglish import panel
from replay import replay


def fixture():
    items = [{'id': 'i' + str(i), 'answer': 'yes', 'options': ['yes', 'no'], 'settlement_stratum': 'primary'} for i in range(8)]
    readers = [{'name': 'reader-a'}, {'name': 'reader-b'}]
    rows = [(x['id'], panel.arm_for(12, r['name'], x['id']), r['name'], 'yes' if i % 3 else 'no') for i, x in enumerate(items) for r in readers]
    contract = [{'id': 'primary', 'weight': 1, 'share': 1.0}]
    lo, hi, journal = panel.attested_bootstrap_accuracy(rows, items, readers, contract, n=100, seed=12)
    value, arms, strata = panel._stratified_accuracy(rows, items, contract)
    return {'manifest_hash': 'a' * 64, 'manifest': {'settlement_strata': [{'id': 'primary', 'weight': 1}]},
            'interval_provenance_attestation': journal, 'value': value,
            'value_lo': panel._register_round(lo, 4), 'value_hi': panel._register_round(hi, 4),
            'stratum_results': strata}


class ReplayTest(unittest.TestCase):
    def test_matches_a_synthetic_official_journal_without_reader_calls(self):
        result = replay(fixture())
        for key in ['journal_hash_matches', 'accepted_draws_match', 'value_matches', 'interval_matches']:
            self.assertTrue(result[key], key)

    def test_corruption_and_false_interval_are_visible(self):
        row = fixture()
        row['interval_provenance_attestation']['content_sha256'] = 'b' * 64
        row['value_lo'] -= 1
        result = replay(row)
        self.assertFalse(result['journal_hash_matches'])
        self.assertFalse(result['interval_matches'])

    def test_missing_duplicate_or_invalid_cells_refuse(self):
        for mutation in ('missing', 'duplicate', 'bad-bit'):
            row = copy.deepcopy(fixture())
            cells = row['interval_provenance_attestation']['cells']
            if mutation == 'missing':
                cells.pop()
            elif mutation == 'duplicate':
                cells.append(cells[0])
            else:
                cells[0]['correct'] = 1
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                replay(row)

    def test_absent_or_unknown_journal_is_not_a_pass(self):
        self.assertEqual(replay({})['status'], 'no_sufficient_journal')
        row = fixture()
        row['interval_provenance_attestation']['algorithm']['name'] = 'other'
        self.assertEqual(replay(row)['status'], 'unsupported_algorithm')


if __name__ == '__main__':
    unittest.main()

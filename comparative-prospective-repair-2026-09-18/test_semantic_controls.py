import unittest
from semantic_controls import CASES, CARVEOUTS, DELETIONS, compatible, classify, delete_word, report


class SemanticControlTests(unittest.TestCase):
    def test_completed_role_not_hidden_bare_gold(self):
        for c in CASES:
            with self.subTest(c['id']):
                idx = 1 if c['role'] == 'doer' else 2
                self.assertEqual('entailed', classify(compatible(c['role']), lambda w: w[0] > w[idx]))
                self.assertEqual('not-determined', classify(compatible('bare_live'), lambda w: w[0] > w[idx]))
                self.assertEqual('contradicted', classify(compatible(c['role']), lambda w: w[0] <= w[idx]))

    def test_role_completions_are_distinct(self):
        self.assertNotEqual(compatible('doer'), compatible('done_to'))
        self.assertEqual(compatible('bare_live'), compatible('doer') | compatible('done_to'))
        self.assertTrue(compatible('doer') - compatible('done_to'))
        self.assertTrue(compatible('done_to') - compatible('doer'))

    def test_level_is_not_implied(self):
        for role, idx in (('doer', 1), ('done_to', 2)):
            self.assertEqual('not-determined', classify(compatible(role), lambda w: w[idx] > 0))

    def test_type_clash_requires_declared_type_restriction(self):
        # Explicit fixture: rival is a parser, not parseable log data.
        bare_roles = {'doer'}
        worlds = frozenset().union(*(compatible(role) for role in bare_roles))
        self.assertEqual('entailed', classify(worlds, lambda w: w[0] > w[1]))
        self.assertNotEqual(worlds, compatible('bare_live'))

    def test_done_to_has_no_light_full_text_saving(self):
        for c in CASES:
            if c['id'] in ('trust-done-to', 'test-done-to'):
                self.assertEqual(c['light'], c['full'])

    def test_deletions_do_not_all_widen_to_bare(self):
        for source, index, expected, label in DELETIONS:
            self.assertEqual(expected, delete_word(source, index))
        self.assertEqual({'malformed', 'ambiguous'}, {x[3] for x in DELETIONS})

    def test_carveouts_are_explicit_not_a_parser_result(self):
        self.assertEqual(4, len(CARVEOUTS))
        self.assertEqual(4, len({x[0] for x in CARVEOUTS}))
        self.assertTrue(all(not x['declared_trigger'] for x in report()['carveouts']))

    def test_empty_or_unknown_semantics_refused(self):
        with self.assertRaises(ValueError): classify(set(), lambda w: True)
        with self.assertRaises(ValueError): compatible('invented')

    def test_no_measurement_claim(self):
        r = report()
        self.assertFalse(r['is_measurement'])
        self.assertEqual(0, r['model_calls'])
        self.assertEqual(6, len(r['cases']))


if __name__ == '__main__': unittest.main()

from copy import deepcopy
from collections import Counter
import unittest
from controls import BASE, V2, FORMS, SPECS, LABELS, build, score, witnesses


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.f = build()

    def test_counts_and_preserved_v2(self):
        self.assertEqual((60, 72, 216), tuple(self.f[k] for k in ('semantic_worlds','semantic_question_probes','prompt_variants')))
        self.assertEqual(self.f['items'][:201], V2.build()['items'])
        self.assertEqual(self.f['candidate_sha256'], V2.build()['candidate_sha256'])
        self.assertEqual(216, len({x['id'] for x in self.f['items']}))

    def test_all_ten_partial_endpoints_and_balanced_rotations(self):
        for form in FORMS:
            for dim in SPECS:
                rows = [x for x in self.f['items'] if x.get('coverage_family') == 'partial_information' and x['form_slot'] == form and x['dimension'] == dim]
                self.assertEqual(3, len(rows))
                self.assertEqual(1, len({x['world_id'] for x in rows}))
                self.assertEqual({LABELS[2]}, {x['gold'] for x in rows})
                self.assertEqual(Counter({0:1,1:1,2:1}), Counter(x['options'].index(x['gold']) for x in rows))

    def test_no_target_markers_or_changed_questions(self):
        for x in self.f['items']:
            self.assertEqual(SPECS[x['dimension']]['question'], x['question'])
            self.assertFalse(any(form in x['text'] + x['question'] for form in FORMS))

    def test_partial_errors_now_fail_all_ten_endpoints(self):
        for label in LABELS[:2]:
            result = score(self.f, BASE.fixture_answers(self.f, lambda x: label if x.get('coverage_family') == 'partial_information' else x['gold']))
            self.assertTrue(result['complete'])
            self.assertEqual('fail', result['fixture_acceptance']['status'])
            self.assertEqual(10, len(result['fixture_acceptance']['failed_endpoints']))
            self.assertEqual(30, result['coverage_families']['partial_information']['incorrect'])
            self.assertTrue(all(x['fixture_checks']['explicit_fact']['status'] == 'pass' for x in result['endpoints']))

    def test_wrong_one_partial_rotation_fails_that_endpoint(self):
        rows = BASE.fixture_answers(self.f)
        rows[-1]['answer'] = 'Yes'
        result = score(self.f, rows)
        self.assertEqual(1, len(result['fixture_acceptance']['failed_endpoints']))

    def test_missing_partial_answer_is_incomplete_not_pass_or_wrong(self):
        for null in (False, True):
            rows = BASE.fixture_answers(self.f)
            if null: rows[-1]['answer'] = None
            else: rows.pop()
            result = score(self.f, rows)
            self.assertEqual('incomplete', result['fixture_acceptance']['status'])
            self.assertEqual([], result['fixture_acceptance']['failed_endpoints'])
            self.assertEqual(1, len(result['fixture_acceptance']['incomplete_endpoints']))

    def test_missing_partial_family_cannot_pass(self):
        self.f['items'] = [x for x in self.f['items'] if x.get('coverage_family') != 'partial_information']
        result = score(self.f, BASE.fixture_answers(self.f))
        self.assertEqual('incomplete', result['fixture_acceptance']['status'])
        self.assertEqual(10, len(result['fixture_acceptance']['incomplete_endpoints']))

    def test_oracle_passes_only_fixture_checks(self):
        result = score(self.f, BASE.fixture_answers(self.f))
        self.assertTrue(result['complete'])
        self.assertEqual('pass', result['fixture_acceptance']['status'])
        self.assertFalse(result['fixture_acceptance']['instrument_qualified'])
        self.assertFalse(result['fileable_measurement'])
        self.assertNotIn('bundle_pass', result)

    def test_all_disclosed_shortcuts_fail(self):
        for name, result in witnesses(self.f).items():
            with self.subTest(name=name):
                self.assertEqual('fail', result['fixture_acceptance']['status'])
                self.assertEqual(10, len(result['fixture_acceptance']['failed_endpoints']))

    def test_other_families_remain_visible_without_an_invented_new_threshold(self):
        result = score(self.f, BASE.fixture_answers(self.f, lambda x: 'Yes' if x.get('coverage_family') == 'name_not_gender' else x['gold']))
        self.assertEqual(6, result['coverage_families']['name_not_gender']['incorrect'])
        self.assertEqual('pass', result['fixture_acceptance']['status'])
        self.assertEqual(['explicit_fact', 'partial_information'], result['fixture_acceptance']['required_checks'])
        self.assertFalse(result['fixture_acceptance']['instrument_qualified'])

    def test_rule_cannot_be_silently_lowered(self):
        for replacement in (None, {}, {'explicit_fact': {'numerator':0,'denominator':10}}):
            self.f['fixture_rule'] = replacement
            with self.assertRaises(ValueError): score(self.f, [])

    def test_single_read_contract_rejects_replica_index_and_duplicates(self):
        rows = BASE.fixture_answers(self.f)
        rows[0]['replica_index'] = 0
        with self.assertRaises(ValueError): score(self.f, rows)
        rows = BASE.fixture_answers(self.f)
        extra = deepcopy(rows[0]); extra['observation_id'] = 'different'
        with self.assertRaises(ValueError): score(self.f, rows + [extra])

    def test_observation_identity_and_endpoint_cannot_be_reused(self):
        for field, value in [('observation_id', 'synthetic/' + self.f['items'][0]['id']), ('dimension','gender')]:
            rows = BASE.fixture_answers(self.f); rows[-1][field] = value
            with self.assertRaises(ValueError): score(self.f, rows)

    def test_repeatable_and_no_mutation(self):
        rows = BASE.fixture_answers(self.f); original = deepcopy((self.f, rows))
        score(self.f, rows)
        self.assertEqual(original, (self.f, rows))
        self.assertEqual(self.f, build())
        self.assertEqual(0, self.f['reader_calls'])


if __name__ == '__main__': unittest.main()

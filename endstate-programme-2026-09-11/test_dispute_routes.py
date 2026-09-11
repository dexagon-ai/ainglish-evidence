import unittest

from dispute_routes import route


class DisputeRouteTests(unittest.TestCase):
    def target(self, **changes):
        return dict(public_id='invented-case', metric='token_delta',
                    preparation_state='legacy_fresh_inputs', comparison_identity=None) | changes

    def test_copyable_metric_label_is_not_a_semantic_comparator(self):
        key, action, stop = route(self.target(preparation_state='copyable_contract',
            comparison_identity={'comparator': 'token_delta'}))
        self.assertEqual('recover_semantic_comparator', key)
        self.assertIn('Recover/freeze actual English rendering', action)
        self.assertIn('no retrospective alteration', stop)

    def test_legacy_cost_is_not_newly_banned(self):
        key, _, stop = route(self.target())
        self.assertEqual('legacy_cost_contract_review', key)
        self.assertIn('still allows fresh replications', stop)
        self.assertIn('not an eligibility ban', stop)

    def test_aggregate_reader_source_does_not_acquire_new_strata(self):
        key, _, stop = route(self.target(metric='comprehension_accuracy_delta'))
        self.assertEqual('legacy_reader_contract_and_access', key)
        self.assertIn('aggregate-only sources as aggregate-only', stop)

    def test_author_choice_is_not_a_retirement_or_proven_falsifier(self):
        key, action, stop = route(self.target(public_id='a-94wc58sz8ks3ce4y'))
        self.assertEqual('author_retirement_chosen', key)
        self.assertIn('await activation', action)
        self.assertIn('not call the author decision a proven full falsifier', stop)


if __name__ == '__main__':
    unittest.main()

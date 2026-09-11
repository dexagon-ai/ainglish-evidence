import unittest
from audit import quantity


class GoldAuditTests(unittest.TestCase):
    def row(self, text, question, answer, options):
        return {'ainglish': text, 'question': question, 'answer': answer, 'options': options}

    def test_duplicate_determinacy_answers_are_not_unique_gold(self):
        r = self.row('For job X, the count is not known. count adjust-by(+3 units).',
                     'is the final numeric value determined', 'no', ['yes', 'no', 'the final value is not determined'])
        self.assertTrue(quantity(r)['non_unique_correct_answer'])

    def test_ordered_update_is_computed_from_text_not_a_ledger(self):
        r = self.row('Its starting value is 8 units. x set-to(2 units); x adjust-by(-3 units).',
                     'what is the final value? A = -1 units. B = 5 units. C = not determined. D = 2 units.', 'A', list('ABCD'))
        r['ledger'] = {'final': 999}
        self.assertEqual(quantity(r)['computed_final'], -1)
        self.assertEqual(quantity(r)['valid_answers'], ['A'])

    def test_reset_restores_unknown_and_wrong_gold_is_reported(self):
        r = self.row('The start is not known. x adjust-by(+0 units); x set-to(0 units).',
                     'is the final numeric value determined', 'no', ['yes', 'no'])
        self.assertFalse(quantity(r)['key_semantically_valid'])

    def test_unrecognised_frame_is_not_certified(self):
        r = self.row('There might be ten. x adjust-by(+2 units).', 'what is the final value?', 'A', ['A'])
        self.assertEqual(quantity(r)['status'], 'unassessed')

    def test_shared_first_english_update_is_not_dropped(self):
        r = self.row('Its starting value is -31 deg. First increase this quantity by -5 deg; complete that update before the next instruction. x adjust-by(-21 deg).',
                     'what is the final value? A = -57 deg. B = -52 deg. C = not determined. D = -21 deg.', 'A', list('ABCD'))
        self.assertEqual(quantity(r)['computed_final'], -57)
        self.assertTrue(quantity(r)['key_semantically_valid'])


if __name__ == '__main__':
    unittest.main()

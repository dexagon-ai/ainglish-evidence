import copy
import json
import unittest
from design import FIELDS
from validate_journals import control_messages, validate


class JournalIntegrityTests(unittest.TestCase):
    def fixture(self):
        plan = {'episodes_per_condition_arm': 1, 'qualification': {'control_items': 1, 'minimum_correct': 1},
                'max_prompt_tokens': 2048, 'arms': ['ainglish'], 'stages': ['sender'], 'max_tokens': {'sender': 192}}
        _, messages = control_messages(0)
        row = {'phase': 'control', 'id': '0', 'condition': 'base', 'ended': True,
               'raw': json.dumps(dict.fromkeys(FIELDS, None)), 'messages': messages, 'input_tokens': 5, 'output_tokens': 30}
        receipt = {'status': 'aborted-controls', 'episodes': 0, 'governance_evidence': False,
                   'controls': [{'correct': False, 'valid': True}]}
        return [row], receipt, plan, [{'id': 'one'}]

    def test_failed_qualification_is_retained_without_targets(self):
        rows, receipt, plan, cases = self.fixture()
        self.assertEqual(0, validate(rows, receipt, plan, cases, 'base', lambda m: 5)['target_calls'])

    def test_missing_duplicate_wrong_prompt_and_token_count_are_refused(self):
        rows, receipt, plan, cases = self.fixture()
        for broken in [[], rows * 2]:
            with self.assertRaises(AssertionError): validate(broken, receipt, plan, cases, 'base', lambda m: 5)
        broken = copy.deepcopy(rows); broken[0]['messages'][1]['content'] = 'Undeclared oracle feedback'
        with self.assertRaises(AssertionError): validate(broken, receipt, plan, cases, 'base', lambda m: 5)
        with self.assertRaises(AssertionError): validate(rows, receipt, plan, cases, 'base', lambda m: 6)

    def test_a_failed_control_cannot_be_claimed_as_complete(self):
        rows, receipt, plan, cases = self.fixture(); receipt['status'] = 'complete'; receipt['episodes'] = 1
        with self.assertRaises(AssertionError): validate(rows, receipt, plan, cases, 'base', lambda m: 5)


if __name__ == '__main__':
    unittest.main()

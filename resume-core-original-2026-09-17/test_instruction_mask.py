import json
from pathlib import Path
import re
import unittest
from instruction_mask_audit import audit,predict_without_instruction

ROOT=Path(__file__).parent
class MaskTests(unittest.TestCase):
    def setUp(self):
        self.replica=json.loads((ROOT/'saturnia-items.json').read_text())['items']
        self.original=json.loads((ROOT/'runspec.json').read_text())['items']
    def test_counterexample_in_both_arms(self):
        for result in audit(self.replica).values():
            self.assertEqual(result['correct_without_instruction'],64)
    def test_neutral_source_ids_do_not_match_label_rule(self):
        for result in audit(self.original).values():
            self.assertEqual(result['predictions_without_instruction'],0)
    def test_last_instruction_cannot_affect_predictor(self):
        for item in self.replica:
            if item.get('calibration'): continue
            replacement=item['english'].rsplit('. ',1)[0]+'. Unrelated final sentence.'
            self.assertEqual(predict_without_instruction(replacement,item['question']),item['answer'])
    def test_masking_visible_label_removes_this_specific_shortcut(self):
        for item in self.replica:
            if item.get('calibration'): continue
            masked=re.sub(r'SAT-RR2-(?:media|reading|review|simulation)-(?:resume|redo)-[0-3]','NEUTRAL-TASK',item['english'])
            self.assertIsNone(predict_without_instruction(masked,item['question']))
    def test_truthful_option_difference(self):
        def count(items):
            return sum(any(o=='Not specified by this message' for o in x['options']) for x in items if x.get('calibration'))
        self.assertEqual(count(self.original),8)
        self.assertEqual(count(self.replica),0)
    def test_no_launch_or_mint_record(self):
        status=json.loads((ROOT/'execution-status.json').read_text())
        self.assertFalse(status['execution_allowed'])
        self.assertEqual(status['reader_calls'],0)
        self.assertFalse((ROOT/'mint-receipt.json').exists())

if __name__=='__main__': unittest.main()

from copy import deepcopy
import json
from pathlib import Path
import unittest
from audit import audit_price, english_truth, marked_truth, legend
from candidate_audit import calendar_audit

class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items=json.loads((Path(__file__).resolve().parent.parent/'price-allocation-original-2026-09-07/items.json').read_text())

    def test_all_frozen_keys_entail_both_arms(self):
        report=audit_price(self.items)
        self.assertEqual(128,report['scientific_items']);self.assertEqual([],report['gold_mismatches'])
        self.assertEqual(41,report['fixed_letter_witness_false_impossibilities'])

    def test_mutated_gold_is_detected(self):
        rows=deepcopy(self.items);rows[0]['answer']='A'
        self.assertEqual(['compute/no-charge/0'],[x['id'] for x in audit_price(rows)['gold_mismatches']])

    def test_semantic_parsers_ignore_hidden_metadata(self):
        for item in self.items:
            if item.get('calibration'):continue
            stripped={k:v for k,v in item.items() if k in ['english','ainglish','question','options']}
            self.assertEqual(english_truth(item),english_truth(stripped))
            self.assertEqual(marked_truth(item),marked_truth(stripped))

    def test_cited_examples_use_their_own_rotated_legend(self):
        rows={x['id']:x for x in self.items}
        self.assertEqual(('yes','yes'),legend(rows['compute/no-charge/3'])['G'])
        self.assertEqual(('not determined','no'),legend(rows['compute/available-now/0'])['I'])

    def test_bad_or_missing_legend_refuses(self):
        for q in ['',self.items[0]['question'].replace('A=first yes, second yes.','A=first no, second no.')]:
            row=deepcopy(self.items[0]);row['question']=q
            with self.assertRaises(AssertionError):legend(row)

    def calendar_items(self):
        doc=json.loads((Path(__file__).resolve().parent.parent/'flagship-comprehension-closure-wave-v1-2026-09-02/next-weekday.items.json').read_text())
        return doc['items'] if isinstance(doc,dict) else doc

    def test_calendar_keys_and_population(self):
        r=calendar_audit(self.calendar_items())
        self.assertEqual([],r['gold_errors']);self.assertEqual(392,r['scientific_items'])
        self.assertEqual({'next-up/divergent':84,'next-up/convergent':112,
                          'next-week/divergent':84,'next-week/convergent':112},r['population'])

    def test_calendar_wrong_key_detected(self):
        rows=self.calendar_items(); rows[0]['answer']='2024-02-26 (+0 days)'
        self.assertEqual([rows[0]['id']],calendar_audit(rows)['gold_errors'])

    def test_calendar_wrong_divergence_metadata_refused(self):
        rows=self.calendar_items(); rows[0]['strata']['constructors_diverge']=True
        with self.assertRaises(AssertionError): calendar_audit(rows)

if __name__=='__main__':unittest.main()

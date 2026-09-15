"""Excluded synthetic tests of the final instrument and analysis. Never target observations."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import build
import analysis


class FinalPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items = json.loads((ROOT/'items.json').read_text())
        cls.plan = json.loads((ROOT/'planned-cells.json').read_text())['cells']
        cls.lookup = {i['id']: i for i in cls.items}
        cls.cells = [{'item_id': c['world_id'], 'reader': c['reader'], 'arm': c['arm'],
                      'answer': cls.lookup[c['world_id']]['answer']} for c in cls.plan]

    def test_full_semantics_and_every_response(self):
        for item in self.items:
            if item.get('calibration'):
                continue
            build.audit.semantic_check(item)
            build.audit_visible_semantics(item)
            for answer in item['options'] + ['off option', None]:
                row = analysis.report.decode([item], [{'item_id': item['id'],
                    'reader': analysis.READERS[0], 'arm': 'ainglish', 'answer': answer}])[0]
                if answer is None:
                    self.assertTrue(row['absent']); self.assertIsNone(row['joint'])
                elif answer == 'off option':
                    self.assertFalse(row['joint']); self.assertIsNone(row['policies'])
                    self.assertTrue(all(d['error'] is None for d in row['decisions'].values()))
                else:
                    record = item['probe_contract']['option_records'][answer]
                    gold = item['probe_contract']['gold']
                    self.assertEqual(row['joint'], answer == item['answer'])
                    self.assertEqual(row['policies'], record['policies'] == gold['policies'])
                    self.assertEqual(row['guarantees'], record['guarantees'] == gold['guarantees'])

    def test_mapping_spans_fail_closed(self):
        source = json.loads((ROOT/'source-contract.json').read_text())
        spans = build.spans_for(source['english_mapping'])
        self.assertEqual([len(spans[f]) for f in build.FORMS], [501, 789])
        with self.assertRaises(AssertionError):
            build.spans_for(source['english_mapping'] + ' changed')
        spec = json.loads((ROOT/'reader-config-review.json').read_text())
        self.assertEqual(spec['comparator']['kind'], 'complete-careful-english-v1')
        settings = json.loads((ROOT/'attempt-settings-review.json').read_text())
        self.assertEqual(settings['proposal_revision'], build.SLUG + '@' + build.CONTENT)

    def test_context_and_all_gold_counterfactuals_unchanged(self):
        twins = json.loads((ROOT/'audit-only-counterfactuals.json').read_text())['items']
        for left, right in zip(twins[::2], twins[1::2]):
            self.assertEqual(left['question'], right['question'])
            self.assertEqual(left['options'], right['options'])
            self.assertNotEqual(left['answer'], right['answer'])
            self.assertEqual(build.audit.visible(left, 'english'), build.audit.visible(right, 'english'))

    def test_rendered_text_error_detected_even_when_metadata_is_unchanged(self):
        item = deepcopy(next(i for i in self.items if not i.get('calibration')))
        uniform = next(p for p in item['probe_contract']['policies'] if p['kind'] == 'equal-probability')
        item['question'] = item['question'].replace(uniform['text'], uniform['text'].replace('1/', '2/', 1))
        with self.assertRaises(AssertionError):
            build.audit_visible_semantics(item)

    def test_ceiling_bootstrap_is_not_preservation(self):
        result = analysis.analyse(self.items, self.cells, self.plan, draws=25)
        self.assertEqual(result['joint_contrast_pp'], 0)
        self.assertEqual(result['equal_reader_within_reader_delta_pp'], 0)
        self.assertTrue(all(not x['passes_minus_5pp'] for x in result['conditional_ni'].values()))
        observed = result['equal_reader_correlation_sensitivity']['world_within_form_domain']['overall']
        self.assertEqual(observed['percentile_95'], [0, 0])
        self.assertTrue(observed['not_a_noninferiority_certificate'])

    def test_reader_mixture_does_not_become_within_reader_effect(self):
        cells = [dict(c, answer='invalid option') if c['reader'] == analysis.READERS[1] else c
                 for c in self.cells]
        rows = analysis.report.decode(self.items, cells)
        self.assertEqual(analysis.equal_reader_contrast(rows), 0)
        self.assertNotEqual(analysis.report.contrast(rows), 0)
        planned = analysis.planned_composition(self.plan)['forms']
        self.assertAlmostEqual(planned['choose-any']['max_absolute_zero_within_reader_effect_composition_pp'], 11.25)
        self.assertAlmostEqual(planned['draw-uniform']['max_absolute_zero_within_reader_effect_composition_pp'], 2.779922779922783)

    def test_adverse_results_preserved(self):
        cells = [dict(c, answer='invalid option') if c['arm'] == 'ainglish' else c for c in self.cells]
        result = analysis.analyse(self.items, cells, self.plan, draws=25)
        self.assertEqual(result['joint_contrast_pp'], -100)
        self.assertEqual(result['equal_reader_within_reader_delta_pp'], -100)

    def test_missing_and_absent_not_silently_counted_as_success(self):
        partial = self.cells[:-1]
        result = analysis.analyse(self.items, partial, self.plan, draws=10)
        self.assertFalse(result['planned_cells_complete'])
        self.assertEqual(result['conditional_ni']['status'], 'unavailable_incomplete_run')
        absent = dict(self.cells[0], answer=None, absence_reason='timeout')
        row = analysis.report.decode(self.items, [absent])[0]
        self.assertTrue(row['absent']); self.assertIsNone(row['joint'])
        single_reader = [r for r in analysis.report.decode(self.items, self.cells)
                         if r['reader'] == analysis.READERS[0]]
        self.assertIsNone(analysis.equal_reader_contrast(single_reader))

    def test_duplicate_changed_arm_and_unknown_reader_refused(self):
        with self.assertRaisesRegex(ValueError, 'Repeated'):
            analysis.validate_journal([self.cells[0], self.cells[0]], self.plan)
        for changed in [dict(self.cells[0], reader='new reader'),
                        dict(self.cells[0], arm='ainglish' if self.cells[0]['arm'] == 'english' else 'english')]:
            with self.assertRaisesRegex(ValueError, 'frozen'):
                analysis.validate_journal([changed], self.plan)

    def test_binomial_reference_boundaries(self):
        self.assertAlmostEqual(analysis.report.cp_upper(0, 59), 1 - .05**(1/59))
        # The published example is rounded: absolute 1e-6, not six decimal-place equality.
        self.assertAlmostEqual(analysis.report.cp_lower(4, 20, .05), .071354, delta=1e-6)
        self.assertAlmostEqual(analysis.report.cp_upper(4, 20, .05), .401029, delta=1e-6)


if __name__ == '__main__':
    unittest.main()

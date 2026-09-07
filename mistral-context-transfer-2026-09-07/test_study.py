import json
import unittest
from study import cases, writer_controls, fixed_lines, parse_writer, render, FIELDS

class ContextTransferTests(unittest.TestCase):
    def test_fresh_balanced_context_cells_and_foil_are_explicit(self):
        rows = cases()
        self.assertEqual(96, len(rows))
        self.assertEqual(96, len({r['id'] for r in rows}))
        for prefix in ['archive', 'waterlab', 'theatre']:
            subset = [r for r in rows if r['id'].startswith(prefix + '/')]
            for field in FIELDS:
                self.assertEqual(16, sum(r['brief'][field] for r in subset))
            for r in subset:
                self.assertIn('not the current plan', r['context'])
                for arm in ['english', 'ainglish']:
                    self.assertEqual(r['brief'], parse_writer(r['messages'][arm], arm))

    def test_one_optional_period_not_unlimited_repair(self):
        brief = dict.fromkeys(FIELDS, False)
        for arm in ['english', 'ainglish']:
            text = render(brief, arm)
            self.assertEqual(brief, parse_writer(text.upper(), arm))
            for suffix in ['.', ' .', '\nDone', '\n' + text.splitlines()[0]]:
                self.assertIsNone(parse_writer(text + suffix, arm))
            self.assertIsNone(parse_writer('```\n' + text + '\n```', arm))

    def test_writer_neutral_controls_balance_and_match_shape(self):
        rows = writer_controls()
        self.assertEqual(16, len(rows))
        for field in rows[0]['brief']:
            self.assertEqual(8, sum(r['brief'][field] for r in rows))
        for row in rows:
            self.assertEqual(5, len(fixed_lines(row['gold'])))
            self.assertEqual(fixed_lines(row['gold']), fixed_lines(row['gold'].upper()))

if __name__ == '__main__':
    unittest.main()

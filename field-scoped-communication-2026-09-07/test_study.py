import itertools
import json
import unittest
from study import FIELDS, ROOT, controls, decode, reader_messages

class FieldScopeTests(unittest.TestCase):
    def test_controls_balanced_and_roundtrip_in_every_dimension(self):
        rows = controls()
        self.assertEqual(48, len(rows))
        self.assertEqual(48, len({r['id'] for r in rows}))
        for d in [1, 2, 5]:
            subset = [r for r in rows if r['dimensions'] == d]
            for key in subset[0]['brief']:
                self.assertEqual(8, sum(r['brief'][key] for r in subset))
            for r in subset:
                self.assertEqual(r['brief'], decode(json.dumps(r['brief']), r['brief']))
                self.assertEqual(r['brief'], decode('```json\n' + json.dumps(r['brief']) + '\n```', r['brief']))

    def test_unrequested_target_keys_not_in_prompt(self):
        cases = json.loads((ROOT.parent / 'communication-diagnostics-2026-09-06/cases.json').read_text())
        for c in cases:
            for arm in ['ainglish', 'english']:
                prompt = json.dumps(reader_messages(c, arm, c['messages'][arm]))
                for field in set(FIELDS) - set(c['brief']):
                    self.assertNotIn(field, prompt)

    def test_no_semantic_repair_or_extra_content(self):
        for text in ['{"x":true,"x":false}', '{"x":1}', '{"x":true,"y":false}',
                     'Note: {"x":true}', '```json\n{"x":true}\n```\nDone']:
            self.assertIsNone(decode(text, ['x']))

if __name__ == '__main__':
    unittest.main()

import unittest
from analyse_completed import grouped


class AnalysisTests(unittest.TestCase):
    def test_contexts_and_languages_are_not_pooled(self):
        rows = [
            {'arm': 'ainglish', 'context': 'x', 'correct': True, 'parsed': True, 'truncated': False},
            {'arm': 'english', 'context': 'x', 'correct': False, 'parsed': False, 'truncated': False},
            {'arm': 'ainglish', 'context': 'y', 'correct': False, 'parsed': True, 'truncated': True},
        ]
        result = grouped(rows, ['context', 'arm'])
        self.assertEqual(3, len(result))
        self.assertEqual([1, 0, 0], [r['correct'] for r in result])
        self.assertEqual([1, 0, 1], [r['parsed'] for r in result])
        self.assertEqual([0, 0, 1], [r['truncated'] for r in result])


if __name__ == '__main__':
    unittest.main()

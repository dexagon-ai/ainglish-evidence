from pathlib import Path
import tempfile
import unittest
from resume_unstarted_calls import Journal, validate_prefix


class PrefixTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / 'journal.jsonl'

    def test_completed_prefix_can_continue_without_replaying(self):
        planned = [('a', {'x': 1}), ('b', {'x': 2})]
        with Journal(self.path, {}) as journal:
            journal.begin(*planned[0]); journal.end('a', {'raw': 'retained'})
        with Journal(self.path, {}, resume=True) as journal:
            self.assertEqual(1, validate_prefix(journal, planned))
            self.assertEqual('retained', journal.lookup(*planned[0])['raw'])
            journal.begin(*planned[1]); journal.end('b', {'raw': 'new'})
            self.assertEqual(2, validate_prefix(journal, planned))

    def test_changed_request_or_order_is_refused(self):
        with Journal(self.path, {}) as journal:
            journal.begin('a', {'x': 1}); journal.end('a', {'raw': 'kept'})
        with Journal(self.path, {}, resume=True) as journal:
            with self.assertRaisesRegex(RuntimeError, 'changed prompt'):
                validate_prefix(journal, [('a', {'x': 3})])
            with self.assertRaisesRegex(RuntimeError, 'prefix'):
                validate_prefix(journal, [('b', {'x': 1}), ('a', {'x': 1})])

    def test_uncertain_call_cannot_be_replayed(self):
        with Journal(self.path, {}) as journal:
            journal.begin('a', {'x': 1})
        with self.assertRaisesRegex(RuntimeError, 'Uncertain'):
            Journal(self.path, {}, resume=True)


if __name__ == '__main__':
    unittest.main()

import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from runtime import Journal, disk_guard, GIB

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'calls.jsonl'

    def test_resume_completed_call_without_new_spend(self):
        with Journal(self.path, {'study':'x'}) as j:
            j.begin('a', {'prompt':'hi'}); j.end('a', {'raw':'hello'})
        with Journal(self.path, {'study':'x'}, resume=True) as j:
            self.assertEqual('hello', j.lookup('a', {'prompt':'hi'})['raw'])
            with self.assertRaises(RuntimeError): j.begin('a', {'prompt':'hi'})
            with self.assertRaises(RuntimeError): j.lookup('a', {'prompt':'changed'})

    def test_uncertain_call_is_never_automatically_replayed(self):
        with Journal(self.path, {'study':'x'}) as j: j.begin('a', {'prompt':'hi'})
        with self.assertRaisesRegex(RuntimeError, 'Uncertain'):
            Journal(self.path, {'study':'x'}, resume=True)

    def test_changed_plan_refused(self):
        with Journal(self.path, {'study':'x'}): pass
        with self.assertRaisesRegex(RuntimeError, 'plan differs'):
            Journal(self.path, {'study':'y'}, resume=True)

    def test_tampering_refused(self):
        with Journal(self.path, {'study':'x'}): pass
        text = self.path.read_text().replace('"study":"x"','"study":"y"')
        self.path.write_text(text)
        with self.assertRaisesRegex(RuntimeError, 'integrity'): Journal(self.path, {'study':'x'}, resume=True)

    def test_partial_row_refused(self):
        with Journal(self.path, {'study':'x'}): pass
        with self.path.open('a') as f: f.write('{')
        with self.assertRaisesRegex(RuntimeError, 'Partial'): Journal(self.path, {'study':'x'}, resume=True)

    def test_second_writer_refused(self):
        with Journal(self.path, {'study':'x'}):
            with self.assertRaises(BlockingIOError): Journal(self.path, {'study':'x'}, resume=True)

    def test_host_disk_not_replaced_by_virtual_capacity(self):
        usage = lambda path: SimpleNamespace(free=(9 if path=='host' else 500)*GIB)
        with self.assertRaisesRegex(RuntimeError, 'Physical host'):
            disk_guard('host','wsl',usage=usage)
        usage = lambda path: SimpleNamespace(free=40*GIB)
        self.assertEqual(40*GIB, disk_guard('host','wsl',usage=usage)['host_free_bytes'])

if __name__ == '__main__': unittest.main()

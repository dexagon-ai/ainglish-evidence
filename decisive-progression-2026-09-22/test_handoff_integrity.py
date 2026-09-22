import copy,json,tempfile,unittest
from pathlib import Path
from handoff_integrity import freeze,verify,sha,audit_journal

class HandoffTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        (self.root/'input.json').write_text('{"example":"not a result"}')
        (self.root/'response.json').write_text('{"raw":"null or adverse result remains retained"}')
        self.schedule={'one':sha(b'first request'),'two':sha(b'second request')}
    def test_bundle_relocation(self):
        b=freeze(self.root,['input.json']);self.assertTrue(verify(self.root,b))
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'input.json').write_bytes((self.root/'input.json').read_bytes());self.assertTrue(verify(root,b))
    def test_changed_bytes_and_policy_refuse(self):
        b=freeze(self.root,['input.json']);bad=copy.deepcopy(b);bad['status']='approved'
        with self.assertRaises(ValueError):verify(self.root,bad)
        (self.root/'input.json').write_text('changed')
        with self.assertRaises(ValueError):verify(self.root,b)
    def test_traversal_secret_and_symlink_refuse(self):
        (self.root/'pat.txt').write_text('synthetic not a credential')
        (self.root/'link').symlink_to(self.root/'input.json')
        (self.root/'linked-dir').symlink_to(self.root,target_is_directory=True)
        for name in ['../input.json','/etc/passwd','pat.txt','link','.hidden','linked-dir/input.json']:
            with self.assertRaises(ValueError):freeze(self.root,[name])
    def issue(self):return {'id':'one','request_sha256':self.schedule['one'],'event':'issued'}
    def terminal(self,state='completed'):
        return self.issue()|{'event':state,'receipt_path':'response.json','receipt_sha256':sha((self.root/'response.json').read_bytes())}
    def test_interruption_is_uncertain_exposure_not_retry_permission(self):
        r=audit_journal(self.root,self.schedule,[self.issue()]);self.assertEqual(['one'],r['uncertain_exposure']);self.assertEqual(['two'],r['never_issued']);self.assertFalse(r['safe_to_autoretry'])
    def test_raw_positive_null_adverse_and_transport_failure_all_retained(self):
        for state in ('completed','failed'):
            r=audit_journal(self.root,self.schedule,[self.issue(),self.terminal(state)]);self.assertEqual(1,r[state]);self.assertFalse(r['safe_to_autoretry'])
    def test_duplicate_issue_unknown_request_or_lost_raw_is_refused(self):
        for events in [[self.issue(),self.issue()],[self.terminal()],[self.issue()|{'id':'unknown'}]]:
            with self.assertRaises(ValueError):audit_journal(self.root,self.schedule,events)
        terminal=self.terminal();(self.root/'response.json').write_text('changed response')
        with self.assertRaises(ValueError):audit_journal(self.root,self.schedule,[self.issue(),terminal])
if __name__=='__main__':unittest.main()

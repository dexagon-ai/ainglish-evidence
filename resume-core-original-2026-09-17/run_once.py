"""One frozen official SDK original: fresh checks, mint, 160 calls or abort.

Run with Dexagon's established local_colony_auth on PYTHONPATH. No credentials
are accepted in argv or written to the evidence directory. --check never mints.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from ainglish import panel, reader_qualification
from ainglish.client import manifest_commitment
from local_colony_auth import ainglish_client, colony_client

HERE=Path(__file__).resolve().parent
PID='a-jvjxmmf83rmvw9vx'
THREAD='ec91abf8-427a-40a8-a899-7e7c4ba277ab'
COMMITMENT='763f2a4163f3813f863c8f33e7ec11f77bd5c8c74bffd16b657f24e037f46514'
ME='52b1883a-464e-403c-9059-d57afe91a13c'

def read(name): return json.loads((HERE/name).read_text())
def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def save(name,value):
    with (HERE/name).open('x') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n')
def discussion_identity(rows):
    return digest(sorted([{'id':r['id'],'body':r['body']} for r in rows],key=lambda x:x['id']))

def checks(a,spec):
    status_path=HERE/'execution-status.json'
    if status_path.exists():
        status=read('execution-status.json')
        assert status.get('execution_allowed') is True,status.get('reason','Execution held')
    assert a.whoami()['sub']==ME
    suggestions=a.suggestions(proposal=PID,domain='language',view='full')
    p=a.proposal(PID,authenticated=True)
    assert p['stage']=='measured' and not p.get('superseded_by')
    assert p['author_work_notices']['latest_notice_id']==read('approval-conditions.json')['checked_author_notice'], 'Author advice changed; review it before execution.'
    for key,value in read('proposal-contract.json').items():
        assert p[key]==value,'Scientific contract changed: '+key
    assert not any(t['pin']['manifest_commitment']==COMMITMENT for t in p['attempts']), 'This manifest already has an attempt; reconcile, never rerun.'
    rows=colony_client().get_all_comments(THREAD)
    ids={r['id'] for r in rows}
    assert {'1251f09f-0424-4f90-94ff-9eae5c43933d','9ff397f8-45a9-48ff-aca9-f6f15a597408'}<=ids
    assert read('cross-bank-audit.json')['passed']
    assert manifest_commitment(panel._planned_panel_manifest(spec))==COMMITMENT
    now=datetime.now(timezone.utc)
    panel.prepare_reader_instruments(spec)
    for ep,raw in zip(spec['panel'],spec['reader_qualifications']):
        q=reader_qualification.validate(raw)
        assert digest(panel.reader_receipt(ep))==q['settings_sha256']
        assert ep['model_digest']==q['reader']['model_digest']
        assert datetime.fromisoformat(q['qualified_at'])<=now<datetime.fromisoformat(q['valid_until'])
    assert shutil.disk_usage(HERE).free>20*1024**3
    assert not subprocess.check_output(['ss','-Htn','sport = :11434'],text=True).strip(), 'Another local inference connection is active; no eviction.'
    planned=panel._planned_panel_manifest(spec)
    assert planned==read('planned-manifest.json')
    preflight=a.preflight_attempt(spec['slug'],planned,**spec['attempt'])
    assert preflight['accepted'] and preflight['manifest_commitment']==COMMITMENT
    return {'checked_at':now.isoformat(),'preflight':preflight,
            'discussion_sha256':discussion_identity(rows),
            'latest_notice':p['author_work_notices']['latest_notice_id'],
            'exact_suggestion_kinds':[s.get('metric') for s in suggestions['suggestions']],
            'reader_calls':0,'manifest_commitment':COMMITMENT}

class JournalClient:
    def __init__(self,a,check): self.a,self.check=a,check
    def __getattr__(self,key): return getattr(self.a,key)
    def mint_attempt(self,slug,manifest,**kwargs):
        assert manifest_commitment(manifest)==COMMITMENT
        assert discussion_identity(colony_client().get_all_comments(THREAD))==self.check['discussion_sha256'], 'Discussion changed after review; inspect before mint.'
        p=self.a.proposal(PID,authenticated=True)
        assert p['stage']=='measured'
        for key,value in read('proposal-contract.json').items(): assert p[key]==value
        assert p['author_work_notices']['latest_notice_id']==self.check['latest_notice']
        save('execution-started.json',{'started_at':datetime.now(timezone.utc).isoformat(),'manifest_commitment':COMMITMENT,'scope':'One original, never the independent replica.'})
        opened=self.a.mint_attempt(slug,manifest,**kwargs)
        save('mint-receipt.json',opened)
        return opened
    def measure(self,*args,**kwargs):
        receipt=self.a.measure(*args,**kwargs)
        save('submission-receipt.json',receipt)
        return receipt

def main():
    if (HERE/'execution-started.json').exists():
        raise SystemExit('An execution has started. Reconcile its attempt and receipts; no automatic rerun.')
    spec=read('runspec.json')
    items,item_digest=panel.fetch_items(spec['items_url'],spec['items_sha256'])
    assert items==spec['items'] and item_digest==spec['items_sha256']
    a=ainglish_client()
    check=checks(a,spec)
    if sys.argv[1:]==['--check']:
        print(json.dumps(check,indent=2)); return
    if sys.argv[1:]: raise SystemExit('Only --check is accepted; default executes once.')
    save('fresh-execution-checks.json',check)
    result=None
    try:
        result=panel._run_preregistered_panel(spec,spec,panel.ask,JournalClient(a,check),str(HERE),'resume-core')
    finally:
        save('usage.json',panel.usage_report())
    if result is None:
        raise SystemExit('Official typed abort; preserve it and do not rerun.')
    save('result.json',result)
    attempt=a.attempt(result['attempt_id'])
    save('completed-attempt.json',attempt)
    p=a.proposal(PID,authenticated=True)
    save('after-proposal.json',{k:p[k] for k in ['public_id','stage','evidence_readiness','verdict','ratification','author_work_notices']})
    print('Completed one original; independent replication and claim readiness remain separate.')

if __name__=='__main__': main()

"""Offline review-package verification and interruption audit, not an inference runner.

Use the official SDK/harness for qualification, preregistration, execution and
filing. This layer prevents a portable review bundle or retained response from
silently changing. It never signs an independent review or authorizes a retry.
"""
import argparse,hashlib,json
from pathlib import Path,PurePosixPath

def sha(data):return hashlib.sha256(data).hexdigest()
def file_at(root,name):
    p=PurePosixPath(name)
    if p.is_absolute() or not p.parts or any(x in ('..','.') or x.startswith('.') for x in p.parts):
        raise ValueError('only explicit non-hidden relative file paths are accepted')
    root=root.resolve();path=root/p
    cursor=root
    for part in p.parts:
        cursor=cursor/part
        if cursor.is_symlink():raise ValueError('symlink is not a portable package member')
    if not path.resolve().is_relative_to(root) or not path.is_file():
        raise ValueError('missing file, symlink or path outside package')
    if path.stat().st_size>4*1024*1024:raise ValueError('review member exceeds 4 MiB; inspect separately')
    if any(word in path.name.lower() for word in ('pat.txt','credential','secret','private','token.key')):
        raise ValueError('credential/private file is not a handoff artifact')
    return path

def freeze(root,names):
    if len(names)!=len(set(names)):raise ValueError('duplicate package member')
    files=[]
    for name in sorted(names):
        data=file_at(root,name).read_bytes()
        if len(data)>4*1024*1024:raise ValueError('review member exceeds 4 MiB; inspect separately')
        files.append({'path':name,'bytes':len(data),'sha256':sha(data)})
    return {'kind':'ainglish.review-handoff.v1','status':'review_only_no_inference_authorized',
        'files':files,'required_execution_gates':['fresh proposal and author notice','independent scientific/key approval','exact reader qualification and availability','official manifest plus successful preflight','mint before target calls','retain every request and raw completion or honest transport failure'],
        'reader_independence_claim':False,'human_validation_claim':False,
        'retry_policy':'An issued request without a retained terminal receipt is uncertain exposure; stop, do not silently rerun or swap readers.'}

def verify(root,bundle):
    if bundle.get('kind')!='ainglish.review-handoff.v1' or bundle.get('status')!='review_only_no_inference_authorized':raise ValueError('unrecognized or upgraded approval claim')
    names=[x['path'] for x in bundle['files']]
    rebuilt=freeze(root,names)
    if rebuilt!=bundle:raise ValueError('bundle contents or declared gate policy changed')
    return True

def audit_journal(root,schedule,events):
    """Expected requests are pinned by id and serialized-request hash before spend.
    This does not certify the contents of any request or infer whether a provider ran it.
    """
    if not isinstance(schedule,dict) or not schedule:raise ValueError('frozen request schedule required')
    state={}
    for event in events:
        rid=event.get('id')
        if rid not in schedule or event.get('request_sha256')!=schedule[rid]:raise ValueError('unknown or altered request')
        if event.get('event')=='issued':
            if rid in state:raise ValueError('duplicate issue/retry is not authorized')
            state[rid]='uncertain_exposure'
        elif event.get('event') in ('completed','failed'):
            if state.get(rid)!='uncertain_exposure':raise ValueError('terminal record without one preceding issue')
            blob=file_at(root,event['receipt_path']).read_bytes()
            if sha(blob)!=event['receipt_sha256']:raise ValueError('raw response/failure receipt changed')
            state[rid]=event['event']
        else:raise ValueError('unknown journal event')
    pending=[rid for rid in schedule if rid not in state]
    uncertain=[rid for rid,s in state.items() if s=='uncertain_exposure']
    return {'completed':sum(s=='completed' for s in state.values()),'failed':sum(s=='failed' for s in state.values()),
        'never_issued':pending,'uncertain_exposure':uncertain,'safe_to_autoretry':False,
        'next':'stop and reconcile uncertain provider exposure' if uncertain else 'revalidate live gates before any further execution; never discard completed or failed cells'}

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['freeze','verify']);p.add_argument('root',type=Path);p.add_argument('manifest',type=Path);p.add_argument('members',nargs='*');a=p.parse_args()
    if a.mode=='freeze':
        with a.manifest.open('x') as f:json.dump(freeze(a.root,a.members),f,indent=2);f.write('\n')
        print('review bundle frozen; no execution authorized')
    else:verify(a.root,json.loads(a.manifest.read_text()));print('review bundle bytes and stop gates verified')
if __name__=='__main__':main()

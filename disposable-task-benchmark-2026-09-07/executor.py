"""Prepared closed-schema local executor. No shell, model-chosen path, or live service."""
import hashlib
import json
from pathlib import Path
import tempfile

def validate(choice):
    if not isinstance(choice,dict) or set(choice)!={'team','work','deadline'}:
        raise ValueError('Exact three-field choice required')
    enums={'team':{'include','exclude'},'work':{'each','one'},'deadline':{'start','complete'}}
    if any(not isinstance(v,str) or v not in enums[k] for k,v in choice.items()):
        raise ValueError('No free-form commands, paths or silent default choices')
    return dict(choice)

def execute(choice, fixture_bytes, *, instrument_qualified=False):
    """Actually read/hash a generated fixture and write review artifacts in a fresh tempdir.

    Clock events are fixed simulator values, not claims about wall-clock deadlines.
    Result artifacts are returned before the disposable directory is cleaned up.
    """
    if instrument_qualified is not True:
        raise RuntimeError('Instrument qualification required before benchmark execution')
    choice=validate(choice)
    if not isinstance(fixture_bytes,bytes) or not 0<len(fixture_bytes)<=65536:
        raise ValueError('A bounded explicit fixture is required')
    decoded=json.loads(fixture_bytes)
    if not isinstance(decoded,dict) or set(decoded)!={'inventory'} or not isinstance(decoded['inventory'],list):
        raise ValueError('Not the frozen inventory fixture shape')
    actors=['Noor','Ivo']+(['Mira'] if choice['team']=='include' else [])
    owners=[actors] if choice['work']=='one' else [[actor] for actor in actors]
    with tempfile.TemporaryDirectory(prefix='ainglish-disposable-review-') as name:
        root=Path(name);source=root/'input.json';source.write_bytes(fixture_bytes)
        reviews=[]
        for i,reviewers in enumerate(owners):
            raw=source.read_bytes()
            row={'reviewers':reviewers,'sha256':hashlib.sha256(raw).hexdigest(),
                 'record_count':len(json.loads(raw)['inventory']),'review_complete':True}
            target=root/f'review-{i}.json'
            with target.open('x') as out:out.write(json.dumps(row,sort_keys=True)+'\n')
            reviews.append(json.loads(target.read_text()))
        assert len(list(root.glob('review-*.json')))==len(owners)
        return {'choice':choice,'artifacts':reviews,'actual_local_io':True,
            'clock_model':{'kind':'simulated-events','start_minute':540,'successful_end_minute':630,'deadline_minute':600},
            'requested_deadline_met':choice['deadline']=='start',
            'no_external_effects':True,'temporary_files_removed_on_return':True}

def follows_intended_plan(receipt,intended):
    intended=validate(intended)
    people=['Noor','Ivo']+(['Mira'] if intended['team']=='include' else [])
    owners=[people] if intended['work']=='one' else [[person] for person in people]
    return receipt['choice']==intended and [r['reviewers'] for r in receipt['artifacts']]==owners and all(r['review_complete'] for r in receipt['artifacts'])

def success(receipt,intended,fixture_bytes):
    expected_hash=hashlib.sha256(fixture_bytes).hexdigest()
    return follows_intended_plan(receipt,intended) and receipt['requested_deadline_met'] is True and all(r['sha256']==expected_hash for r in receipt['artifacts'])

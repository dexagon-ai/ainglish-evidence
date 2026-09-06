"""Execute the two previously frozen, unspent probability designs, once each."""
from datetime import datetime, timezone
from fractions import Fraction
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request
from unittest.mock import patch

from ainglish import panel
from ainglish.client import manifest_commitment
from ainglish.experiment_audit import audit_items
from local_colony_auth import ainglish_client

ROOT = Path(__file__).resolve().parent
PRIOR = ROOT.parent / 'overnight-2026-09-05'
OUT = ROOT / 'probability'
STUDIES = ['probability.numeric', 'probability.boundaries']
IDENTIFIER = 'a-b46kna5nkdy1d1fq'


def now():
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def save(name, value):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write('\n')


def audit(stem):
    items = json.loads((PRIOR / 'frozen' / (stem + '.items.json')).read_text())
    report = audit_items(items, require_balanced=True)
    assert report['ok'], report
    for item in items:
        if item.get('calibration'):
            continue
        facts = item['audit']
        a, b = facts['favourable'], facts['unfavourable']
        assert a >= 0 and b >= 0 and a + b > 0
        assert Fraction(facts['probability']) == Fraction(a, a+b)
        assert Fraction(facts['complement']) == Fraction(b, a+b)
        expected = {'probability': str(Fraction(a,a+b)), 'complement': str(Fraction(b,a+b)),
                    'odds-orientation': f'{b}:{a}'}.get(item['probe'])
        if expected is None:
            expected = 'yes' if facts['separately_supplied_information'] else 'no'
        assert expected == facts['semantic_gold'] == facts['answer_meanings'][item['answer']]
    report['arithmetic_and_declared_gold_recount'] = 'passed for every real row'
    report['scope'] = 'Numeric quantity/orientation versus complete English, or separately reported information; not bare-odds superiority, humans, channel robustness or future-trained performance.'
    return report


def prepare(source_specs):
    for stem in STUDIES:
        spec = json.loads((Path(source_specs) / (stem + '.runspec.json')).read_text())
        assert spec['items_sha256'] == hashlib.sha256(canonical(json.loads(
            (PRIOR / 'frozen' / (stem + '.items.json')).read_text()))).hexdigest()
        save(stem + '.runspec.json', spec)
        save(stem + '.input-audit.json', audit(stem))
    save('preparation.json', {'at': now(), 'prior_hold': 'No attempt minted and zero calls on 5 September; token prerequisite was missing.',
        'change': 'No item, reader, estimator or admission-policy changes. New output directory; same frozen 5 September source design.',
        'order': STUDIES, 'max_calls': 480, 'retries': 0,
        'stop': 'First scientific abort or runtime error prevents the remaining study. Eligibility/resource refusal before mint spends zero calls.',
        'not_claimed': ['independent replication', 'full original proposal validation', 'human comprehension', 'future-trained efficiency']})


def run(commit):
    assert not (OUT / 'started.json').exists(), 'Reconcile existing receipts; never retry targets'
    for path in [ROOT/'probability.py', *OUT.glob('*.runspec.json'), *OUT.glob('*.input-audit.json'), OUT/'preparation.json']:
        published = subprocess.run(['git','show',f'{commit}:{path.relative_to(ROOT.parent)}'], cwd=ROOT.parent,
                                   check=True, capture_output=True).stdout
        assert path.read_bytes() == published, 'Frozen source changed'
    save('started.json', {'at': now(), 'source_commit': commit, 'pid': os.getpid(), 'retries': 0})
    outcomes = []
    for stem in STUDIES:
        opened, count = {}, 0
        try:
            spec = json.loads((OUT / (stem + '.runspec.json')).read_text())
            assert audit(stem)['ok']
            c = ainglish_client()
            selection = c.suggestions(proposal=IDENTIFIER)
            p = c.proposal(c.proposal_slug_history(IDENTIFIER)['current_slug'], authenticated=True)
            assert p['stage'] in ['seconded','measured'] and p['publication_status'] == 'visible'
            assert 'token_delta' in p['evidence_readiness']['satisfied']
            assert hashlib.sha256(p['english_mapping'].encode()).hexdigest() == spec['attempt']['planned_sample']['mapping_sha256']
            with urllib.request.urlopen('http://127.0.0.1:11434/api/ps', timeout=10) as response:
                loaded = json.load(response)['models']
            assert all(m.get('name',m.get('model')) in {r['model'] for r in spec['panel']} for m in loaded), 'Unrelated loaded model; do not evict it'
            items, sha = panel.fetch_items(spec['items_url'], spec['items_sha256'])
            manifest = dict(spec, items=items, items_sha256=sha)
            panel.prepare_reader_instruments(manifest)
            for reader, qualification in zip(manifest['panel'],manifest['reader_qualifications']):
                assert datetime.fromisoformat(qualification['valid_until']) > datetime.now(timezone.utc)
                assert hashlib.sha256(canonical(panel.reader_receipt(reader))).hexdigest() == qualification['settings_sha256']
            planned = panel._planned_panel_manifest(manifest)
            settings = panel._attempt_settings(spec['attempt'],[panel.calibration_gate_statement(manifest),panel.admissibility_gate_statement(manifest)])
            save(stem+'.preflight.json', c.preflight_attempt(p['slug'], planned, **settings))
            save(stem+'.intent.json', {'at':now(),'manifest_commitment':manifest_commitment(planned),
                'manifest':planned,'settings':settings,'selection':selection,'evidence_readiness':p['evidence_readiness']})
            lookup = {(item[arm],item['question']): {'item_id':item['id'],'arm':arm,'calibration':bool(item.get('calibration'))}
                      for item in items for arm in ['english','ainglish']}
            assert len(lookup) == 2*len(items), 'Prompt identity collision'
            original_mint, original_chat = c.mint_attempt, panel.chat
            with (OUT/(stem+'.calls.jsonl')).open('x') as journal, (OUT/(stem+'.raw.jsonl')).open('x') as raw:
                def mint(*args,**kwargs):
                    receipt = original_mint(*args,**kwargs)
                    save(stem+'.opened.json',receipt); opened.update(receipt)
                    return receipt
                def chat(reader,prompt):
                    record={'at':now(),'reader':reader['name'],'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest()}
                    try:
                        output,truncated=original_chat(reader,prompt)
                        record.update(output=output,truncated=truncated)
                        return output,truncated
                    except BaseException as exc:
                        record['error_type']=type(exc).__name__; raise
                    finally:
                        raw.write(json.dumps(record)+'\n'); raw.flush(); os.fsync(raw.fileno())
                def ask(reader,text,question,options):
                    nonlocal count
                    assert opened, 'No inference before retained mint'
                    record=dict(lookup[text,question],at=now(),reader=reader['name'],attempt_id=opened['attempt']['attempt_id'])
                    try:
                        answer=panel.ask(reader,text,question,options)
                        record.update(answer=str(answer),absent_reason=getattr(answer,'reason',None) if panel.is_absent(answer) else None)
                        return answer
                    except BaseException as exc:
                        record['exception_type']=type(exc).__name__; raise
                    finally:
                        journal.write(json.dumps(record)+'\n'); journal.flush(); os.fsync(journal.fileno()); count+=1
                        if count%32==0: print(stem,count,'calls retained',flush=True)
                with patch.object(c,'mint_attempt',side_effect=mint),patch.object(panel,'chat',side_effect=chat):
                    result=panel._run_preregistered_panel(manifest,spec,ask,c,receipt_dir=str(OUT),receipt_stem=stem)
            if result is not None:
                save(stem+'.result.json',result); save(stem+'.server.json',c.attempt(result['attempt_id']))
            outcome={'study':stem,'state':'filed' if result else 'aborted','calls':count,
                     'value':result['value'] if result else None}
            outcomes.append(outcome); print(json.dumps(outcome),flush=True)
            if result is None: break
        except BaseException as exc:
            save(stem+'.exception.json',{'at':now(),'type':type(exc).__name__,'message':str(exc),'calls_retained':count,
                'attempt_id':opened.get('attempt',{}).get('attempt_id'),'recovery':'Reconcile retained receipt; no target retry.'})
            outcomes.append({'study':stem,'state':'reconciliation-required','calls':count})
            print(stem,type(exc).__name__,'retained; no retry',flush=True); break
    save('finished.json',{'at':now(),'outcomes':outcomes})


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['prepare','run'])
    parser.add_argument('--source-specs')
    parser.add_argument('--commit')
    args=parser.parse_args()
    if args.command=='prepare': prepare(args.source_specs)
    else: run(args.commit)

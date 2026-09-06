"""Exercise the released SDK ingestion path on the existing v3 pack, offline.

Outputs are local ingestion receipts, not a new language release or evidence of
external lab use. Never modifies the source pack or reads model weights.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
from ainglish.training_ingestion import prepare_training_records, content_fingerprint, cli

ROOT=Path(__file__).resolve().parent
PIN='b1031f56b308390de8f2a5eaa5c902c6bb62fea34cb9289dcaed7701a5c69b5c'

def save(name,value):
    p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as out:out.write(json.dumps(value,indent=2,ensure_ascii=False)+'\n')

def main(pack):
    before={str(p.relative_to(pack)):hashlib.sha256(p.read_bytes()).hexdigest() for p in pack.rglob('*') if p.is_file()}
    assert before['MANIFEST.json']==PIN
    summaries=[]
    for dataset in ['instruction','parallel','pretrain_documents']:
        for supplemental in [False,True]:
            result=prepare_training_records(pack,expected_manifest_sha256=PIN,dataset=dataset,include_non_normative=supplemental)
            name=dataset+('-with-supplemental' if supplemental else '-canonical')
            save(name+'/RECEIPT.json',result['receipt'])
            save(name+'/records.json',result['records'])
            source=[json.loads(l) for l in (pack/'data'/(dataset+'.jsonl')).read_text().splitlines()]
            original={r['id']:r for r in source}
            assert all(r['row']==original[r['row']['id']] for r in result['records'])
            summaries.append({'dataset':dataset,'supplemental':supplemental,'input':result['receipt']['input_rows'],
                'output':len(result['records']),'drops':dict(Counter(r['reason'] for r in result['receipt']['dropped'])),'whole_source_rows_unchanged':True})
    canonical=prepare_training_records(pack,expected_manifest_sha256=PIN,dataset='instruction')
    canaries=[content_fingerprint('instruction',r['row']) for r in canonical['records'][:3]]
    save('exclusion-canaries.json',canaries)
    code=cli([str(pack),'--manifest-sha256',PIN,'--dataset','instruction','--exclude-evaluation',str(ROOT/'exclusion-canaries.json'),'--output',str(ROOT/'cli-output')])
    assert code==0
    kept=[json.loads(l) for l in (ROOT/'cli-output/records.jsonl').read_text().splitlines()]
    assert not set(canaries)&{content_fingerprint('instruction',r['row']) for r in kept}
    assert len(kept)==len(canonical['records'])-3
    # The canaries are copied public training rows solely to test exclusion plumbing;
    # this must not be advertised as an independently held-out evaluation set.
    trainer=[]
    for record in kept:
        row=record['row']
        trainer.append({'messages':[{'role':'user','content':row['prompt']},{'role':'assistant','content':row['response']}],
            'metadata':{'source_row_id':row['id'],**record['provenance']}})
    for original,row in zip(kept,trainer):
        assert row['messages'][0]['content']==original['row']['prompt'] and row['messages'][1]['content']==original['row']['response']
    save('trainer-chat-records.json',trainer)
    # Negative checks use the authentic pack read-only. No forged release manifest.
    refused=[]
    for name,kwargs in [('wrong_pin',{'expected_manifest_sha256':'0'*64}),('unknown_slug',{'expected_manifest_sha256':PIN,'slugs':['not-a-ratified-entry']})]:
        try:prepare_training_records(pack,**kwargs)
        except ValueError:refused.append(name)
        else:raise AssertionError('Invalid input accepted: '+name)
    assert cli([str(pack),'--manifest-sha256',PIN,'--output',str(ROOT/'cli-output')])==2
    probe={'prompt':'Explain we-including-you.','response':'The group includes its addressee.'}
    changed=dict(probe,prompt=probe['prompt'].replace('-',' '))
    assert content_fingerprint('instruction',probe)!=content_fingerprint('instruction',changed)
    after={str(p.relative_to(pack)):hashlib.sha256(p.read_bytes()).hexdigest() for p in pack.rglob('*') if p.is_file()}
    assert before==after
    save('RESULTS.json',{'kind':'ainglish.training-ingestion-rehearsal.v1','source_manifest_sha256':PIN,
        'source_commit':'5c3b487f39087f1de0738ffd6b7f3492b688e40e','sdk_commit':'acc70d2b23df18cde3c9e74c47212afb0b304602',
        'projection_runs':summaries,'exact_exclusion_canaries':3,'trainer_chat_records':len(trainer),'negative_refusals':refused+['existing_output'],
        'source_files_unchanged':True,'hyphen_preserving_fingerprints':True,'new_downloads':0,'model_training':False,'external_adoption':False,
        'limits':['Exact copied-row exclusion is not paraphrase/template leakage detection.',
            'Chat envelopes preserve content but are not a claim that every training framework accepts their metadata unchanged.',
            'This exercises the existing ingestion CLI rather than introducing a duplicate ingestion implementation.',
            'A local successful ingest is not an external-lab inclusion, training or tokenizer-adoption receipt.']})
    print(json.dumps(summaries,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('pack',type=Path);a=p.parse_args();main(a.pack)

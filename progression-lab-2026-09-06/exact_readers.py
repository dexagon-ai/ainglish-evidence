"""Prospective population correction. No source or target cells are retried."""
import argparse
import hashlib
import json
import os
from unittest.mock import patch
from ainglish import panel, reader_qualification
from snapshot import ROOT, save
from execute_campaign import committed, now


def build():
    source = json.loads((ROOT/'sources/40702354347269f4230a1e2964522d8da3081fc7a188229204a00b833dba0d0e.json').read_text())
    specs = []
    for i, reader in enumerate(source['manifest']['readers']):
        reader = {k:reader[k] for k in ('name','provider','model','api','base_url','model_digest','answer_protocol','max_tokens','timeout_s','temperature')}
        reader.update(name=['Dexagon-Qwen7-Q4','Dexagon-Gemma12-Q4','Dexagon-Mistral24-Q4'][i], precision='q4_k_m')
        controls=[]
        for j in range(8):
            options=['violet','copper','ivory','indigo']
            answer=options[j%4]
            controls.append({'id':f'exact-format-{j}', 'detectable':f'The stored colour for record {j} is {answer}.',
                'other':f'The stored colour for record {j} is not provided.',
                'question':'Which colour is stated in the record? If absent, choose no listed colour.',
                'options': options+['not stated'], 'answer':answer})
        specs.append({'kind':reader_qualification.SCREEN_KIND,'roster_id':reader['name']+'@q4_k_m',
            'reader':reader,'lineage':{'key':['qwen2.5','gemma3','mistral-small3.2'][i],
                'basis':'Three exact cached source GGUF digests. Different families are not proof of independent training data.'},
            'controls':controls,'validity_days':7,'min_gap_bps':5000,'min_recovered_bps':8750})
    for spec in specs: reader_qualification.validate_screen(spec)
    save('frozen/exact-reader-screens.json', specs)
    save('frozen/POPULATION-CORRECTION.json', {'at':now(), 'supersedes':'construction.runspec.template.json',
        'reason':'Full-thread handoff explicitly requires the three-reader source population. The two-reader template was not executed or minted; model availability and thread review, not target outcomes, justify this correction.',
        'models':[s['reader']['model_digest'] for s in specs], 'target_calls':0,'new_downloads':0,
        'held_constant':'Source model digests, 1024 output-token cap, greedy decoding, provider defaults, five-option task, three regime weights. Fresh independently qualified controls precede target spend.'})


def qualify(commit):
    for path in [ROOT/'frozen/exact-reader-screens.json', ROOT/'exact_readers.py']: committed(path,commit)
    specs=json.loads((ROOT/'frozen/exact-reader-screens.json').read_text())
    save('execution/exact-readers.intent.json', {'at':now(),'freeze':commit,'retries':0})
    results=[]
    with (ROOT/'execution/exact-readers.raw.jsonl').open('x') as journal:
        original=panel.chat
        def chat(reader,prompt):
            raw,truncated=original(reader,prompt)
            journal.write(json.dumps({'reader':reader['name'],'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(), 'raw':raw,'truncated':truncated})+'\n')
            journal.flush();os.fsync(journal.fileno())
            return raw,truncated
        with patch.object(panel,'chat',side_effect=chat):
            for spec in specs:
                result=reader_qualification.run_screen(spec)
                results.append(result)
                save('execution/'+spec['reader']['name']+'.qualification.json',result)
                print(spec['reader']['name'],result['status'],flush=True)
    save('execution/exact-reader-results.json',results)
    if not all(r['status']=='passed' for r in results): raise SystemExit('Exact population failed qualification; no replacement or target retry')
    template=json.loads((ROOT/'frozen/construction.runspec.template.json').read_text())
    template['panel']=[s['reader'] for s in specs]
    template['reader_qualifications']=[r['receipt'] for r in results]
    template['panel_neff']=3
    template['attempt']['estimand']='Fresh-input replication of 40702354: equal-weight b/r/i consequence classification, original three cached model digests and decoding population, same comparator and five-option scoring.'
    template['attempt']['planned_sample']['readers']=3
    template['attempt']['admissibility_gates'][2]='All three exact qualified cached source readers complete the fixed run under declared calibration and cell-yield gates; no retries.'
    save('frozen/construction.exact-template.json',template)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','qualify']);p.add_argument('--commit');a=p.parse_args()
    build() if a.action=='build' else qualify(a.commit)

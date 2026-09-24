"""Run the proposed SDK diagnostic over retained preparation data, never science."""
from collections import Counter
import json
from pathlib import Path
from ainglish.experiment_audit import audit_items, audit_declarations, items_digest

ROOT=Path(__file__).resolve().parent


def write(name,data): (ROOT/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')


def run():
    audits={}
    for name in ('latest','stat','assignment'):
        rows=json.loads((ROOT/(name+'.careful-panel-draft.json')).read_text())
        declaration=json.loads((ROOT/(name+'.declarations.json')).read_text())
        audits[name]={'structure':audit_items(rows),'declared_design':audit_declarations(rows,declaration)}
        assert audits[name]['structure']['ok']
        assert not audits[name]['declared_design']['warnings']
    snapshots=sorted(ROOT.glob('live-*.json'));assert snapshots
    snap=json.loads(snapshots[-1].read_text());source=snap['stat_token_source']
    assert source['manifest_hash']=='f8b68a42ab8bef927b7f5d6161b17bd066b7a7dad8c6daf95e874afda13e9daa'
    manifest=source['manifest_fields'];pairs=manifest['test_set']
    assert items_digest(pairs)==manifest['items_sha256']=='b71d4f887e617018575bac0fc3de1db63dd4c7612779dba27f5716943ed9f9bd'
    # Explicit, separately dated reviewer annotations; source bytes remain untouched.
    annotations=[]
    for i,pair in enumerate(pairs,1):
        neg=' is not ' in pair['ainglish']
        annotations.append(dict(pair,id=f'source-pair-{i}',settlement_stratum=pair['stratum'],
            population_cell=pair['stratum']+('-negative' if neg else '-positive')))
    declaration={'kind':'ainglish.study-declarations.v1','expected_target_rows':8,'expected_control_rows':0,
        'counts':{'population_cell':{'statistical-positive':3,'statistical-negative':1,'practical-positive':3,'practical-negative':1}},
        'strata':[{'id':'statistical','count':4,'weight':1},{'id':'practical','count':4,'weight':1}]}
    audit=audit_declarations(annotations,declaration)
    assert audit['count_checks']['population_cell']['actual']=={'statistical-positive':3,'statistical-negative':1,'practical-positive':2,'practical-negative':2}
    assert audit['warnings']==[{'code':'declared_population_mismatch','field':'population_cell'}]
    assert [{k:r[k] for k in pairs[i]} for i,r in enumerate(annotations)]==pairs
    write('stat-token-review-annotations.json',{'source_manifest_hash':source['manifest_hash'],
        'source_items_sha256':manifest['items_sha256'],'review_only':True,
        'annotation_rule':'Manual review of all eight sentences, checked by literal is-not negation in this exact pinned bank; not a general semantic parser',
        'items':annotations,'declarations':declaration,'audit':audit})
    write('packet-audits.json',audits)
    print(json.dumps({'bank_structure_ok':{k:v['structure']['ok'] for k,v in audits.items()},
        'declared_answer_position_warnings':{k:v['structure']['evaluation']['warnings'] for k,v in audits.items()},
        'stat_source_warning':audit['warnings'],'reader_calls':0,'tokenizer_calls':0}))


if __name__=='__main__':run()

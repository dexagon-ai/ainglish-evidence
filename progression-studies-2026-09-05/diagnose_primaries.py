"""Post-filing descriptive diagnostics, not additional evidence or replacement values."""
import json
from pathlib import Path
import sys
from ainglish import panel
ROOT=Path(__file__).resolve().parent
for name in sys.argv[1:]:
    result=json.loads((ROOT/(name+'-primary-result.json')).read_text())
    spec=json.loads((ROOT/(name+'.runspec.json')).read_text())
    source=name+('.kit-v1.json' if name=='will' else '.items-v2.json')
    items=[r for r in json.loads((ROOT/source).read_text()) if not r.get('calibration')]
    prefix=name+'-primary.attempt-'+result['attempt_id']
    cells=json.loads((ROOT/(prefix+'.cells.json')).read_text())['rows']
    controls=json.loads((ROOT/(prefix+'.calibration.cells.json')).read_text())['rows']
    rows=[(r['item_id'],r['arm'],r['reader'],r['answer']) for r in cells]
    ids={r['id'] for r in items}
    assert len(cells)==len(items)*2 and all(r['item_id'] in ids for r in cells)
    by_form={}
    for stratum in spec['settlement_strata']:
        subset=[r for r in items if r['settlement_stratum']==stratum['id']]; wanted={r['id'] for r in subset}
        selected=[r for r in rows if r[0] in wanted]
        arms,_=panel.score(selected,subset)
        lo,hi=panel.bootstrap_delta(selected,subset,'comprehension_accuracy_delta',n=2000,seed=spec['seed'])
        by_form[stratum['id']]={'items':len(subset),'arms_unrounded':arms,
            'postfiling_descriptive_item_bootstrap_95':[lo,hi],
            'ni_minus5_descriptive':'inferior' if hi < -5 else 'not_inferior' if lo >= -5 else 'inconclusive'}
    calibration={}
    for reader in sorted({r['reader'] for r in controls}):
        calibration[reader]={}
        for arm in ['english','ainglish']:
            rows_arm=[r for r in controls if r['reader']==reader and r['arm']==arm]
            calibration[reader][arm]={'correct':sum(r['correct'] for r in rows_arm),'n':len(rows_arm)}
    report={'kind':'ainglish.postfiling-primary-diagnostics.v1','manifest_hash':result['manifest_hash'],
        'real_cells':len(cells),'control_cells':len(controls),'calibration_by_reader':calibration,
        'per_form':by_form,'no_extra_reader_calls':True,
        'boundary':'These per-form intervals are post-filing descriptive analyses using SDK bootstrap_delta, not changes to filed server-attested pooled intervals or newly submitted evidence. Fixed template/reader generalization limits remain.'}
    with (ROOT/(name+'-primary-diagnostics.json')).open('x') as f:json.dump(report,f,indent=2)
    print(name,json.dumps(by_form),flush=True)

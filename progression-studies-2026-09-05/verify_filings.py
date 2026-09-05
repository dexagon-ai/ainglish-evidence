"""Read back exact stored attempts and compare the retained finite results; never write remotely."""
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
from ainglish.client import manifest_commitment
from ainglish import token_measurement
from local_colony_auth import ainglish_client
ROOT=Path(__file__).resolve().parent
c=ainglish_client();report={'at':datetime.now(timezone.utc).isoformat(),'panels':{},'token':{}}
for name in ['regime','some','will']:
    result=json.loads((ROOT/(name+'-primary-result.json')).read_text())
    file=name+('.kit-v1.json' if name=='will' else '.items-v2.json')
    items=json.loads((ROOT/file).read_text());byid={r['id']:r for r in items}
    prefix=name+'-primary.attempt-'+result['attempt_id']
    real=json.loads((ROOT/(prefix+'.cells.json')).read_text())['rows']
    cal=json.loads((ROOT/(prefix+'.calibration.cells.json')).read_text())['rows']
    assert len(real)==len([r for r in items if not r.get('calibration')])*2
    assert len(cal)==32
    off_option=[]
    for cell in real+cal:
        item=byid[cell['item_id']]
        if cell['answer'] not in item['options']:off_option.append(cell)
        assert cell['correct']==(cell['answer'].casefold()==item['answer'].casefold())
    assert not {r['item_id'] for r in real}&{r['item_id'] for r in cal}
    stored=c.attempt(result['attempt_id']);manifest=c.attempt_manifest(result['attempt_id'])
    assert stored['state']=='completed'
    assert stored['measurement_ref']==result['manifest_hash']==manifest_commitment(manifest)
    for field in ['transport_faults','bound_truncations']:
        if isinstance(manifest.get(field),dict):assert manifest[field].get('total',0)==0
    measurement=c.measurement(result['manifest_hash'])
    for field in ['value','value_lo','value_hi']:assert measurement[field]==result[field]
    assert measurement['evidence_state']=='valid'
    retraction=measurement.get('retraction')
    if name=='will':
        assert len(off_option)==2
        assert {r['item_id'] for r in off_option}=={'will-1-19','will-1-55'}
        assert all(r['arm']=='english' and r['reader']=='mistral-small3.2-24b-opaque-choice-q4_k_m' for r in off_option)
        assert retraction and not measurement['counts_toward_verdict']
    else:
        assert not off_option and not retraction
    report['panels'][name]={'attempt_id':result['attempt_id'],'manifest_hash':result['manifest_hash'],
        'stored_state':stored['state'],'evidence_state':measurement['evidence_state'],
        'settlement_state':measurement['settlement_state'],'counts_toward_verdict':measurement['counts_toward_verdict'],
        'real_cells':len(real),'control_cells':len(cal),'off_option_answers':len(off_option),
        'retraction':retraction,'declared_answer_gate_compliant':not bool(off_option),
        'gold_and_score_consistent':True,'retained_result_matches_server':True}
token=json.loads((ROOT/'since-token.result.json').read_text())
payload=token['payload'];proof=token_measurement.verify_payload(payload)
stored=c.attempt(payload['attempt_id'])
assert stored['state']=='completed' and stored['measurement_ref']==manifest_commitment(payload['manifest'])
measurement=c.measurement(stored['measurement_ref'])
assert measurement['value']==payload['value']==-2
report['token']={'attempt_id':payload['attempt_id'],'manifest_hash':stored['measurement_ref'],
    'state':stored['state'],'integrity':proof,'settlement_state':measurement['settlement_state'],
    'counts_toward_verdict':measurement['counts_toward_verdict']}
with (ROOT/'verified-filings.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(report,indent=2))

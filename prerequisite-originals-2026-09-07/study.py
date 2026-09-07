"""Four prospective deterministic cost originals; no readers or tokenizer calls at build."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
from datetime import datetime, timezone

from ainglish import estimand, token_measurement
from ainglish.client import _canonical_json, manifest_commitment

ROOT=Path(__file__).resolve().parent
PRIVATE=Path('/home/dexagon/codex/ratification-20260907')
TARGETS={'windows':('a-vq5925e9710c574a',1), 'negative-modal':('a-y0h6xwnc74cg0p18',2),
         'stock-flow':('a-xffrm7wz2wt3xhzf',4), 'incident':('a-mxcehfr17mygjpsv',2)}
DOMAINS=['software','mechanical','logistics','documents','events','staffing','inventory','devices']

def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as out:
        json.dump(value,out,indent=2,ensure_ascii=False,allow_nan=False);out.write('\n')

def pair(ident,form,a,e):
    return {'id':ident,'stratum':form,'ainglish':a,'english':e}

def windows():
    rows=[];cells=[]
    things=['requests','jobs','parcels','revisions','tickets','shifts','orders','signals']
    units=[('hour','60m','clock hour','60-minute'),('minute','60s','clock minute','60-second'),
           ('day@UTC','24h','UTC calendar day','24-hour'),('week@UTC','7d','UTC calendar week','7-day')]
    for d,thing in enumerate(things):
        for u,(unit,span,clock,duration) in enumerate(units):
            n=[17,29,43,61][(d+u)%4]
            for form in ['per-clock','per-any']:
                ident=f'w-{d}-{u}-{form}'
                a=f'At most {n} {thing} {form}({unit if form=="per-clock" else span}).'
                e=f'At most {n} {thing} in each {clock}.' if form=='per-clock' else f'At most {n} {thing} in any {duration} span.'
                rows.append(pair(ident,form,a,e))
                cells.append({'id':ident,'domain':DOMAINS[d],'cap':n,'unit':unit,'span':span,'mode':form})
    return rows,cells

def negative_modal():
    frames=[('courier','enter the depot'),('backup','finish before dawn'),('visitor','arrive at the hall'),
        ('service','access the staging network'),('robot','cross the painted line'),('pump','start during inspection'),
        ('driver','leave the loading bay'),('package','reach the sorting hub'),('editor','publish the notice'),
        ('indexer','remove the archived draft'),('performer','join the rehearsal'),('scanner','admit the pass'),
        ('reviewer','approve the checklist'),('sensor','report during maintenance'),('supplier','ship the spare'),
        ('controller','open the bypass')]
    rows=[];cells=[]
    for f,(subject,predicate) in enumerate(frames):
        for v in range(8):
            person=f'The {subject} R{f:02}{v}'
            # Both readings stay grammatically possible; a claim types what the message
            # asserts, not what actually occurred. No undeclared exclusion or outcome key.
            for form in ['may-not-as-prohibition','may-not-as-possibility']:
                ident=f'm-{f:02}-{v}-{form}'
                a=f'{person} {form} {predicate}.'
                e=f'{person} is forbidden to {predicate}.' if form.endswith('prohibition') else f'{person} might not {predicate}.'
                rows.append(pair(ident,form,a,e))
                cells.append({'id':ident,'domain':DOMAINS[f//2],'subject':person,'predicate':predicate,
                    'mode':form,'bare':f'{person} may not {predicate}.',
                    'policy_status':[False,True,None,None][v%4],
                    'forecast_nonoccurrence_possible':[False,None,True,None][(v//2)%4],
                    'cost_only':True})
    return rows,cells

def stock_flow():
    members=['workers','occupants','evacuees','requests','crates','replicas','subscribers','devices']
    rows=[];cells=[]
    for d,member in enumerate(members):
        for v in range(16):
            scope=f'S{d}{v:02}';stamp=f'{8+v//4:02}:{15*(v%4):02}Z'
            interval=f'[07:00Z,{stamp})';n=(d+3*v)%11
            for form in ['remain-in','departed-from']:
                ident=f's-{d}-{v:02}-{form}'
                if form=='remain-in':
                    a=f'Exactly {n} {member} remain-in({scope}) as_of({stamp}).'
                    e=f'Exactly {n} distinct {member} are in {scope} at {stamp}, after changes effective then.'
                else:
                    a=f'Exactly {n} distinct {member} departed-from({scope}) during({interval}).'
                    e=f'Exactly {n} distinct {member} exited {scope} during {interval}.'
                rows.append(pair(ident,form,a,e))
                cells.append({'id':ident,'domain':['staffing','rooms','evacuation','queues','inventory','replicas','subscriptions','fleets'][d],
                    'member_type':member,'scope':scope,'identity_key':'member ID','stamp':stamp,'interval':interval,
                    'endpoint_rule':'left included, right excluded','mode':form,'exact_count':n,
                    'limit':'separately frozen claim-cost population, not a full event-log comprehension instrument'})
    return rows,cells

def incident():
    rows=[];cells=[]
    for d,domain in enumerate(DOMAINS):
        for v in range(8):
            for world in range(4):
                k=(d*8+v)*4+world
                incident=f'I{k:03}';check=f'C{k:03}';cause=f'K{k:03}';test=f'T{k:03}'
                stamp=f'{6+v:02}:{15*world:02}Z'
                cell={'id':f'i-{k:03}','domain':domain,'incident':incident,'check':check,'time':stamp,
                    'cause':cause,'test':test,'world_impact_absent':bool(world&1),'world_cause_removed':bool(world&2),
                    'schema':'Each reference resolves locally to one named incident, one impact-specific check, one candidate mechanism and its post-change test. Assertions are not additional proof of truth or exclusive attribution.',
                    'hard_case':['restart without repair','cause patch with draining backlog','narrow probe only','second active cause','old observation','workaround hides symptoms','wrong attribution','recurrence after check'][v]}
                cells.append(cell)
                rows.append(pair(cell['id']+'-impact','impact-recovered',
                    f'{incident} impact-recovered({check}@{stamp}).',
                    f'In {incident}, check {check} found its named impact absent at {stamp}.'))
                rows.append(pair(cell['id']+'-cause','cause-resolved',
                    f'{incident} cause-resolved({cause}, checked-by={test}).',
                    f'In {incident}, {cause} was removed and the post-change test {test} passed.'))
    return rows,cells

GENERATORS={'windows':windows,'negative-modal':negative_modal,'stock-flow':stock_flow,'incident':incident}

def build():
    from local_colony_auth import ainglish_client
    c=ainglish_client();limits=c.protocols()['measurement_submission']['manifest']['token_delta_limits']
    plan={}
    for name,(pid,bound) in TARGETS.items():
        p=json.loads((PRIVATE/'targets'/f'{pid}.json').read_text())
        rows,cells=GENERATORS[name]()
        forms=list(dict.fromkeys(r['stratum'] for r in rows))
        manifest={'metric':'token_delta','models':['cl100k_base','o200k_base','p50k_base'],
            'proposal_revision':p['slug'],'test_set':rows,
            'settlement_strata':[{'id':form,'weight':1} for form in forms],
            'estimand_contract':estimand.declaration(
                unit_span='complete resolved claim sentence, with identical references and temporal spellings in both arms where applicable',
                contrast='registered surface versus concise semantically complete careful English; omitted inferences are not positive claims in either arm',
                population=f'{len(rows)} frozen {name} complete pairs from eight authored domain frames; equal form weights; shared schemas excluded from both cost arms; repeated templates are not independent language populations',
                reducer='least_favourable',aggregation_rule='mean complete-pair difference within each tokenizer, then maximum tokenizer mean; equal form strata retained separately')}
        prepared=token_measurement.prepare({'manifest':manifest},token_limits=limits)
        save(ROOT/f'{name}.prepared.json',prepared)
        save(ROOT/f'{name}.cells.json',cells)
        save(ROOT/f'{name}.proposal.json',{k:p.get(k) for k in ['public_id','slug','form','english_mapping','predicted_measurement','evidence_contract','colony_thread_url']})
        plan[name]={'public_id':pid,'slug':p['slug'],'bound':bound,'pairs':len(rows),
            'manifest_hash':prepared['manifest_commitment'],'canonical_bytes':len(_canonical_json(prepared['manifest']).encode()),
            'mapping_sha256':hashlib.sha256(p['english_mapping'].encode()).hexdigest(),
            'prediction_sha256':hashlib.sha256(p['predicted_measurement'].encode()).hexdigest()}
    save(ROOT/'PLAN.json',{'kind':'ainglish.prerequisite-originals.v1','targets':plan,'reader_calls':0,'tokenizer_calls_at_freeze':0,
        'followthrough':'No comprehension spend until each cost prerequisite has independent confirming evidence and the complete instrument is qualified. Semantic cells are a reusable bridge, not a claim that a comprehension run is prepared or completed. Incident cost covers both individual marker claims, not a separately settled conjunction cost.'})
    save(ROOT/'FROZEN.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.iterdir()) if p.is_file()})
    print(json.dumps(plan,indent=2))

def run(name):
    from local_colony_auth import ainglish_client, colony_client
    freeze=json.loads((ROOT/'FROZEN.json').read_text())
    for filename,h in freeze.items():assert hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()==h,filename
    target=json.loads((ROOT/'PLAN.json').read_text())['targets'][name]
    prepared=json.loads((ROOT/f'{name}.prepared.json').read_text())
    assert prepared['manifest_commitment']==manifest_commitment(prepared['manifest'])==target['manifest_hash']
    out=ROOT/'execution'/name
    assert not out.exists(),'Existing execution: reconcile, never silently remint.'
    assert shutil.disk_usage('/mnt/c').free>=15*1024**3
    c=ainglish_client();c.suggestions(proposal=target['public_id'])
    p=c.proposal(target['slug'],authenticated=True)
    assert p['stage'] in ['seconded','measured'] and p['public_id']==target['public_id']
    for field,key in [('english_mapping','mapping_sha256'),('predicted_measurement','prediction_sha256')]:
        assert hashlib.sha256(p[field].encode()).hexdigest()==target[key]
    colony_client().get_all_comments(p['colony_thread_url'].rsplit('/',1)[-1])
    limits=c.protocols()['measurement_submission']['manifest']['token_delta_limits']
    preflight=c.preflight_attempt(target['slug'],prepared['manifest'],**prepared['mint'])
    save(out/'preflight.json',preflight)
    save(out/'intent.json',{'at':datetime.now(timezone.utc).isoformat(),'manifest_hash':target['manifest_hash'],'freeze':freeze,'retries':0})
    opened=c.mint_attempt(target['slug'],prepared['manifest'],**prepared['mint']);save(out/'opened.json',opened)
    attempt=opened['attempt']['attempt_id']
    try:
        result=token_measurement.run_prepared(prepared,attempt,token_limits=limits)
    except Exception as error:
        fault={'kind':'ainglish.prerequisite-cost-fault.v1','type':type(error).__name__,'message':str(error)}
        save(out/'fault.json',fault)
        save(out/'abort.json',c.abort_attempt(attempt,str(error)[:500],fault,failed_gate_kind='harness_refuse'))
        raise
    save(out/'result.json',result)
    save(out/'receipt.json',c.measure(target['slug'],result['payload']))
    save(out/'source.json',c.measurement(target['manifest_hash']))
    save(out/'after.json',c.proposal(target['slug'],authenticated=True))
    print(name,result['payload']['value'],'bound',target['bound'],'attempt',attempt,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','run']);p.add_argument('--target',choices=list(TARGETS));a=p.parse_args()
    build() if a.action=='build' else run(a.target)

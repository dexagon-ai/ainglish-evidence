"""Independent replication of one small mixed-comparator diagnostic, not full qualification."""
import argparse,copy,hashlib,json,shutil,subprocess,urllib.request
from contextlib import redirect_stdout
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
from ainglish import panel,reader_qualification
from ainglish.client import _canonical_json,manifest_commitment
from local_colony_auth import ainglish_client
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parent;OUT=ROOT/'retention-replication'
TARGET='921717f2a794f292b6f21f987f532f749a05ab0ca7a5627b29d7f57b39da3436'
PID='a-5p0ywh1y1ec555wc';SLUG='all-or-nothing-keep-successes-say-what-survives-when-part-of-2'
def save(name,x):
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/name).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False)
def load(name):return json.loads((OUT/name).read_text())
def digest(x):return hashlib.sha256(_canonical_json(x).encode()).hexdigest()
def fresh():
    c=ainglish_client();s=c.suggestions(proposal=PID);p=c.proposal(SLUG,authenticated=True);m=c.measurement(TARGET)
    assert any(x.get('replicates_hash')==TARGET for x in s['suggestions'])
    assert m['submitter']['sub']!=c.whoami()['sub'] and m['evidence_state']=='valid' and not m['confirmed']
    assert p['public_id']==PID and p['stage']=='measured' and 'token_delta' in p['evidence_readiness']['satisfied']
    assert manifest_commitment(m['manifest'])==TARGET
    assert shutil.disk_usage('/mnt/c').free>15*1024**3
    return c,p,s,m
def prepare():
    c,p,s,m=fresh();source=m['manifest'];readers=copy.deepcopy(source['readers'])
    # Published receipts describe omitted sampler fields as provider-default; that
    # sentinel is metadata, not a literal request parameter. Reconstruct omission,
    # then demand that the newly bound canonical receipt exactly matches the source.
    for reader in readers:
      for key in list(reader):
        if reader[key]=='provider-default':del reader[key]
    # Explicit known local endpoint already configured on this machine. No foreign
    # source URLs are probed and no files/weights are copied or downloaded.
    assert all(r['provider']=='ollama' and r['base_url']=='http://localhost:11434/v1' for r in readers)
    bound=panel.prepare_reader_instruments({'panel':readers})['panel']
    for r,old in zip(bound,source['readers']):assert panel.reader_receipt(r)==old
    configs=[
      ('access','Add Pia to the maintainer group; add Quill to the auditor group; add Runa to the deployer group.',
       'The Pia and Quill membership changes succeeded, but the Runa membership change failed.'),
      ('publication','Release the timetable; release the map; release the accessibility guide.',
       'The timetable and map releases succeeded, but the accessibility-guide release failed.'),
      ('archive','Store the invoices in cold storage; store the receipts in cold storage; store the manifests in cold storage.',
       'The invoices and receipts were stored successfully, but storing the manifests failed.'),
    ]
    originals=[x for x in source['items'] if not x.get('calibration')];real=[]
    for i,old in enumerate(originals):
      row=copy.deepcopy(old);domain,actions,outcomes=configs[i//4];assert domain==row['strata']['domain']
      form=row['strata']['form'];comparator=row['strata']['comparator']
      disclosure='' if comparator=='bare' else (
       ' If any required member fails, no successful member effect may remain authoritative at terminal handoff.'
       if form=='all-or-nothing' else ' If a required member fails, each successful sibling effect remains authoritative and the failures stay disclosed.')
      row.update(id=f'dx-retention-{i+1:02}',english='Perform this bounded action set: '+actions+disclosure+' '+outcomes,
                 ainglish=actions[:-1]+', '+form+'. '+outcomes)
      real.append(row)
    pairs={(x['english'],x['ainglish']) for x in originals}
    assert not pairs & {(x['english'],x['ainglish']) for x in real}
    assert len(real)==12 and all(real[i]['strata']==originals[i]['strata'] for i in range(12))
    # Preserve source question, options, answer keys and the aggregate-only mixture.
    # Only complete action/outcome messages and their scenario identity are fresh.
    controls=[]
    for i,name in enumerate(('Ari','Bela','Cleo','Daru','Etta','Fenn')):
      controls.append({'id':f'dx-retention-cal-{i}','calibration':True,
       'calibration_scope':'target-independent','calibration_construct':'resolved custody',
       'english':f'Parcel receipt SR-{800+i}: the collector is not recorded.',
       'ainglish':f'Parcel receipt SR-{800+i}: the collector is {name}.',
       'question':f'Who collected the parcel on receipt SR-{800+i}?',
       'options':['Ari','Bela','Cleo','Daru','Etta','Fenn','not determined'],'answer':name})
    items=real+controls
    spec={'public_id':PID,'slug':SLUG,'construct':p['form'],'metric':'comprehension_accuracy_delta',
      'seed':20260909151,'comparator':source['comparator'],'panel':bound,'models':source['models'],
      'panel_neff':m['panel_neff'],'planted_arm':'ainglish','calibration_min_gap':0.5,
      'items':items,'items_sha256':digest(items),'replicates_hash':TARGET,
      'attempt':{'estimand':'The source mixed bare/careful comparator diagnostic: same 3 domains, both policies, same failure position, same exact reader population, aggregate-only. Not the complete 100-per-form careful-English claim.',
       'admissibility_gates':['Abort if target ceases to be eligible for this identity or its claim changes.',
        'Abort if exact cached source weights/settings are unavailable or qualification fails.',
        'Abort on faults, truncation, failed calibration, changed source comparator/population or any prior complete-pair overlap.'],
       'planned_sample':{'real_items':12,'calibration_items':6,'readers':2,'target_calls':24,'calibration_calls':24}}}
    save('source.json',m);save('proposal-before.json',p);save('suggestions-before.json',s)
    save('unqualified-runspec.json',spec);save('items.json',items)
    save('claim-lock.json',{k:p[k] for k in ('public_id','form','english_mapping','predicted_measurement','evidence_contract')})
    for i,reader in enumerate(bound):
      qcontrols=[]
      for n,name in enumerate(('Gina','Hale','Iris','Joss','Kira','Luz','Mika','Neri')):
        opts=['Gina','Hale','Iris','Joss','Kira','Luz','Mika','Neri']
        qcontrols.append({'id':f'qual-retention-{n}','detectable':f'Sealed dispatch QF-{910+n}: the recipient is {name}.',
          'other':f'Sealed dispatch QF-{910+n}: the recipient is not identified.',
          'question':f'Who is the recipient of dispatch QF-{910+n}?','options':opts,'answer':name})
      screen={'kind':reader_qualification.SCREEN_KIND,'roster_id':source['models'][i],'reader':reader,
       'lineage':{'key':('falcon3','olmo2')[i],'basis':'Distinct published base-model family; exact cached source weight digest preserved. Not a claim of disjoint training data.'},
       'controls':qcontrols,'validity_days':7,'min_gap_bps':5000,'min_recovered_bps':10000}
      reader_qualification.validate_screen(screen);save(f'qualification-screen-{i}.json',screen)
    save('design.json',{'scope':'Independent confirmation attempt of the existing 12-item mixed diagnostic only.',
      'limitations':['Six bare items measure recovery of a writer-intended policy, not textual entailment: bare policy is unspecified.',
       'The pooled source estimate is not a careful-English effect and cannot establish the full claim.',
       'Three related scenario templates are not twelve independent scenario clusters.',
       'Failure of the third action after two successes does not test every failure position or impossible atomicity.'],
      'preserved':['3 domains x 2 forms x 2 comparator types','exact source opaque question/options/golds','same failure position','same exact model and answer-affecting settings','aggregate-only result shape'],
      'changed':['fresh complete action and outcome messages','fresh control messages','prospectively fixed assignment seed'],
      'spend':'No model calls before this freeze. Qualification is target-independent; scientific mint occurs before target/calibration calls.'})
    print('Prepared source-matched retention replication; no inference',flush=True)
def qualify():
    assert not (OUT/'qualification-result-0.json').exists(),'Do not retry a qualification toward passing'
    fresh();spec=load('unqualified-runspec.json');receipts=[]
    for i in range(2):
      result=reader_qualification.run_screen(load(f'qualification-screen-{i}.json'));save(f'qualification-result-{i}.json',result)
      print('Qualification',i,result['status'],result['receipt']['result'],flush=True)
      if result['status']!='passed':return
      receipts.append(result['receipt'])
    spec['reader_qualifications']=receipts;save('unbound-runspec.json',spec)
def bind():
    c,p,s,m=fresh();spec=load('unbound-runspec.json')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
    spec['items_url']=f'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/completion-paths-2026-09-09/retention-replication/items.json'
    with urllib.request.urlopen(spec['items_url'],timeout=30) as f:assert json.load(f)==spec['items']
    manifest=panel._planned_panel_manifest(spec);settings=panel._attempt_settings(spec['attempt'],[panel.calibration_gate_statement(spec)])
    assert manifest.get('replicates_hash')==TARGET and not manifest.get('settlement_strata')
    save('preflight.json',c.preflight_attempt(SLUG,manifest,**settings));save('planned-manifest.json',manifest);save('runspec.json',spec)
    print('Preflight passed; no target calls',flush=True)
def run():
    assert not (OUT/'execution').exists(),'Reconcile previous execution, do not rerun'
    c,p,s,m=fresh();spec=load('runspec.json')
    assert {k:p[k] for k in load('claim-lock.json')}==load('claim-lock.json')
    assert manifest_commitment(panel._planned_panel_manifest(spec))==manifest_commitment(load('planned-manifest.json'))
    path=OUT/'execution';path.mkdir();original=panel.chat;ordinal=0
    with (path/'journal.jsonl').open('x') as journal:
      def chat(endpoint,prompt):
        nonlocal ordinal
        assert shutil.disk_usage('/mnt/c').free>15*1024**3
        ordinal+=1;journal.write(json.dumps({'event':'begin','ordinal':ordinal,'reader':endpoint['name'],'prompt':prompt})+'\n');journal.flush()
        raw,truncated=original(endpoint,prompt)
        journal.write(json.dumps({'event':'end','ordinal':ordinal,'raw':raw,'truncated':truncated})+'\n');journal.flush()
        return raw,truncated
      with patch.object(panel,'chat',side_effect=chat),(path/'runner.log').open('x') as log,redirect_stdout(log):
        result=panel._run_preregistered_panel(spec,spec,panel.ask,c,receipt_dir=str(path),receipt_stem='retention')
    save('outcome.json',result or {'filed':False,'calls':ordinal})
    if result:
      row=c.measurement(manifest_commitment(result['manifest']));save('measurement-after.json',row);save('source-after.json',c.measurement(TARGET))
      print('FILED',row['manifest_hash'],row['value'],row['value_lo'],row['value_hi'],row['settlement_eligible'],flush=True)
    save('proposal-after.json',c.proposal(SLUG,authenticated=True));save('suggestions-after.json',c.suggestions(proposal=PID))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','qualify','bind','run']);a=ap.parse_args();globals()[a.action]()

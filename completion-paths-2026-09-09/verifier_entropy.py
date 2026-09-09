"""Prospective verifier-tier entropy originals; never an adoption or correctness claim."""
import argparse,copy,hashlib,json,shutil,subprocess,urllib.request
from collections import Counter
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from ainglish import panel,reader_qualification
from ainglish.client import _canonical_json,manifest_commitment
from local_colony_auth import ainglish_client
ROOT=Path(__file__).resolve().parent; REPO=ROOT.parent; OUT=ROOT/'verifier-entropy'
PID='a-0vwy86qyygbqmr10'; SLUG='x-verifier-at-vantage-tier-2'; SEED=20260909271
def save(name,x):
    path=OUT/name;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False)
def load(name):return json.loads((OUT/name).read_text())
def digest(x):return hashlib.sha256(_canonical_json(x).encode()).hexdigest()
def fresh(require_suggestion=True):
    c=ainglish_client(); s=c.suggestions(proposal=PID); p=c.proposal(SLUG,authenticated=True)
    assert p['public_id']==PID and p['stage']=='measured'
    if require_suggestion:
        assert any(x.get('evidence_work',{}).get('metric')=='interpretation_entropy_delta' for x in s['suggestions'])
    assert shutil.disk_usage('/mnt/c').free>15*1024**3
    return c,p,s
def prepare():
    c,p,s=fresh(); readers=[];qualifications=[]
    retention=json.loads((ROOT/'retention-replication/unbound-runspec.json').read_text())
    readers.extend(copy.deepcopy(retention['panel'])); qualifications.extend(retention['reader_qualifications'])
    for family in ('mistral','gemma'):
        old=json.loads((REPO/f'reader-and-web-followthrough-2026-09-08/qualification/{family}.screen.json').read_text())
        reader=copy.deepcopy(old['reader']);reader['base_url']='http://localhost:11434/v1'
        readers.append(reader)
    bound=panel.prepare_reader_instruments({'panel':readers})['panel']
    assert len({r['model_digest'] for r in bound})==4
    # Qualification settings for the two reused receipts are unchanged, including endpoint.
    for i in range(2):assert digest(panel.reader_receipt(bound[i]))==qualifications[i]['settings_sha256']
    save('proposal-before.json',p);save('suggestions-before.json',s);save('readers.json',bound)
    save('reused-qualifications.json',qualifications)
    for i in (2,3):
        controls=[]
        for n,name in enumerate(('Opal','Perrin','Quin','Ravi','Sela','Tarin','Uma','Vela')):
            controls.append({'id':f'qual-verifier-{n}',
              'detectable':f'Consignment CX-{940+n} was collected by {name}.',
              'other':f'The collector of consignment CX-{940+n} is not identified.',
              'question':f'Who collected consignment CX-{940+n}?',
              'options':['Opal','Perrin','Quin','Ravi','Sela','Tarin','Uma','Vela'],'answer':name})
        screen={'kind':reader_qualification.SCREEN_KIND,'roster_id':bound[i]['name']+'@'+bound[i]['precision'],
          'reader':bound[i],'lineage':{'key':('mistral-small3.2','gemma3')[i-2],
          'basis':'Named distinct base family, exact cached quantized weight digest. No assertion of independent training data.'},
          'controls':controls,'validity_days':7,'min_gap_bps':5000,'min_recovered_bps':10000}
        reader_qualification.validate_screen(screen);save(f'qualification-screen-{i}.json',screen)
    tiers=('re-derivable','witnessed','testimony')
    # Eight independently written record situations, each crossed with all three tiers.
    # Same vantage labels across contrasting evidence tiers are deliberate falsifiers.
    worlds=[('chain-state','The reported block total is 17.', 'the public block records and the summation rule', 'the independent indexer receipt'),
      ('provider-billing','The charged usage total is 23.', 'the publicly signed usage rows and tariff', 'the independent auditor statement'),
      ('archive-catalogue','The inventory contains 31 records.', 'the public inventory entries and counting rule', 'the independent custodian report'),
      ('release-log','The release contains 19 files.', 'the public archive bytes and manifest rule', 'the independent mirror receipt'),
      ('local-log','The completed task count is 11.', 'the published signed task records and counting rule', 'the independent monitor attestation'),
      ('sensor-record','The threshold was crossed at 14:20.', 'the public sensor samples and fixed threshold', 'the independent observer receipt'),
      ('test-transcript','The suite passed 29 tests.', 'the public test inputs, implementation and deterministic replay rule', 'the independent laboratory report'),
      ('message-archive','The dispatch count is 13.', 'the public signed dispatch records and counting rule', 'the independent relay receipt')]
    main=[]
    for wi,(vantage,claim,public,byproduct) in enumerate(worlds):
      for ti,tier in enumerate(tiers):
        common=f'Record V{wi+1}-{ti+1}. '
        if tier=='re-derivable':
          common+=f'Anyone can retrieve {public}, and recompute the exact reported quantity without relying on a person\'s assertion. '
          answer='Repeat the public procedure without requesting anyone\'s permission.'
        elif tier=='witnessed':
          common+=f'Raw inputs are unavailable. A separate party with an independently controlled record supplied {byproduct}; this byproduct can be inspected, but outsiders cannot recompute the quantity from raw inputs. '
          answer='Inspect the separate party\'s retained byproduct, while distinguishing it from a recomputation.'
        else:
          common+='The reporter alone states the result. No underlying inputs or separate-party byproduct are available to the recipient. The word log in a location name supplies no extra record. '
          answer='Request new evidence before treating the report as independently checked.'
        # Balance every item to two distinct readers per arm without using any outcomes.
        nonce=0
        while True:
          iid=f'verifier-{wi+1:02}-{ti+1}-deal-{nonce}'
          if Counter(panel.arm_for(SEED,r['name'],iid) for r in bound)=={'english':2,'ainglish':2}:break
          nonce+=1
        explanation={'re-derivable':'reader recomputes from public inputs, trusts nobody',
          'witnessed':'an independent party with a stake left a checkable byproduct',
          'testimony':"the claimant's own word, no independent trace"}[tier]
        base={'id':iid,'context':common,'claim':claim,'tier':tier,'vantage':vantage,
          'ainglish':common+claim[:-1]+f' verifier-at({vantage};{tier}).',
          'careful':common+claim[:-1]+f", and its correctness is checkable from {vantage} at the stated tier: {explanation}.",
          'bare':common+claim,'question':'Which next step is justified by the evidence currently described?',
          'options':["Repeat the public procedure without requesting anyone's permission.",
            "Inspect the separate party's retained byproduct, while distinguishing it from a recomputation.",
            'Request new evidence before treating the report as independently checked.',
            'Treat the location name alone as a guarantee that the report is correct.'],'answer':answer}
        assert answer in base['options'];main.append(base)
    save('worlds-and-golds.json',main)
    controls=[]
    for n,name in enumerate(('Wren','Xara','Yori','Zela','Anik','Brin','Caro','Deni')):
      controls.append({'id':f'verifier-cal-{n}','calibration':True,'calibration_scope':'target-independent',
        'calibration_construct':'receipt holder','english':f'Receipt CP-{990+n} omits its holder.',
        'ainglish':f'Receipt CP-{990+n} names {name} as its holder.',
        'question':f'Who holds receipt CP-{990+n}?','options':['Wren','Xara','Yori','Zela','Anik','Brin','Caro','Deni'],'answer':name})
    for comparator in ('bare','careful'):
      items=[{k:x[k] for k in ('id','ainglish','question','options','answer')}|{'english':x[comparator],
        'strata':{'tier':x['tier'],'vantage':x['vantage']}} for x in main]+controls
      spec={'public_id':PID,'slug':SLUG,'construct':p['form'],'metric':'interpretation_entropy_delta',
       'seed':SEED,'comparator':{'kind':('context-matched-untagged-v1' if comparator=='bare' else 'complete-careful-english-v1'),
         'description':'Identical complete evidence context; '+('only the verifier tag is absent.' if comparator=='bare' else 'tag expanded using the filed tier meanings.')},
       'panel':bound,'panel_neff':4,'planted_arm':'ainglish','calibration_min_gap':0.5,
       'items':items,'items_sha256':digest(items),
       'attempt':{'estimand':f'Mean within-item interpretation entropy difference, verifier-at minus {comparator} English, across 24 frozen evidence situations and exactly four named readers. Correctness and credibility-transfer are separate retained diagnostics.',
        'admissibility_gates':['Proposal meaning and entropy prerequisite unchanged immediately before mint.',
         'All four exact cached instruments qualified; no replacement model, rerun, or changed gold.',
         'All target cells start only after mint. Abort on faults, truncation or calibration refusal.',
         'Two readers per item per arm were fixed before any outcome; no later item exclusion.'],
        'planned_sample':{'real_items':24,'calibration_items':8,'readers':4,'target_calls':96,'calibration_calls':64}}}
      save(f'{comparator}/items.json',items);save(f'{comparator}/unbound-runspec.json',spec)
    save('claim-lock.json',{k:p[k] for k in ('public_id','form','english_mapping','predicted_measurement','evidence_contract')})
    save('design.json',{'scope':'Two prospective originals sharing worlds; never pool them as independent samples.',
      'assignment':'Seed fixed at 20260909271. For each world choose the first integer ID nonce giving exactly two distinct readers in each arm. No outcomes are consulted.',
      'population':'Eight deliberately constructed evidence situations, each crossed with all three tiers. Same location string does not imply same evidence tier. Local-log includes both real external evidence and testimony-only cases.',
      'limitations':['Two co-readers per cell permit only 0 or 1 empirical entropy bit. No claim about the population of future models.',
        'Four model families are not proof of independent training data; panel_neff is declared only.',
        'The three evidence classes are related templates, not 24 independent natural-world draws.',
        'Low entropy can mean agreement on a wrong answer; retain per-tier accuracy and wrong-guarantee choices.',
        'The local-log testimony false-credibility option is diagnostic, not a separate confirmed falsifier study.',
        'No future tokenizer or model-weight training effect is measured.'],
      'policy':'File actual null/adverse outcomes unchanged; no CAD claim carrier is filed from this entropy study.'})
    print('Prepared both entropy contrasts; zero new model calls.',flush=True)
def qualify():
    fresh(); qs=load('reused-qualifications.json')
    assert not (OUT/'qualification-result-2.json').exists()
    for i in (2,3):
      r=reader_qualification.run_screen(load(f'qualification-screen-{i}.json'));save(f'qualification-result-{i}.json',r)
      print('Qualification',i,r['status'],flush=True)
      if r['status']!='passed':return
      qs.append(r['receipt'])
    save('qualifications.json',qs)
def bind():
    c,p,s=fresh(); commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
    for comp in ('bare','careful'):
      spec=load(f'{comp}/unbound-runspec.json');spec['reader_qualifications']=load('qualifications.json')
      spec['items_url']=f'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/completion-paths-2026-09-09/verifier-entropy/{comp}/items.json'
      with urllib.request.urlopen(spec['items_url'],timeout=30) as f:assert json.load(f)==spec['items']
      m=panel._planned_panel_manifest(spec);settings=panel._attempt_settings(spec['attempt'],[panel.calibration_gate_statement(spec)])
      save(f'{comp}/preflight.json',c.preflight_attempt(SLUG,m,**settings));save(f'{comp}/planned-manifest.json',m);save(f'{comp}/runspec.json',spec)
    print('Both contrasts preflighted without target inference.',flush=True)
def run():
    for comp in ('bare','careful'):
      # Both contrasts are prospectively frozen. After the first original, discovery
      # may correctly advertise independent replication rather than another original.
      # The named companion contrast is not a new opportunistic task or self-replication.
      c,p,s=fresh(require_suggestion=comp=='bare')
      assert {k:p[k] for k in load('claim-lock.json')}==load('claim-lock.json')
      if comp=='careful':
        first=c.measurement(load('bare/measurement-after.json')['manifest_hash'])
        assert first['evidence_state']=='valid' and not first.get('retraction') and not first['is_replication']
      spec=load(f'{comp}/runspec.json');path=OUT/comp/'execution';path.mkdir()
      assert manifest_commitment(panel._planned_panel_manifest(spec))==manifest_commitment(load(f'{comp}/planned-manifest.json'))
      original=panel.chat;ordinal=0
      with (path/'journal.jsonl').open('x') as journal:
        def chat(endpoint,prompt):
          nonlocal ordinal
          assert shutil.disk_usage('/mnt/c').free>15*1024**3
          ordinal+=1;journal.write(json.dumps({'event':'begin','ordinal':ordinal,'reader':endpoint['name'],'prompt':prompt})+'\n');journal.flush()
          raw,truncated=original(endpoint,prompt)
          journal.write(json.dumps({'event':'end','ordinal':ordinal,'raw':raw,'truncated':truncated})+'\n');journal.flush()
          return raw,truncated
        with patch.object(panel,'chat',side_effect=chat),(path/'runner.log').open('x') as log,redirect_stdout(log):
          result=panel._run_preregistered_panel(spec,spec,panel.ask,c,receipt_dir=str(path),receipt_stem=comp)
      save(f'{comp}/outcome.json',result or {'filed':False,'calls':ordinal})
      if result:
        row=c.measurement(manifest_commitment(result['manifest']));save(f'{comp}/measurement-after.json',row)
        print('FILED',comp,row['manifest_hash'],row['value'],row['value_lo'],row['value_hi'],flush=True)
      save(f'{comp}/proposal-after.json',c.proposal(SLUG,authenticated=True))
      if not result:return # no second contrast after a failed instrument/calibration gate
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','qualify','bind','run']);a=ap.parse_args();globals()[a.action]()

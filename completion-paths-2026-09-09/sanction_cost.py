"""One full-scope cost original: freeze, publish, mint, count once, retain outcome."""
import argparse,hashlib,json,subprocess,urllib.request
from pathlib import Path
from unittest.mock import patch
from ainglish import estimand,study_scope,token_measurement
from ainglish.client import _canonical_json,manifest_commitment
from local_colony_auth import ainglish_client

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'sanction-cost'
REPO=ROOT.parent
SLUG='sanction-allow-authority-clause-sanction-penalize-authority'
PID='a-dt2zbxfcgfbtsnvj'
FIELDS=('public_id','form','english_mapping','predicted_measurement','evidence_contract')
def digest(x):return hashlib.sha256(_canonical_json(x).encode()).hexdigest()
def save(name,x):
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/name).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False)
def load(name):return json.loads((OUT/name).read_text())
def fresh():
    c=ainglish_client();s=c.suggestions(proposal=PID);p=c.proposal(SLUG,authenticated=True)
    assert p['public_id']==PID and p['stage'] in ('seconded','measured') and not p.get('superseded_by')
    assert s['budgets']['measurements']['remaining']>0 and s['budgets']['attempts']['remaining']>0
    assert p['evidence_contract']['prerequisites']==[{'metric':'token_delta','at_most':4,'tokenizer_roster':['cl100k_base','o200k_base']}]
    return c,s,p
def text_pair(row):return tuple(row) if isinstance(row,list) else (row.get('english',row.get('baseline')),row.get('ainglish'))
def rows():
    # Fixed before encoding. Sixteen distinct authority/target contexts, each with both
    # poles, and four discourse/voice treatments. No selection on observed token cost.
    contexts=[
      ('person','Licensing Panel','Mara\'s pilot licence','current'),
      ('company','Trade Board','the Alder import company','future'),
      ('transaction','Payments Committee','the Cedar transfer','expired'),
      ('deployment','Release Council','the Larch rollout','denial'),
      ('product','Standards Office','the Kestrel sensor model','uncertain'),
      ('state','Harbour Assembly','the Northern Federation','quoted'),
      ('person','Accreditation Board','Ivo\'s inspection practice','current'),
      ('company','Market Commission','the Birch courier company','future'),
      ('transaction','Exchange Panel','the Aspen clearing transaction','expired'),
      ('deployment','Operations Board','the Rowan archive deployment','denial'),
      ('product','Equipment Council','the Copper control unit','uncertain'),
      ('state','Treaty Committee','the Western Confederation','quoted'),
      ('person','Review Tribunal','Nela\'s surveying practice','current'),
      ('company','Transport Office','the Hazel freight company','future'),
      ('transaction','Audit Council','the Willow settlement transaction','expired'),
      ('deployment','Safety Panel','the Juniper staging deployment','current'),
    ]
    result=[]
    for i,(domain,authority,target,status) in enumerate(contexts):
      shared=(f'Fictional record SC-{i+1}. The named authority is the {authority}; the target is {target}. '
              + {'current':'The recorded act is effective now.',
                 'future':'The recorded act takes effect next Monday.',
                 'expired':'The recorded act expired yesterday.',
                 'denial':'The following sentence denies that the formal act occurred.',
                 'uncertain':'The following sentence asks whether the formal act occurred.',
                 'quoted':'The following quoted sentence is not asserted by this report.'}[status]+' ')
      for form in ('sanction-allow','sanction-penalize'):
        if form=='sanction-allow':
          active=f'The {authority} formally permitted {target}.'
          passive=f'{target[0].upper()+target[1:]} was formally permitted by the {authority}.'
        else:
          active=f'The {authority} formally imposed a penalty on {target}.'
          passive=f'A penalty on {target} was formally imposed by the {authority}.'
        prose=active if i%2==0 else passive
        marked=f'{form}({authority}): {target}.'
        if status=='denial':prose='It is not true that '+prose[0].lower()+prose[1:];marked='It is not true that '+marked
        if status=='uncertain':prose='Is it true that '+prose[0].lower()+prose[1:-1]+'?';marked='Is it true that '+marked[:-1]+'?'
        if status=='quoted':prose='"'+prose+'"';marked='"'+marked+'"'
        result.append({'id':f'SC-{i+1}-{form}','domain':domain,'form':form,'status':status,
                       'voice':'active' if i%2==0 else 'passive','english':shared+prose,'ainglish':shared+marked})
    assert len(result)==32 and len({text_pair(x) for x in result})==32
    assert all(sum(x['form']==f for x in result)==16 for f in ('sanction-allow','sanction-penalize'))
    return result
def overlap(c,p,pairs):
    hashes=[]
    for m in p['measurements']:
      if m['metric']!='token_delta':continue
      d=c.measurement(m['manifest_hash']);hashes.append(m['manifest_hash'])
      prior=d['manifest'].get('test_set',[])
      assert not ({text_pair(x) for x in pairs}&{text_pair(x) for x in prior if isinstance(x,(dict,list))}), 'Prior complete-pair overlap'
    return hashes
def prepare():
    c,s,p=fresh();pairs=rows();sources=overlap(c,p,pairs)
    scope={k:p[k] for k in FIELDS};limits=c.protocols()['measurement_submission']['manifest']['token_delta_limits']
    mf=c.measurement_template('token_delta',models=['cl100k_base','o200k_base'])['manifest']
    mf.update(test_set=pairs,proposal_scope_sha256=digest(scope),
      test_set_note='32 fresh full utterance pairs, 16 per form; shared authority/target/time/force context identical. Fixed active/passive mix, no post-count selection.',
      input_construction={'domains':['person','company','transaction','deployment','product','state'],
        'weighting':'Each of the 32 complete pairs has equal weight. Each form contributes exactly half.',
        'sampling':'Descriptive predeclared finite grid, not 32 independent draws from all language. Repeated contexts across poles remain related.',
        'competitors':'Active formally permitted / formally imposed a penalty; passive formally permitted by / penalty formally imposed by. No bare ambiguous sanction comparator.',
        'limits':'Tests current tokenizer price, not comprehension, legal authority, future trained token cost or the full required robustness programme.'})
    mf=study_scope.attach(mf,purpose='claim_test',scope='The existing full 32-pair, two-tokenizer +4 cost prerequisite; not a retrospective reaggregation of old three-tokenizer studies.')
    mf=estimand.attach(mf,estimand.declaration(unit_span='one complete meaning-matched utterance pair',
       contrast='Ainglish minus full careful-English formal-act disclosure',population='32 fixed fresh pairs, 16 per form, declared six-domain authority/target grid and force/voice mix',
       reducer='least_favourable',aggregation_rule='Unrounded arithmetic mean of all 32 pairs per tokenizer; the maximum tokenizer mean over cl100k_base and o200k_base is the least-favourable headline. Member span is not sampling uncertainty.'))
    plan=token_measurement.prepare({'manifest':mf},token_limits=limits)
    plan['mint']['admissibility_gates'] += ['Abort before counting if the pinned current claim or exact tokenizer roster changed.',
      'Abort on any complete-pair overlap with historical token evidence.', 'Abort if an encoding is not already cached; no vocabulary or model downloads.']
    save('claim-lock.json',scope);save('sources-checked.json',sources);save('plan.json',plan)
    save('before.json',{'proposal':p,'suggestions':s});save('preflight.json',c.preflight_attempt(p['slug'],plan['manifest'],**plan['mint']))
    print('Prepared, no tokenizer calls',plan['manifest_commitment'],flush=True)
def run():
    assert not (OUT/'mint.json').exists(),'Existing execution: reconcile, do not rerun'
    plan=load('plan.json');commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
    url=f'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/completion-paths-2026-09-09/sanction-cost/plan.json'
    with urllib.request.urlopen(url,timeout=30) as r:assert json.load(r)==plan,'Freeze not publicly retrievable'
    c,s,p=fresh();assert digest({k:p[k] for k in FIELDS})==plan['manifest']['proposal_scope_sha256']
    overlap(c,p,plan['manifest']['test_set']);c.preflight_attempt(p['slug'],plan['manifest'],**plan['mint'])
    opened=c.mint_attempt(p['slug'],plan['manifest'],**plan['mint']);save('mint.json',opened);aid=opened['attempt']['attempt_id']
    with patch('tiktoken.load.read_file',side_effect=RuntimeError('No downloads permitted')):
      result=token_measurement.run_prepared(plan,aid,token_limits=plan.get('transport_limits'))
      token_measurement.verify_payload(result['payload'])
    save('result.json',result);receipt=c.measure(p['slug'],result['payload']);save('receipt.json',receipt)
    save('measurement-after.json',c.measurement(manifest_commitment(result['payload']['manifest'])))
    save('proposal-after.json',c.proposal(p['slug'],authenticated=True));save('suggestions-after.json',c.suggestions(proposal=PID))
    print('FILED',manifest_commitment(result['payload']['manifest']),result['payload']['value'],flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','run']);a=ap.parse_args();(prepare if a.action=='prepare' else run)()

"""Freeze, then mint-before-encoding a new original. No comprehension claim."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from ainglish import estimand, token_measurement
from local_colony_auth import ainglish_client

ROOT=Path(__file__).resolve().parent
def save(name,value):
    p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')

def build():
    domains=['invitations','approvals','scheduling','support','design-review','procurement','account-access','delivery','incident-coordination','job-offers','volunteer-offers','surveys','agent-callbacks','equipment-loans','publishing','venue-bookings']
    rows=[];cells=[]
    for di,domain in enumerate(domains):
        for scenario in range(8):
            for delivered in [False,True]:
                actor=['Mira','Lee','Noor','Ivo'][di%4]
                request=f'{domain}-{di+71}-{scenario}-revision-2'
                cutoff='2026-09-07T17:00Z'
                policy=['go without assent','wait for explicit assent','leave the next action undecided'][(di+scenario)%3]
                common=f'The exact request is {request}. Delivery to {actor} is '+('confirmed by a read receipt' if delivered else 'unknown')+f'. The separate workflow policy is to {policy}. '
                # Keep answer-bearing world facts out of the matched surfaces. A later
                # bare-status arm must not get its answer from shared context leakage.
                hidden_world=['An attributable negative answer exists.',
                    'The exact request concerns this week; its negative answer says not this week, not never.',
                    'The negative answer concerns revision 2, while revision 3 is current.',
                    'An attributable negative answer was sent in chat; the email thread is empty.',
                    'No response exists in the collector record.',
                    'An affirmative answer exists in chat, outside the email observation scope.',
                    'The first email answer arrives at 17:01Z, after the cutoff.',
                    'The email collector stopped receiving updates at 16:45Z; later unobserved mail is unknown.'][scenario]
                if scenario<4:
                    english=f'{actor} replied no to {request}.'
                    ainglish=f'{actor} replied-no(to={request}).'
                    form='replied-no'
                else:
                    english=f'By {cutoff}, no email reply from {actor} to {request} was observed.'
                    ainglish=f'no-reply-from({actor}, to={request}, via=email) as_of({cutoff}).'
                    form='no-reply-from'
                rows.append({'english':common+english,'ainglish':common+ainglish,'stratum':form})
                cells.append({'id':f'{domain}/{scenario}/{int(delivered)}','domain':domain,'scenario':scenario,'delivery_known':delivered,'policy':policy,'form':form,'shared_context':common,'hidden_world_for_later_gold_review':hidden_world,'english_claim':english,'ainglish_claim':ainglish})
    assert len(rows)==256 and len({(r['english'],r['ainglish']) for r in rows})==256
    manifest={'metric':'token_delta','models':['cl100k_base','o200k_base','p50k_base'],
        'test_set':rows,'settlement_strata':[{'id':'replied-no','weight':1},{'id':'no-reply-from','weight':1}],
        'estimand_contract':estimand.declaration(unit_span='complete vignette and scoped claim',
            contrast='registered exact-request reply or scoped observation claim versus concise meaning-complete careful English, with identical surrounding facts',
            population='256 cells: 16 authored domains, 8 response situations and 2 delivery states; equal form weights; domain and identifier variants are not independent grammatical frames',
            reducer='least_favourable',aggregation_rule='equal cell means then maximum tokenizer mean; preserve separate reply and no-observed-reply strata')}
    save('replied-token/cells.json',cells)
    save('replied-token/prepared.json',token_measurement.prepare({'manifest':manifest}))
    source=json.loads((ROOT/'replied-after-second.json').read_text())
    save('replied-token/PLAN.json',{'kind':'ainglish.replied-token-original.v1','public_id':source['public_id'],'slug':source['slug'],
        'mapping_sha256':hashlib.sha256(source['english_mapping'].encode()).hexdigest(),
        'governance_metric':'token_delta','comprehension_calls':0,'claim':'Current-tokenizer prerequisite only; threshold +3 tokens, not a prediction after training or new tokenizer exposure.',
        'limits':['The same semantic cells are retained for later comprehension-design review, but no joint-answer gold kit or bare-status score is claimed here.',
            'Absence is an observation claim, not proof that no answer exists. The stale collector cell deliberately preserves unknown world history.',
            '16 domains and identifier variants are not 256 independent linguistic templates. Policies are varied, not an exhaustive full interaction design.']})
    print('256 complete pairs frozen; no tokenizer loaded.')

def run(commit):
    for name in ['replied_tokens.py','replied-token/cells.json','replied-token/prepared.json','replied-token/PLAN.json']:
        path=ROOT/name
        assert subprocess.check_output(['git','show',f'{commit}:{path.relative_to(ROOT.parent)}'],cwd=ROOT.parent)==path.read_bytes()
    subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=ROOT.parent,check=True)
    if (ROOT/'replied-token/intent.json').exists():raise SystemExit('Existing intent: reconcile, never remint or recount.')
    plan=json.loads((ROOT/'replied-token/PLAN.json').read_text());prepared=json.loads((ROOT/'replied-token/prepared.json').read_text())
    c=ainglish_client();c.suggestions(proposal=plan['public_id'])
    fresh=c.proposal(plan['slug'],authenticated=True)
    assert fresh['stage'] in ['seconded','measured'] and hashlib.sha256(fresh['english_mapping'].encode()).hexdigest()==plan['mapping_sha256']
    preflight=c.preflight_attempt(plan['slug'],prepared['manifest'],**prepared['mint'])
    save('replied-token/preflight.json',preflight)
    save('replied-token/intent.json',{'at':datetime.now(timezone.utc).isoformat(),'freeze':commit,'retries':0})
    opened=c.mint_attempt(plan['slug'],prepared['manifest'],**prepared['mint']);save('replied-token/opened.json',opened)
    result=token_measurement.run_prepared(prepared,opened['attempt']['attempt_id']);save('replied-token/result.json',result)
    receipt=c.measure(plan['slug'],result['payload']);save('replied-token/receipt.json',receipt)
    save('replied-token/after.json',c.proposal(plan['slug'],authenticated=True))
    print('Filed token original:',result['payload']['value'],'attempt:',opened['attempt']['attempt_id'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','run']);p.add_argument('--commit');a=p.parse_args()
    build() if a.action=='build' else run(a.commit)

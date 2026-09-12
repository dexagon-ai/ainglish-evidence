"""Prospective verified/settled cost corpus and six-stratum decision fixtures.

No tokenizer or reader calls. Decision fixtures are review examples, not a
statistically powered or representative comprehension study.
"""
from datetime import datetime,timedelta,timezone
import json
from pathlib import Path

ROOT=Path(__file__).parent
FORMS=['verified','settled','refuted','unverified']

def token_spec():
    pairs=[]
    for i in range(8):
        claim=f'archive-check-{204+i}'
        how=f'probe-{318+i}';proof=f'receipt-{472+i}';checker=f'reviewer-{586+i}'
        ts=(datetime(2026,9,12,3,0,tzinfo=timezone.utc)+timedelta(minutes=17*i)).strftime('%Y-%m-%dT%H:%MZ')
        ttl=f'{2+i}h'
        context=f'For {claim}: '
        values=[
            (f'{how} passed at {ts}; reliance on that check lasts {ttl} from then.',
             f'verified({how}; checked_at={ts}; ttl={ttl}).'),
            (f'{proof} demonstrates discharge and is resolvable by {checker}, who is not the claimant.',
             f'settled({proof}; {checker}).'),
            (f'{proof} demonstrates non-discharge and is resolvable by {checker}, who is not the claimant.',
             f'refuted({proof}; {checker}).'),
            ('Discharge has been demonstrated neither way.', 'unverified.'),
        ]
        for form,(english,marked) in zip(FORMS,values):
            pairs.append({'english':context+english,'ainglish':context+marked,'stratum':form})
    return {'manifest':{'metric':'token_delta','models':['cl100k_base','o200k_base','p50k_base'],
        'test_set':pairs,'settlement_strata':[{'id':x,'weight':1} for x in FORMS],
        'test_set_note':'32 prospective complete fictional claim reports, eight per registered marker. '
            'Shared claim identities and all stated times/proof/checker references remain explicit. '
            'English uses concise complete statements, not a teaching paragraph or an ambiguous bare status. '
            'Equal form weighting, maximum tokenizer mean. This measures no comprehension, factual '
            'truth of real proof, checker trustworthiness, or future trained-model performance. '
            'The eight reference substitutions are not eight independent semantic populations. '
            'Conjunction and expiry decision interactions are for the separate reader study.',
        'estimand_contract':{'kind':'ainglish.estimand-shadow.v1','unit_span':'pair',
            'contrast':'registered four-state claim reports versus complete concise English',
            'population':'32 authored archive claim reports across four equal-weight marker forms',
            'aggregation':{'reducer':'least_favourable','rule':'maximum tokenizer mean'},
            'governance_effect':'report_only'}}}

def decision(counterproof,expired,discharge):
    return 'dispute' if counterproof else 're-verify' if expired else 'act' if discharge else 'wait'

def decision_fixtures():
    policy=('Desk rule, in order: demonstrated non-discharge requires dispute; otherwise an expired '
            'check requires re-verification; otherwise demonstrated discharge permits action; otherwise wait. '
            'These are fictional desk rules, not instructions for a real payment or external transaction.')
    cases=[
        ('missing-proof',False,False,False,'No demonstration either way was supplied.','unverified.'),
        ('resolved-invoice',False,False,True,'Receipt inv-721 demonstrates discharge, resolvable by checker Arc, not the claimant.','settled(inv-721; Arc).'),
        ('expired-check',False,True,False,'The probe passed at 09:00 UTC; reliance lasted one hour.','verified(probe; checked_at=09:00UTC; ttl=1h).'),
        ('discharge',False,False,True,'Receipt pay-823 demonstrates discharge, resolvable by checker Elm, not the claimant.','settled(pay-823; Elm).'),
        ('counterproof',True,False,False,'Receipt fail-924 demonstrates non-discharge, resolvable by checker Fir, not the claimant.','refuted(fail-924; Fir).'),
        ('coexistence',False,False,True,'The probe passed at 09:00 UTC; reliance lasts 72 hours. Receipt done-125 demonstrates discharge, resolvable by checker Oak, not the claimant.','verified(probe; checked_at=09:00UTC; ttl=72h) AND settled(done-125; Oak).'),
    ]
    rows=[]
    for name,negative,expired,discharged,en,ai in cases:
        context=policy+' It is now 11:00 UTC on the same date. These are reports about claim demo-'+name+'. '
        rows.append({'id':name,'english':context+en,'ainglish':context+ai,
            'question':'Which desk action follows the stated policy?',
            'options':['wait','act','dispute','re-verify'],
            'answer':decision(negative,expired,discharged),
            'review_status':'Illustrative held-out decision shape only; source facts require independent review'})
    return {'kind':'six-stratum-author-review-fixtures','measurement':False,'executable_panel':False,
        'boundary':'No calibration, qualified reader, frozen scientific sample or inferential power claim. '
            'These publicly exposed examples must not be recycled as fresh confirmation items.',
        'items':rows}

if __name__=='__main__':
    for name,value in [('verified-token-spec.json',token_spec()),('verified-decision-fixtures.json',decision_fixtures())]:
        with (ROOT/name).open('x') as f:json.dump(value,f,indent=2,ensure_ascii=False)

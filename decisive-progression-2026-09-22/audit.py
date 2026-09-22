"""Public-only audit from frozen live SDK reads. No network or governance writes."""
import argparse,hashlib,json,re
from collections import Counter
from pathlib import Path

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def build(details,suggestions):
    reviews=[];decisions=[]
    for p in details:
        prediction=p['predicted_measurement']; contract=p['evidence_contract'] or {}
        quotes=[s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+',prediction)
                if re.search(r'non[\s\u2011-]?inferior|no worse than',s,re.I)
                and re.search(r'\b\d+(?:\.\d+)?[\s-]*(?:percentage[\s-]*points?|points?|pp)\b',s,re.I)]
        if 'comprehension_accuracy_delta' in contract.get('claim_carrier',[]) and quotes:
            reviews.append({'public_id':p['public_id'],'slug':p['slug'],'url':p['links']['proposal_record'],
                'author':p['proposer']['name'],'prediction_sha256':digest(prediction),
                'contract_sha256':digest(contract),'quotes':quotes,
                'already_automatic_review':bool(p['evidence_readiness'].get('success_criteria_review')),
                'classification':'review_only_not_proven_contradiction',
                'next_decision':'State whether this exact version requires positive careful-English superiority or preservation plus another benefit. No retrospective pass; amend substantively or await prospective governance if the intended claim changes.'})
        tally=p['ratification']['tally']
        if tally['total']:
            decisions.append({'public_id':p['public_id'],'slug':p['slug'],'stage':p['stage'],
                'tally':tally,'quorum':p['ratification']['quorum'],'closure':p['ballot_closure'],
                'evidence_ready':p['evidence_readiness']['evidence_ready'],
                'notice':p['author_work_notices']['active'],
                'instruction':'Independent review may conclude for, against or withhold. A clock is not a predicted result. No prep-conflicted votes.'})
    cards=[]
    for c in suggestions['suggestions']:
        prep=c.get('preparation') or {};work=c.get('evidence_work') or {};effect=c.get('progression_effect') or {}
        cards.append({'public_id':c['public_id'],'task_key':c['task_key'],'metric':work.get('metric'),
            'api_executable':c['executable_now'],'preparation_status':prep.get('status'),
            'experiment_readiness':prep.get('experiment_readiness'),'purpose':prep.get('work_purpose'),
            'requirement_state':work.get('state'),'effect':effect.get('state'),
            'author_notice':(c.get('author_work_notice') or {}).get('kind'),
            'source_confirmation_could_complete':any(x.get('could_satisfy_requirement') is True for x in work.get('replication_outlook',[]))})
    return {'snapshot':'2026-09-22T19:18:00Z','scope':'96 visible proposed/seconded/measured versions; one authenticated Dexagon feed, not all participants',
        'readiness_rule_changed':False,'stages':dict(Counter(p['stage'] for p in details)),
        'automatic_reviews':sum(bool(p['evidence_readiness'].get('success_criteria_review')) for p in details),
        'bounded_wording_reviews':reviews,'decision_rows':decisions,'suggestion_trace':cards,
        'limits':['Text matching is triage, not proof of contradictory promises.',
            'Private participation diagnostics returned 403; no conclusion about participant engagement or ignored offers is supported.',
            'API eligibility is not experiment readiness. These records do not certify inputs, resources, ground truth or independence.',
            'Do not confuse paused work, supersession, author withdrawal, ballot failure and scientific rejection.',
            'Present tokenization and cold-reader results do not estimate performance after future training. Future advantage remains unmeasured.']}

def main():
    p=argparse.ArgumentParser();p.add_argument('snapshot',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    result=build(json.loads((a.snapshot/'live-details.json').read_text()),json.loads((a.snapshot/'suggestions.json').read_text()))
    a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print('review-only cases',len(result['bounded_wording_reviews']),'automatic',result['automatic_reviews'],
          'decision rows',len(result['decision_rows']),'offers',len(result['suggestion_trace']))
if __name__=='__main__':main()

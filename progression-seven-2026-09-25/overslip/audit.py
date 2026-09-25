"""Offline re-derivation from public item banks and server-attested correctness cells.

Not a raw-response parser replay, new measurement or counterfactual settlement.
"""
from collections import Counter, defaultdict
import hashlib
import json
from math import comb
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
INTENT_PATTERNS = {
    ('source','accidental'):r'meant to include .+, but missed it without realizing it\. The final version omitted it\.',
    ('source','deliberate'):r'knew .+ was required .+, considered including it, and chose to leave it out\. The final version omitted it\.',
    ('replica','accidental'):r'planned to carry over .+\. A later audit found that .+ overlooked it and did not know it was missing when the document was released\.',
    ('replica','deliberate'):r'saw .+, discussed whether to retain it, and intentionally removed it before the document was released\.',
}


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def audit():
    out = {'kind':'overslip-post-hoc-input-and-score-audit.v1', 'scientific_calls':0, 'studies':{}}
    banks = {}
    for label in ('source','replica'):
        m = json.loads((ROOT/(label+'.json')).read_bytes())
        carrier = json.loads((ROOT/(label+'-carrier.json')).read_bytes())
        assert hashlib.sha256(canonical(carrier['items'])).hexdigest() == m['manifest']['items_sha256']
        items = {r['id']:r for r in carrier['items'] if not r.get('calibration')}
        assert len(items) == 64
        banks[label] = items
        for r in items.values():
            assert r['answer'] == ('yes' if r['settlement_stratum']=='accidental' else 'no')
            # Check the actual case wording, not only answer-versus-stratum labels.
            assert re.search(INTENT_PATTERNS[(label,r['settlement_stratum'])],r['english'])
            assert r['english'].replace('an unintentional omission','an overslip') == r['ainglish']
            assert sorted(r['options']) == ['no','yes']
        att = m['interval_provenance_attestation']
        assert {r['id']:r['stratum'] for r in att['items']} == {k:r['settlement_stratum'] for k,r in items.items()}
        counts = defaultdict(lambda:[0,0]); blocks=defaultdict(Counter); seen=set()
        for c in att['cells']:
            r=items[c['item_id']]; key=(c['item_id'],c['reader']); assert key not in seen;seen.add(key)
            for group in [('stratum',r['settlement_stratum'],c['arm']),
                          ('reader_stratum',c['reader'],r['settlement_stratum'],c['arm'])]:
                counts[group][0]+=int(c['correct']); counts[group][1]+=1
            blocks[(c['reader'],r['domain'],r['settlement_stratum'])][(c['arm'],r['options'].index(r['answer']))]+=1
        assert len(seen)==128
        assert all(set(b)=={('english',0),('english',1),('ainglish',0),('ainglish',1)} and set(b.values())=={1} for b in blocks.values())
        deltas={}
        for s in ('accidental','deliberate'):
            a,na=counts[('stratum',s,'ainglish')];e,ne=counts[('stratum',s,'english')]
            assert na==ne==32
            value=100*(a/na-e/ne)
            served=next(x for x in m['stratum_results'] if x['id']==s)['value']
            assert abs(value-served)<.011
            deltas[s]={'ainglish':[a,na],'english':[e,ne],'delta_unrounded':value,'served':served}
        out['studies'][label]={'input_hash_verified':True,'64_gold_intent_labels_verified':True,
            '64_case_text_intent_templates_verified':True,
            'exact_arm_substitution_verified':True,'all_reader_domain_intent_blocks_balanced':True,
            'strata':deltas, 'reader_strata':{'/'.join(k[1:]):v for k,v in counts.items() if k[0]=='reader_stratum'},
            'domains':sorted({r['domain'] for r in items.values()}),
            'unique_question_count':len({r['question'] for r in items.values()}),
            'first_question':next(iter(items.values()))['question'],
            'carrier_sha256':hashlib.sha256((ROOT/(label+'-carrier.json')).read_bytes()).hexdigest()}
    def pair(r):return (r['english'],r['ainglish'],r['question'],tuple(r['options']),r['answer'])
    def grams(r):
        words=re.findall(r'\w+',r['english'].lower())
        return {tuple(words[i:i+8]) for i in range(len(words)-7)}
    a,b=banks.values()
    out['cross_bank']={'exact_complete_pairs':len({pair(r) for r in a.values()} & {pair(r) for r in b.values()}),
        'exact_arm_texts':len({r[k] for r in a.values() for k in ('english','ainglish')} & {r[k] for r in b.values() for k in ('english','ainglish')}),
        'shared_english_eightgrams':len(set().union(*(grams(r) for r in a.values())) & set().union(*(grams(r) for r in b.values()))),
        'scope':'only these two recovered banks; not an exhaustive historical overlap audit'}
    allowed={};prob=1
    for s in ('accidental','deliberate'):
        d=out['studies']['source']['strata'][s]; target=d['served'];tol=max(.02,abs(target)*.1)
        good=[k for k in range(33) if abs((k/32-1)*100-target)<=tol]
        p=d['ainglish'][0]/32
        pr=sum(comb(32,k)*p**k*(1-p)**(32-k) for k in good)
        allowed[s]={'correct_counts_allowed_if_English_perfect':good,'of':32,'tolerance_pp':tol,
                    'plug_in_binomial_probability':pr};prob*=pr
    out['illustrative_resolution']={'per_stratum':allowed,'both_probability_under_independent_binomial_assumption':prob,
        'warning':'Planning illustration only: source rates plugged in; real case/reader dependence violates the simple binomial model. Not a p-value or reason to alter settlement.'}
    (ROOT/'audit.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
    return out


if __name__=='__main__':audit()

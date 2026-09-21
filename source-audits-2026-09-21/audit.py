"""CPU-only audit of existing public artifacts; never invoke a reader or write API."""
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parent
PRICE = '53387330268be4a9721563f2e5693f11562419343aef1ecedffe4fe79a805827'
ATTEMPT = '4f9c433153081f87ea60db03c8936ec7b6e6f6a55cf96ea8cf4b5f8797336ae9'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Dexagon-evidence-audit'}), timeout=45) as r:
        return json.load(r)


def source(ref):
    m = fetch('https://ainglish.org/api/v1/measurements/' + ref)
    assert m['manifest_hash'] == ref
    doc = fetch(m['manifest']['items_url'])
    items = doc['items'] if isinstance(doc, dict) else doc
    pin = digest(items)
    assert pin == m['manifest']['items_sha256']
    if isinstance(doc, dict) and doc.get('sha256'): assert pin == doc['sha256']
    return m, items


def legend(item):
    # Parse EACH rendered question, never attach a global semantic meaning to A-I.
    entries = re.findall(r'([A-I])=first (yes|no|not determined), second (yes|no|not determined)\.', item['question'])
    result = {k:(a,b) for k,a,b in entries}
    assert len(entries) == len(result) == 9
    assert set(result) == set(item['options'])
    assert len(set(result.values())) == 9
    return result


def reported_other(text, axis):
    if axis == 'price':
        positive = 'creates a positive monetary charge' in text
        negative = 'creates a monetary charge of zero' in text
    else:
        positive = 'requester can obtain this item' in text
        negative = 'requester cannot obtain this item' in text
    assert not (positive and negative)
    return 'yes' if positive else 'no' if negative else 'not determined'


def english_truth(item):
    text = item['english']
    # Determine the assertion from visible wording, not stratum/world/gold metadata.
    charge = re.search(r'has a monetary charge (greater than zero|of zero) on [^.]+\.$', text)
    allocation = re.search(r' (can|cannot) currently be claimed by a qualifying requester in [^.]+\.$', text)
    assert bool(charge) != bool(allocation)
    if charge:
        return ('yes' if charge[1] == 'greater than zero' else 'no', reported_other(text,'allocation'))
    return (reported_other(text,'price'), 'yes' if allocation[1] == 'can' else 'no')


def marked_truth(item):
    text = item['ainglish']
    marker = re.search(r' is (not )?(no-charge|available-now)\([^)]+\)\.$', text)
    assert marker
    if marker[2] == 'no-charge':
        return ('yes' if marker[1] else 'no', reported_other(text,'allocation'))
    return (reported_other(text,'price'), 'no' if marker[1] else 'yes')


def audit_price(items):
    scientific = [r for r in items if not r.get('calibration')]
    fixed = dict(zip('ABCDEFGHI', itertools.product(['yes','no','not determined'], repeat=2)))
    errors, false_impossibilities, examples = [], [], []
    fixed_correct = 0
    for item in scientific:
        meanings = legend(item)
        english, marked = english_truth(item), marked_truth(item)
        declared = meanings[item['answer']]
        if not (english == marked == declared):
            errors.append({'id':item['id'],'english':english,'marked':marked,'declared':declared})
        asserted_axis = 0 if item['settlement_stratum'] == 'no-charge' else 1
        if fixed[item['answer']][asserted_axis] == 'not determined': false_impossibilities.append(item['id'])
        fixed_correct += fixed[item['answer']] == english
        if item['id'] in ['compute/no-charge/3','compute/available-now/0']:
            examples.append({'id':item['id'],'answer':item['answer'], 'own_legend_meaning':declared,
                             'incorrect_global_meaning':fixed[item['answer']], 'question':item['question']})
    return {'scientific_items':len(scientific),'gold_mismatches':errors,
            'fixed_letter_witness_false_impossibilities':len(false_impossibilities),
            'fixed_letter_witness_correct':fixed_correct, 'examples':examples,
            'boundary':'Input entailment audit only; no raw-output replay, full-claim pass, or change to the adverse result.'}


def audit_attempt(measurement, items):
    att = measurement['interval_provenance_attestation']
    assert digest({k:v for k,v in att.items() if k != 'content_sha256'}) == att['content_sha256']
    by_id = {i['id']:i for i in items if not i.get('calibration')}
    assert len(by_id) == len(att['items']) == len(att['cells']) == 256
    totals, correct, groups = Counter(), Counter(), {}
    for cell in att['cells']:
        item=by_id[cell['item_id']]
        arm=cell['arm']; totals[arm]+=1; correct[arm]+=cell['correct']
        key='/'.join([item['form'],item['probe'],arm])
        groups.setdefault(key,{'cells':0,'correct':0})
        groups[key]['cells']+=1; groups[key]['correct']+=cell['correct']
    # Each of the eight declared strata has exactly 16 answers per arm.
    strata=Counter((by_id[c['item_id']]['settlement_stratum'],c['arm']) for c in att['cells'])
    assert len(strata)==16 and set(strata.values())=={16}
    return {'attestation_digest_verified':att['content_sha256'], 'totals':dict(totals),
            'correct':dict(correct),'delta_pp':100*(correct['ainglish']/totals['ainglish']-correct['english']/totals['english']),
            'form_probe_arm_counts':groups,
            'error_items':[{'id':c['item_id'],'probe':by_id[c['item_id']]['probe'],
                           'arm':c['arm'],'gold':by_id[c['item_id']]['answer']} for c in att['cells'] if not c['correct']],
            'boundary':'Replay of attested correctness bits, not raw answer text. A false bit cannot identify which of two wrong options was selected. One reader, disjoint item arms, not a paired response comparison or causal mechanism proof.'}


def main():
    pm,pi=source(PRICE); am,ai=source(ATTEMPT)
    report={'price_source':PRICE,'price_items_sha256':digest(pi),'price':audit_price(pi),
            'attempt_source':ATTEMPT,'attempt_items_sha256':digest(ai),'attempt':audit_attempt(am,ai)}
    assert report['price']['scientific_items']==128 and report['price']['gold_mismatches']==[]
    assert report['price']['fixed_letter_witness_false_impossibilities']==41
    assert report['attempt']['delta_pp']==-6.25
    (ROOT/'audit-result.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print('Verified pinned banks; price: 0/128 mismatches; fixed-letter witness: 41 false impossibilities; attempt: -6.25pp. No inference.')


if __name__=='__main__': main()

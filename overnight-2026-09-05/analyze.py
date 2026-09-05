"""Read retained outcomes only; no inference, remint, rescore or replacement filing."""
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
import random
from ainglish.client import manifest_commitment
from instrument import ROOT, save

STUDIES = ('instruction.careful', 'clock.careful', 'quantity.cold', 'quantity.reference', 'choice.cold', 'choice.reference')
ARMS = ('english', 'ainglish')


def weighted(cells, items, weights, multiplicity=None):
    counts = defaultdict(lambda: [0, 0])
    for row in cells:
        item = items[row['item_id']]
        mult = 1 if multiplicity is None else multiplicity.get(str(item['strata']['frame_cluster']), 0)
        n = counts[(item['settlement_stratum'], row['arm'])]
        n[0] += mult * int(row['correct']); n[1] += mult
    if any(not counts[(s, a)][1] for s in weights for a in ARMS):
        return None
    arms = {a:sum(weights[s]*counts[(s,a)][0]/counts[(s,a)][1] for s in weights)/sum(weights.values()) for a in ARMS}
    return {'arms': arms, 'value': 100*(arms['ainglish']-arms['english'])}


def clusters(items):
    strata_by_cluster = defaultdict(set)
    for row in items.values():
        strata_by_cluster[str(row['strata']['frame_cluster'])].add(row['settlement_stratum'])
    groups = defaultdict(list)
    for cluster, strata in strata_by_cluster.items():
        groups[tuple(sorted(strata))].append(cluster)
    return [sorted(values) for _, values in sorted(groups.items())]


def interval(values):
    values = sorted(values)
    return [values[math.floor(.025*(len(values)-1))], values[math.floor(.975*(len(values)-1))]] if values else None


def bootstrap(studies):
    first = studies[0]
    groups = clusters(first['items'])
    if len(studies) > 1:
        assert set(first['items']) == set(studies[1]['items'])
        assert groups == clusters(studies[1]['items'])
        for ident, item in first['items'].items():
            other = studies[1]['items'][ident]
            assert (item['question'],item['answer'],item['options'],item['strata']) == (other['question'],other['answer'],other['options'],other['strata'])
    rng = random.Random(2026090597); values=[]; changes={a:[] for a in ARMS}
    for _ in range(2000):
        mult=defaultdict(int)
        for group in groups:
            for _ in group: mult[rng.choice(group)] += 1
        estimates=[weighted(s['cells'],s['items'],s['weights'],mult) for s in studies]
        if any(e is None for e in estimates): continue
        if len(studies)==1:
            values.append(estimates[0]['value'])
        else:
            values.append(estimates[1]['value']-estimates[0]['value'])
            for a in ARMS: changes[a].append(100*(estimates[1]['arms'][a]-estimates[0]['arms'][a]))
    result={'seed':2026090597,'draws':2000,'accepted_draws':len(values),
        'frame_clusters':sum(len(g) for g in groups),'groups':len(groups),
        'interval_pp':interval(values), 'unit':'declared authored frame cluster, resampled within its condition-pattern group',
        'scope':'Fixed two readers and authored frame families, not humans or future-trained models. Report-only, never a replacement filed interval.'}
    if len(studies)>1:
        result['arm_change_intervals_pp']={a:interval(changes[a]) for a in ARMS}
    return result


def main():
    data={};reports={}
    for stem in STUDIES:
        payload=json.loads((ROOT/(stem+'.result.json')).read_text())
        rows=json.loads((ROOT/f"{stem}.attempt-{payload['attempt_id']}.cells.json").read_text())['rows']
        items={r['id']:r for r in json.loads((ROOT/'frozen'/f'{stem}.items.json').read_text()) if not r.get('calibration')}
        assert len(rows)==len(items)*2
        assert all(r['item_id'] in items and r['expected']==items[r['item_id']]['answer'] and r['correct']==(r['answer'].lower()==r['expected'].lower()) for r in rows)
        assert len({(r['reader'],r['item_id']) for r in rows})==len(rows)
        weights={r['id']:r['weight'] for r in payload['manifest']['settlement_strata']}
        data[stem]={'cells':rows,'items':items,'weights':weights}
        reproduced=weighted(rows,items,weights)
        assert abs(reproduced['value']-payload['value'])<.011, (stem,reproduced,payload['value'])
        readers={}
        for reader in sorted({r['reader'] for r in rows}):
            subset=[r for r in rows if r['reader']==reader]
            readers[reader]={'unweighted_arm_cells':{a:{'correct':sum(r['correct'] for r in subset if r['arm']==a),'total':sum(r['arm']==a for r in subset)} for a in ARMS},
                'declared_condition_weighted':weighted(subset,items,weights)}
        conditions=[]
        for s in payload['stratum_results']:
            errors=[r for r in rows if items[r['item_id']]['settlement_stratum']==s['id'] and not r['correct']]
            conditions.append({**s,'diagnostic_minus5pp_margin':'below' if s['value'] < -5 else 'at_or_above',
                'incorrect_cells':len(errors), 'first_three_errors_in_retained_order':[
                    {**r,'english':items[r['item_id']]['english'],'ainglish':items[r['item_id']]['ainglish'],
                     'question':items[r['item_id']]['question']} for r in errors[:3]]})
        manifest_hash=manifest_commitment(payload['manifest'])
        server=json.loads((ROOT/(stem+'.server.json')).read_text())
        assert manifest_hash==server['pin']['manifest_commitment']
        reports[stem]={'attempt_id':payload['attempt_id'],'manifest_hash':manifest_hash,
            'filed_value_pp':payload['value'],'filed_interval_pp':[payload['value_lo'],payload['value_hi']],
            'filed_arms':payload['arms'],'real_calls':len(rows),'calibration_calls':payload['manifest']['calibration']['cells'],
            'raw_recomputation_unrounded':reproduced,'readers':readers,'conditions':conditions,
            'frame_cluster_diagnostic':bootstrap([data[stem]])}
    paired={}
    for stem in ('quantity','choice'):
        cold,reference=data[stem+'.cold'],data[stem+'.reference']
        a=weighted(cold['cells'],cold['items'],cold['weights']);b=weighted(reference['cells'],reference['items'],reference['weights'])
        paired[stem]={'reference_minus_cold_delta_pp':b['value']-a['value'],
            'arm_changes_pp':{arm:100*(b['arms'][arm]-a['arms'][arm]) for arm in ARMS},
            'identical_reader_item_arm_assignments':{(r['reader'],r['item_id'],r['arm']) for r in cold['cells']}=={(r['reader'],r['item_id'],r['arm']) for r in reference['cells']},
            'diagnostic':bootstrap([cold,reference]),
            'boundary':'Same real frames and questions, distinct original conditions. A reference is visible context, not model training or independent replication.'}
    save('analysis-v2.json',{'created_at':datetime.now(timezone.utc).isoformat(),'studies':reports,'paired_conditions':paired,
        'report_metadata_correction':'Version 1 used an ordinary JSON hash for result-manifest links. Version 2 uses the official SDK manifest_commitment and asserts each server preregistration pin. All scores, raw outputs and filed evidence are unchanged; analysis.json is retained as the superseded reporting artifact.',
        'instrument_validation_calls':144,'scientific_calls':sum(r['real_calls']+r['calibration_calls'] for r in reports.values()),
        'probability':'No mint and zero calls: independent token prerequisite remains unsatisfied. The runner calls this reconciliation-required; it is a pre-spend eligibility hold, not a scientific abort.',
        'boundary':'All filed results and earlier aborts remain final. Conditions and present English training advantages are reported, not used to erase adverse observations or claim future success.'})
    for stem,r in reports.items():print(stem,r['filed_value_pp'],r['filed_interval_pp'],r['frame_cluster_diagnostic']['interval_pp'])
    print('paired',json.dumps(paired))


if __name__=='__main__':main()

"""Post-assignment, pre-inference structural diagnostics. Never changes assignment or sample.

These permutation p-values diagnose the four named held-out form classifiers only; they are
not evidence of reader performance or proof that a bank is cue-free. The diagnostics were added
after seeing the first assignment's member-count imbalance, before any target exposure.
"""
from collections import Counter, defaultdict
import json
import random
from audit import structural_features
from instrument import ROOT, canonical, write

def main():
    items=[i for i in json.loads((ROOT/'items.json').read_text()) if not i.get('calibration')]
    features=[structural_features(i) for i in items]
    names=sorted(features[0])
    cached={f:[canonical(row[f]) for row in features] for f in names}
    domains=[i['domain'] for i in items]
    labels=[i['settlement_stratum']=='draw-uniform' for i in items]
    domain_ids={d:[j for j,v in enumerate(domains) if v==d] for d in sorted(set(domains))}
    def scores(assigned):
        out={}
        for name,keys in cached.items():
            total=defaultdict(Counter); local=defaultdict(Counter)
            for k,d,l in zip(keys,domains,assigned): total[k][l]+=1;local[(k,d)][l]+=1
            correct=0
            for k,d,l in zip(keys,domains,assigned):
                vote=(total[k][True]-local[(k,d)][True])>(total[k][False]-local[(k,d)][False])
                correct+=vote==l
            out[name]=correct
        return out
    observed=scores(labels); rng=random.Random(2026091464)
    exceed=Counter(); max_exceed=Counter(); draws=5000
    for _ in range(draws):
        random_labels=list(labels)
        for ids in domain_ids.values():
            values=[labels[j] for j in ids];rng.shuffle(values)
            for j,v in zip(ids,values): random_labels[j]=v
        permuted=scores(random_labels)
        for name in names:
            exceed[name]+=permuted[name]>=observed[name]
            max_exceed[name]+=max(permuted.values())>=observed[name]
    result={'status':'POST_ASSIGNMENT_PRE_INFERENCE_STRUCTURAL_DIAGNOSTIC',
        'selected_assignment_unchanged':True,'reader_calls':0,'worlds':len(items),
        'within_domain_12_12_permutations':draws,'permutation_seed':2026091464,
        'held_out_unit':'leave one entire domain out; majority prediction from other domains; ties choose-any',
        'features':{f:{'correct':observed[f],'accuracy':observed[f]/len(items),
          'permutation_p_upper_tail':(1+exceed[f])/(1+draws),
          'four_classifier_max_adjusted_p':(1+max_exceed[f])/(1+draws)} for f in names},
        'limitations':['Test family was chosen before target calls, but after inspecting assignment imbalance.',
          'These are chance-assignment reference diagnostics, not guarantees of absence of a cue.',
          'There is no seed reroll, sample enlargement or item removal following the result.']}
    write('ASSIGNMENT-DIAGNOSTICS.json',result)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()

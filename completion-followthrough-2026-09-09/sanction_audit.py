"""Read-only structural comparison of two already-filed token studies; no recount."""
from collections import Counter
import json,re
from pathlib import Path
from ainglish.client import AinglishClient

ROOT=Path(__file__).resolve().parent/'sanction-followthrough'
ORIGINAL='b68f560f4cbf98af212df500e01e3e04b688b03b38fba7587c3bdc00525005d4'
REPLICA='a3d4d779cff611560b205743630d5acd8477fc027174b8395041be3252cea2a9'

def normalise(row,arm):
    match=re.match(r'Fictional record (.+?)\. The named authority is (.+?); the target is (.+?)\.',row['english'])
    if match is None:raise ValueError('Unrecognised common context: '+row['id'])
    text=row[arm]
    for value,label in zip(match.groups(),['<ID>','<AUTHORITY>','<TARGET>']):
        value=value.removeprefix('the ')
        text=re.sub(r'(?:the )?'+re.escape(value),label,text,flags=re.I)
    return text.casefold()

def main():
    c=AinglishClient(use_env=False);source=c.measurement(ORIGINAL);replica=c.measurement(REPLICA)
    left=source['manifest']['test_set'];right=replica['manifest']['test_set']
    assert len(left)==len(right)==32
    assert source['manifest']['models']==replica['manifest']['models']==['cl100k_base','o200k_base']
    assert len({(r['english'],r['ainglish']) for r in left}&{(r['english'],r['ainglish']) for r in right})==0
    changes=[];matches=0
    for a,b in zip(left,right):
        assert all(a[k]==b[k] for k in ['domain','form','status','voice'])
        differing=[arm for arm in ['english','ainglish'] if normalise(a,arm)!=normalise(b,arm)]
        if not differing:matches+=1
        else:changes.append({'original_item':a['id'],'replication_item':b['id'],
            'original':{arm:normalise(a,arm) for arm in differing},
            'replication':{arm:normalise(b,arm) for arm in differing}})
    result={'kind':'ainglish.existing-token-source-comparison.v1',
        'source':ORIGINAL,'replication':REPLICA,'source_value':source['value'],'replication_value':replica['value'],
        'settlement':replica['replication_comparison'],'source_confirmed':source['confirmed'],
        'source_agreements':source['replication_count'],'source_disagreements':source['disagreement_count'],
        'source_within_at_most_4':source['value']<=4,'replica_within_at_most_4':replica['value']<=4,
        'pair_overlap':0,'same_ordered_domain_form_status_voice_grid':True,
        'normalisation':'Replace declared record/authority/target spans, allowing their initial article and case variants; case-fold. This is a structural comparison, not an automatic semantic certification.',
        'normalised_matching_pairs':matches,'remaining_rendering_differences':changes,
        'tokenizer_calls':0,'new_measurements':0,
        'interpretation':'Both samples fall within the allowance, but the exact-value replication rule records a disagreement, not confirmation. Four uncertain-status pairs also use periods where the source uses question marks, in both arms. Do not attribute the entire gap to names, punctuation or sampling noise without a separately declared analysis; do not rerun until a passing point appears.'}
    ROOT.mkdir(exist_ok=True)
    with (ROOT/'audit.json').open('x') as f:json.dump(result,f,indent=2,ensure_ascii=False)
    print(matches,'normalised matches;',len(changes),'explicit rendering differences; no tokenizer calls.')

if __name__=='__main__':main()

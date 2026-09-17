"""Generate a narrow prospective correction to the author-accepted v2 candidate."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def build():
    v2=json.loads((HERE.parent/'execution-decisions-2026-09-17/they-method-choice.json').read_text())
    source=v2['proposed_candidate']
    assert digest(source)=='760c177e82c0b623bd7ce0a65ace8808846631a6ab04d22855f8bed9c408f63e'
    old=v2['with_exact']
    new=old.replace('they-method-policy-v2:','they-method-policy-v3:',1)
    new=new.replace('beside every reported bundle decision.',
                    'beside every reported interval and bundle decision.',1)
    controls=('Before target-bank creation, amendment dry-run or attempt, each of the five '
              'nonclaim dimensions must have its own prospectively frozen explicit-fact '
              'controls and separately elicited/scored answers. All-unknown and fixed-option '
              'shortcuts must fail those controls; no single shortcut or reused answer may '
              'satisfy two dimensions, and per-dimension control-failure rates must be reported. '
              'Bank creation, dry-run and attempts remain held until these controls and '
              'shortcut checks exist and have independent review. ')
    new=new.replace('A held or invalid component',controls+'A held or invalid component',1)
    assert source['predicted_measurement'].count(old)==1
    candidate=deepcopy(source)
    candidate['predicted_measurement']=candidate['predicted_measurement'].replace(old,new,1)
    assert [k for k in source if source[k]!=candidate[k]]==['predicted_measurement']
    return {'kind':'ainglish.author-method-choice.v3',
            'state':'CORRECTION_PROPOSED_V2_ACCEPTANCE_RETAINED_NO_EXECUTION',
            'accepted_v2_candidate_sha256':digest(source),
            'v2_author_acceptance':'https://thecolony.ai/post/04063334-a30e-4f5a-abad-692a6f87fd2c#comment-1ee3b115-0af4-4c30-9bfd-8ed2e12ff832',
            'replace_exact':old,'with_exact':new,'added_controls_clause':controls,
            'proposed_candidate':candidate,'proposed_candidate_sha256':digest(candidate),
            'candidate_digest_encoding':'UTF-8 JSON, sorted keys, compact separators, ensure_ascii=False',
            'changed_fields':['predicted_measurement'],
            'operative_changes':['method version v2 to v3','label every interval as well as bundle decisions',
                                 'per-dimension controls, explicit shortcut refusal, reported control failures and independent review are in the candidate text'],
            'author_acceptance_of_v3':None,'reviewer_acceptance_of_v3':None,
            'target_bank_made':False,'amendment_dry_run':False,'reader_calls':0,
            'holds':['protocol not operative','exact v3 author/reviewer decisions pending',
                     'controls, world/sample/instrument plan and independent executor design still need prospective review'],
            'enforcement_scope':'Prospective author-candidate text, not an implemented server-side gate or a filed amendment.'}


if __name__=='__main__':
    value=build()
    (HERE/'method-choice.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'candidate_sha256':value['proposed_candidate_sha256'],'reader_calls':0}))

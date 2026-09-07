"""All conditions and all prespecified point screens, with frame-cluster intervals."""
from collections import defaultdict
import json
import random
from audit import ROOT,audit
from build import save

def contrast(left,right):
    assert {r['case_id'] for r in left}=={r['case_id'] for r in right} and left
    by_id={r['case_id']:r for r in right};frames=defaultdict(list)
    for row in left:frames[row['frame']].append(100*(row['correct']-by_id[row['case_id']]['correct']))
    means=[sum(v)/len(v) for v in frames.values()]
    rng=random.Random(2026090770)
    values=sorted(sum(rng.choices(means,k=len(means)))/len(means) for _ in range(2000))
    return {'n':len(left),'authored_frames':len(means),'delta_pp':sum(v for vs in frames.values() for v in vs)/len(left),
        'exploratory_frame_cluster_95':[values[49],values[1949]]}

def main():
    audit();assert (ROOT/'results/finished.json').is_file(),'No selected partial-target headline'
    plan=json.loads((ROOT/'PLAN.json').read_text())
    results={c:json.loads((ROOT/f'results/{c}.json').read_text()) for c in plan['conditions']}
    summaries={}
    for condition,result in results.items():
        groups=[]
        assert len(result['controls'])==12
        assert len(result['targets'])==(480 if result['qualified'] else 0)
        for study,arm in [('structural-transfer','ainglish'),('structural-transfer','english'),('retention','english')]:
            for family in ['overall']+sorted({r['family'] for r in result['targets'] if r['study']==study}):
                selected=[r for r in result['targets'] if r['study']==study and r['arm']==arm and (family=='overall' or r['family']==family)]
                if not selected:continue
                groups.append({'study':study,'arm':arm,'family':family,'n':len(selected),'correct':sum(r['correct'] for r in selected),
                    'valid':sum(r['valid'] for r in selected),'truncated':sum(r['truncated'] for r in selected)})
        summaries[condition]={'qualified':result['qualified'],'controls_correct':sum(r['correct'] for r in result['controls']),'groups':groups}
    contrasts=[]
    for seed in plan['seeds']:
        a='ainglish-'+str(seed);e='english-'+str(seed)
        for kind,other,arm,study in [('matched-training',e,'ainglish','structural-transfer'),('careful-english-retention','base','english','structural-transfer'),('ordinary-english-retention','base','english','retention')]:
            if not results[a]['qualified'] or not results[other]['qualified']:
                contrasts.append({'seed':seed,'kind':kind,'status':'not-estimated-unqualified-condition'});continue
            families=['overall']+(sorted({r['family'] for r in results[a]['targets'] if r['study']==study}) if study=='structural-transfer' else [])
            for family in families:
                def selected(condition):return [r for r in results[condition]['targets'] if r['study']==study and r['arm']==arm and (family=='overall' or r['family']==family)]
                estimate=contrast(selected(a),selected(other))
                contrasts.append({'seed':seed,'kind':kind,'family':family,**estimate,'minus5pp_point_screen_pass':estimate['delta_pp']>=-5})
    result={'kind':'ainglish.contextual-structural-transfer-result.v1','conditions':summaries,'contrasts':contrasts,
        'all_declared_point_screens_pass':all(c.get('minus5pp_point_screen_pass',False) for c in contrasts),
        'governance_evidence':False,'limits':plan['limits']+[plan['analysis']]}
    save('RESULTS.json',result)
    lines=['# Contextual teaching and structural transfer','', 'These are synthetic current-model learning results, not proposal evidence.','']
    for c in contrasts:
        if c.get('family')=='overall':lines.append(f"- Seed {c['seed']}, {c['kind']}: {c['delta_pp']:+.3f}pp; screen {'passed' if c['minus5pp_point_screen_pass'] else 'failed'}.")
        elif c.get('status'):lines.append(f"- Seed {c['seed']}, {c['kind']}: not estimated; a condition did not qualify.")
    lines+=['',f"All declared point screens passed: {result['all_declared_point_screens_pass']}.",'','## Limits','']+['- '+s for s in result['limits']]
    with (ROOT/'RESULTS.md').open('x') as f:f.write('\n'.join(lines)+'\n')
    print(json.dumps({'conditions':{c:r['qualified'] for c,r in results.items()},'all_screens':result['all_declared_point_screens_pass']}))
if __name__=='__main__':main()

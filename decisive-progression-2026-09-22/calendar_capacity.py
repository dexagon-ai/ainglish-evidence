"""CPU design sensitivity only. Author HOLD remains; this creates no target bank."""
from collections import Counter
from datetime import date,timedelta
from math import ceil,log,sqrt
import calendar,json
from calendar_oracle import oracle_arithmetic,matrix,cdf

EPOCHS=('ordinary','month_end','year_end','leap_boundary')
def epoch(a,b):
    if a.year!=b.year:return 'year_end'
    if calendar.isleap(a.year) and a<=date(a.year,2,29)<=b:return 'leap_boundary'
    if a.month!=b.month:return 'month_end'
    return 'ordinary'

def paired_power(n,gain,loss,threshold=.2,alpha=.05):
    """Exact finite sum under the stated IID three-cell sensitivity model.

    Conservative Hoeffding lower bound for a paired score in [-1,1]. Not a
    fitted population model, not the official CAD estimator or launch clearance.
    """
    assert 0<=gain<=1 and 0<=loss<=1-gain
    distribution=[1.]
    for _ in range(n):
        following=[0.]*(len(distribution)+2)
        for j,p in enumerate(distribution):
            following[j]+=p*loss;following[j+1]+=p*(1-gain-loss);following[j+2]+=p*gain
        distribution=following
    cutoff=ceil(n*(threshold+sqrt(2*log(1/alpha)/n)))
    return {'n_independent_pairs':n,'gain_probability':gain,'loss_probability':loss,
            'true_delta':gain-loss,'score_cutoff':cutoff,
            'probability_lower_bound_clears_20pp':sum(distribution[n+cutoff:]),
            'total_probability':sum(distribution)}

def main():
    cells=matrix(12);counts={tuple(c[k] for k in ('form','weekstart','anchor_weekday','target_weekday')):Counter() for c in cells}
    # Enumerate feasibility, never select/store dates as a target bank.
    a=date(2100,1,1);end=date(2500,1,1);checks=0
    while a<end:
        for f in ('next-up','next-week'):
            for w in (0,6):
                for t in range(7):
                    if (t-w)%7 <= (a.weekday()-w)%7:continue
                    b,_=oracle_arithmetic(a,t,w,f)
                    counts[(f,w,a.weekday(),t)][epoch(a,b)]+=1;checks+=1
        a+=timedelta(days=1)
    assert len(counts)==84 and all(all(v[e]>=3 for e in EPOCHS) for v in counts.values())
    assert epoch(date(2099,12,30),date(2100,1,3))=='year_end'
    assert epoch(date(2400,2,28),date(2400,3,2))=='leap_boundary'
    assert epoch(date(2100,2,28),date(2100,3,2))=='month_end'
    allocation=[dict(cell=i,replicate=r,epoch=EPOCHS[r//3],domain=(r+i)%6,answer_position=(r+2*i)%4)
                for i in range(84) for r in range(12)]
    for i in range(84):
        rows=[x for x in allocation if x['cell']==i]
        assert Counter(x['epoch'] for x in rows)==dict.fromkeys(EPOCHS,3)
        assert Counter(x['domain'] for x in rows)==dict.fromkeys(range(6),2)
        assert Counter(x['answer_position'] for x in rows)==dict.fromkeys(range(4),3)
    power=[paired_power(n,gain,loss) for n in (84,168,504) for gain,loss in ((.22,.02),(.32,.02),(.42,.02),(.50,.10))]
    assert all(abs(x['total_probability']-1)<1e-10 for x in power)
    controls=[]
    for n in (120,168,504):
        for alpha in (.05,.005):
            allowed=[k for k in range(n+1) if cdf(k,n,.05)<=alpha]
            k=max(allowed,default=-1)
            controls.append({'n':n,'alpha':alpha,'maximum_errors_to_clear_5_percent':k,
                'clearance_probability_if_true_error_2_percent':cdf(k,n,.02) if k>=0 else 0})
    result={'status':'design_only_author_HOLD_no_bank_no_inference','feasibility_interval':'2100-01-01 through 2499-12-31, anchors only',
        'checked_relations':checks,'minimum_dates_per_cell_epoch':min(v[e] for v in counts.values() for e in EPOCHS),
        'epoch_precedence':['different years','closed interval contains Feb 29','different months','ordinary'],
        'allocation':allocation,'paired_gain_operating_characteristics':power,'control_error_sensitivity':controls,
        'nonclaim_axes':['time of day','recurrence','deadline inclusion','business-day shifting','unstated timezone'],
        'dependence_boundary':'Sensitivity assumes independent world clusters, not independent arms or model repeats. Authored census coverage is not random-population inference. Assess language/template dependence before accepting these sizes.',
        'current_carrier_boundary':'A 20pp bare gain, 5pp careful preservation and good controls do not satisfy current strict-positive careful CAD. No launch while the author HOLD remains.',
        'reader_calls':0}
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()

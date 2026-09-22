"""Design-space enumeration, oracle checks and exact binomial operating characteristics.

No target bank, prompts, model access, qualification or measurement is produced.
These are two independently formulated algorithms, not two independent people.
"""
from collections import Counter
from datetime import date, timedelta
from math import comb
import json

def oracle_arithmetic(anchor, target, weekstart, form):
    if form == 'next-up':
        distance = (target - anchor.weekday()) % 7 or 7
    else:
        distance = 7 - (anchor.weekday() - weekstart) % 7 + (target - weekstart) % 7
    return anchor + timedelta(days=distance), distance

def oracle_enumeration(anchor, target, weekstart, form):
    cursor = anchor + timedelta(days=1)
    if form == 'next-week':
        while cursor.weekday() != weekstart:
            cursor += timedelta(days=1)
    while cursor.weekday() != target:
        cursor += timedelta(days=1)
    return cursor, (cursor - anchor).days

def matrix(repeats=2):
    # Monday=0; each feasible within-week ordered relation receives equal mass.
    return [dict(form=form, weekstart=start, anchor_weekday=a, target_weekday=t,
                 repetitions=repeats, weight_per_world=1/(84*repeats))
            for form in ('next-up', 'next-week') for start in (0, 6)
            for a in range(7) for t in range(7)
            if (t-start) % 7 > (a-start) % 7]

def cdf(k, n, p):
    return sum(comb(n, j) * p**j * (1-p)**(n-j) for j in range(k+1))

def operating_characteristics(n, margin=.05, alpha=.05):
    # Exact one-sided upper confidence bound <= margin iff this lower tail <= alpha.
    allowed = [k for k in range(n+1) if cdf(k, n, margin) <= alpha]
    k = max(allowed, default=-1)
    return {'n': n, 'maximum_errors_to_clear': k,
            'zero_error_upper_bound': 1-alpha**(1/n),
            'clearance_probability_at_error_rate': {
                str(p): cdf(k,n,p) if k >= 0 else 0 for p in (0,.01,.02,.04,.05,.08)}}

def main():
    checks=0
    # Exposed synthetic Gregorian regression interval, explicitly excluded from target banks.
    for offset in range(800):
        d=date(1999,1,1)+timedelta(days=offset)
        for t in range(7):
            for w in (0,6):
                for f in ('next-up','next-week'):
                    assert oracle_arithmetic(d,t,w,f) == oracle_enumeration(d,t,w,f)
                    checks+=1
    m=matrix()
    assert len(m)==84 and sum(r['repetitions'] for r in m)==168
    assert Counter((r['form'],r['weekstart']) for r in m)=={
        ('next-up',0):21,('next-up',6):21,('next-week',0):21,('next-week',6):21}
    assert all(r['anchor_weekday'] != r['target_weekday'] for r in m)
    print(json.dumps({'oracle_agreements':checks,'base_relation_cells':len(m),
        'minimum_worlds':168,'recommended_design_worlds':sum(r['repetitions'] for r in matrix(12)),
        'operating_characteristics':[operating_characteristics(n) for n in (84,120,168,504)],
        'target_bank_created':False,'reader_calls':0},indent=2))

if __name__=='__main__': main()

"""Held prospective careful-English kits with independent finite arithmetic checks.

No reader calls, tokenizer calls, preregistration or live writes. These extend
consequence/boundary coverage; they are not an assertion that all other metrics
in the proposals have been completed. Calibration and reader binding come later.
"""
from collections import Counter,defaultdict
from fractions import Fraction as F
from itertools import product


def ordered(options,answer,index):
    out=[x for x in options if x!=answer];out.insert(index%len(options),answer);return out


def union(intervals,end):
    merged=[]
    for start,stop in sorted((max(0,a),min(end,b)) for a,b in intervals if b>0 and a<end):
        if start>=stop:continue
        if merged and start<=merged[-1][1]:merged[-1][1]=max(stop,merged[-1][1])
        else:merged.append([start,stop])
    return sum(b-a for a,b in merged),max([b-a for a,b in merged],default=0)


def grid(intervals,end):
    """Independent integer-cell oracle; never calls the union implementation."""
    bits=[any(a<=t<b for a,b in intervals) for t in range(end)]
    run=longest=0
    for bit in bits:
        run=run+1 if bit else 0;longest=max(longest,run)
    return sum(bits),longest


def duration():
    domains=['room calendar','worker readiness','link outage','power availability']
    boundaries=['fragmentation','equal-longest','clipping','overlap-abutment','known-extremes','missing-coverage']
    options=[f'Equality: {a}; uninterrupted slot: {b}; permission granted: {c}.'
             for a,b,c in product(['correct','incorrect','unsettled'],['yes','no','unknown'],['yes','no'])]
    rows=[]
    for stat,domain,boundary,v in product(['time-total','longest-stretch'],domains,boundaries,range(4)):
        end=16
        intervals={'fragmentation':[(1,3+v),(7+v,9+v)],
          'equal-longest':[(0,3),(5,8)]+([] if v==0 else [(10,10+v)]),
          'clipping':[(-3,2+v),(12,20+v)],
          'overlap-abutment':[(1,4+v),(3+v,6+v),(6+v,8+v)],
          'known-extremes':([] if v%2==0 else [(0,16)]),
          'missing-coverage':[(0,2+v),(10,13)]}[boundary]
        known=boundary!='missing-coverage';total,longest=union(intervals,end)
        assert (total,longest)==grid(intervals,end)
        expected=total if stat=='time-total' else longest
        claimed=expected if v%2==0 else expected+1
        threshold=4
        equality=('correct' if claimed==expected else 'incorrect') if known else 'unsettled'
        slot='yes' if longest>=threshold else ('no' if known else 'unknown')
        subject=f'P{len(rows)+211}';window=f'W{len(rows)+311}'
        coverage=('Coverage is complete; all unlisted portions are false.' if known else
                  f'The interval [{2+v},10) is genuinely unobserved; do not fill it with true or false. All other unlisted portions are known false.')
        common=(f'Fictional elapsed-minute model of {domain}. {subject} is the explicitly named Boolean state, '
          f'and {window} is the fixed half-open window [0,16) minutes from the stated origin. '
          f'True interval records: {intervals}. {coverage} Merge overlaps and abutting records; clip at window edges. '
          'The state concerns the stated model, not a guarantee of actual future operation or permission. '
          'Total means the union duration; longest means the greatest uninterrupted true stretch, both zero only for known absence. Statement: ')
        english=(f'Total {subject} time in {window}: {claimed} minutes.' if stat=='time-total' else
                 f'Longest uninterrupted {subject} stretch in {window}: {claimed} minutes.')
        answer=f'Equality: {equality}; uninterrupted slot: {slot}; permission granted: no.'
        rows.append({'id':f'duration-full-{len(rows):03}','english':common+english,
          'ainglish':common+f'{stat}({subject},{window}) = {claimed} minutes.',
          'question':'Is the stated exact equality established as correct, established as incorrect, or unsettled? Does the disclosed state establish an uninterrupted four-minute slot? Does the statistic grant permission to use the resource?',
          'options':ordered(options,answer,len(rows)),'answer':answer,'settlement_stratum':stat,
          'domain':domain,'boundary':boundary,'variant':v,
          'oracle':{'complete_coverage':known,'known_true_union':total,'longest_observed':longest,
             'exact_requested':expected if known else None,'claimed':claimed,'permission':False}})
    assert len(rows)==192
    return rows


def outcomes(compact=False):
    domains=['toy output','queue delay','retry count','resource use','simulated inventory','generated batch size']
    designs={'mean-outside':[(0,F(1,2)),(6,F(1,2))],
      'mode-below-half':[(0,F(2,5)),(2,F(3,10)),(5,F(3,10))],
      'tied-modes':[(1,F(2,5)),(3,F(2,5)),(7,F(1,5))],
      'mean-is-mode':[(0,F(1,4)),(2,F(1,2)),(4,F(1,4))],
      'aggregate-paths':[(0,F(1,5)),(4,F(3,10)),(4,F(3,10)),(8,F(1,5))]}
    options=[f'Claim true: {a}; x possible: {b}; x unique most probable: {c}; next result guaranteed x: {d}.'
      for a,b,c,d in product(['yes','no'],repeat=4)]
    rows=[]
    for marker,domain,(boundary,base),v in product(['mean-outcome','likeliest-outcome'],domains,designs.items(),range(4)):
        paths=[(F(x+v),p) for x,p in base];mass=defaultdict(F)
        for x,p in paths:mass[x]+=p
        assert sum(mass.values())==1 and all(p>0 for p in mass.values())
        mean=sum(x*p for x,p in mass.items());peak=max(mass.values());modes={x for x,p in mass.items() if p==peak}
        # A second exact oracle expands equiprobable tickets; no float approximation.
        denominator=1
        from math import gcd
        for p in mass.values():denominator=denominator*p.denominator//gcd(denominator,p.denominator)
        tickets=[x for x,p in mass.items() for _ in range(int(p*denominator))]
        counts=Counter(tickets)
        assert mean==sum(tickets)/len(tickets)
        assert modes=={x for x,n in counts.items() if n==max(counts.values())}
        x=(mean if marker=='mean-outcome' else min(modes))+(0 if v%2==0 else 1)
        correct=x==mean if marker=='mean-outcome' else x in modes
        flags=[correct,x in mass,modes=={x},mass.get(x)==1]
        answer='Claim true: %s; x possible: %s; x unique most probable: %s; next result guaranteed x: %s.'%tuple('yes' if b else 'no' for b in flags)
        ref=f'D{len(rows)+421}'
        common=(f'Fictional {domain} model {ref}, version v3 under the stated conditioning; one unit is declared. '
          'The mutually exclusive paths below are exhaustive, exact rational masses, not rounded observations: '
          +'; '.join(f'value {a} units with mass {p}' for a,p in paths)+'. '
          'Add masses of paths with the same value. Mean is the probability-weighted arithmetic mean; most probable compares aggregated value masses and allows ties. '
          f'Here x = {x} units. No claim that the model is correct or guarantees a trial is supplied. Statement: ')
        if compact:english=f'Mean under {ref}: {x} units.' if marker=='mean-outcome' else f'A most probable outcome under {ref}: {x} units.'
        else:english=f'Under {ref}, the probability-weighted mean is {x} units.' if marker=='mean-outcome' else f'Under {ref}, {x} units has the highest outcome probability, ties allowed.'
        rows.append({'id':f'outcome-full-{len(rows):03}','english':common+english,
          'ainglish':common+f'{x} units is {marker}({ref}).',
          'question':'Evaluate the claim, whether x can actually occur, whether x alone is most probable, and whether the next result is guaranteed to equal x.',
          'options':ordered(options,answer,len(rows)),'answer':answer,'settlement_stratum':marker,
          'domain':domain,'boundary':boundary,'variant':v,
          'oracle':{'mean':str(mean),'modes':sorted(map(str,modes)),'value':str(x),'flags':flags,
             'masses':{str(a):str(p) for a,p in mass.items()}}})
    assert len(rows)==240
    return rows


def identity():
    domains=['physical copies','books and editions','files and paths','data records','accounts','configurations',
             'model artifacts','running workers','devices','measured quantities','versioned documents','archive containers']
    options=[f'Returning Y: {a}; update through X visible via Y: {b}; relation certifies unchanged history: {c}.'
       for a,b,c in product(['justified','not justified','clarify'],['yes','no','unknown'],['yes','no'])]
    rows=[]
    for domain,v,marker in product(domains,range(8),['same-instance-as','value-equal-to']):
        identity_claim=marker=='same-instance-as';resolved=v!=7;key_resolved=v!=6
        identity_known=True if identity_claim and resolved else [None,False,False,True,False,True,None,None][v]
        policy='identity' if v%2==0 else 'value'
        extra=''
        if not identity_claim and identity_known is not None:
            extra='The identity ledger separately establishes that X and Y are '+('aliases of one entity. ' if identity_known else 'distinct entities. ')
        if v==1:extra+='Earlier and current snapshots differ; no unchanged history is claimed. '
        if v==2:extra+='The earlier snapshot predates a recorded update; historical values cannot be inferred from the current relation. '
        if v==3:extra+='A separate audit says earlier and current snapshots match; that audit is independent of the relation claim. '
        if v==2 and not identity_claim:extra+='Values on an unrelated key J differ. '
        if v==4:extra+='Their display labels look alike; labels are not identity records. '
        if v==5:extra+='Their display labels look different; labels are not identity records. '
        if not key_resolved:extra+='K is missing its projection definition and cannot be resolved. '
        if not resolved:extra+='X is an ambiguous reference to two possible records; its referent is unresolved. '
        common=(f'Fictional {domain} handoff in a declared identity system at observation time T. '
          +('X and Y are uniquely resolved references. ' if resolved else '')
          +('K uniquely names the auditable current value projection in this system. ' if key_resolved else '')
          +'The system rule is explicit: an authorised update to an entity is visible through all its aliases but not through distinct copies. '
          +('The return policy requires the original entity, not merely equal values. ' if policy=='identity' else
            'The return policy accepts any object with equal current value under K; entity identity is not required. ')
          +extra+'Statement: ')
        valid=resolved and (identity_claim or key_resolved)
        if not valid or (policy=='value' and not key_resolved):action='clarify'
        elif policy=='value':action='justified'
        else:action={True:'justified',False:'not justified',None:'clarify'}[identity_known]
        update={True:'yes',False:'no',None:'unknown'}[identity_known if resolved else None]
        answer=f'Returning Y: {action}; update through X visible via Y: {update}; relation certifies unchanged history: no.'
        english='X and Y denote one and the same individual entity.' if identity_claim else 'X and Y have equal current values under the named projection K.'
        ainglish='X same-instance-as(Y).' if identity_claim else 'X value-equal-to(Y, by=K).'
        rows.append({'id':f'identity-full-{len(rows):03}','english':common+english,'ainglish':common+ainglish,
          'question':'Does the supplied relation justify returning Y under this policy, or require refusal/clarification? If an update to X were authorised, would it appear through Y under the stated system rule? Does the relation itself certify unchanged historical values?',
          'options':ordered(options,answer,len(rows)),'answer':answer,'settlement_stratum':marker,
          'domain':domain,'boundary':v,'oracle':{'identity_known':identity_known,'references_resolved':resolved,
              'key_resolved':key_resolved,'policy':policy,'valid_relation':valid,'history_implied':False}})
    assert len(rows)==192
    return rows


GENERATORS={'identity':identity,'duration':duration,'outcome-careful':outcomes,
            'outcome-compact':lambda:outcomes(True)}


def selfcheck():
    report={}
    for name,fn in GENERATORS.items():
        rows=fn();assert len({(r['english'],r['ainglish'],r['question']) for r in rows})==len(rows)
        positions=Counter(r['options'].index(r['answer']) for r in rows)
        assert max(positions.values())-min(positions.values())<=1
        assert all(r['answer'] in r['options'] and len(r['options'])==len(set(r['options'])) for r in rows)
        report[name]={'targets':len(rows),'strata':dict(Counter(r['settlement_stratum'] for r in rows)),
          'domains':dict(Counter(r['domain'] for r in rows)),'answer_positions':dict(positions),'reader_calls':0}
    return report

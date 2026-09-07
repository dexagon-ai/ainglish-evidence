"""Create one prospective narrow replication; never run a reader or submit."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
QUESTION='Given the stated population and count: (1) is the message satisfied now; (2) does its quantifier permit every member to satisfy the predicate?'
CHOICES=['yes / no','no / yes','no / no','unknown / yes','unknown / unknown','yes / yes']
WORLDS=[('archive','catalogue drawers','received an inventory label',7,0),
        ('conservation','habitat plots','received a soil survey',8,1),
        ('shipping','freight lockers','received a routing card',9,9)]

def build():
    rows=[]
    for domain,noun,predicate,total,count in WORLDS:
        for comparator in ('bare','careful'):
            for form in ('some-or-all','some-but-not-all'):
                permits=form=='some-or-all'
                current=count>=1 and (permits or count<total)
                answer=('yes' if current else 'no')+' / '+('yes' if permits else 'no')
                shared=f'The bounded population has {total} members; exactly {count} {predicate}.'
                english=f'Some of the {noun} {predicate}.'
                if comparator=='careful':
                    english=(f'At least one of the {noun} {predicate}; the message remains compatible with every member satisfying that predicate.' if permits else
                        f'At least one of the {noun} {predicate}, and at least one did not; the message excludes every member satisfying that predicate.')
                index=len(rows); shift=index%6
                rows.append({'id':f'dx-ratification-some-{index+1:02d}',
                    'english':english+' '+shared,'ainglish':f'{form} {noun} {predicate}. '+shared,
                    'question':QUESTION,'options':CHOICES[shift:]+CHOICES[:shift],'answer':answer,
                    'strata':{'domain':domain,'form':form,'comparator':comparator,'observed_count':f'{count}-of-{total}'}})
    for permits in (True,False):
        for index,(_,_,_,total,count) in enumerate(WORLDS):
            current=count>=1 and (permits or count<total)
            answer=('yes' if current else 'no')+' / '+('yes' if permits else 'no')
            force=('At least one marked member is required; every member being marked is permitted.' if permits else
                   'At least one marked member and at least one unmarked member are required; every member being marked is excluded.')
            shift=len(rows)%6
            rows.append({'id':f'dx-ratification-some-cal-{len(rows)-11:02d}','calibration':True,
                'english':f'There are {count} marked members in a population of {total}; the quantified requirement is not available.',
                'ainglish':force+f' There are {count} marked members in a population of {total}.',
                'question':QUESTION,'options':CHOICES[shift:]+CHOICES[:shift],'answer':answer,
                'strata':{'control':'construct-free-planted-effect'}})
    assert len(rows)==18 and len({r['id'] for r in rows})==18
    assert all(r['answer'] in r['options'] and len(set(r['options']))==6 for r in rows)
    real=[r for r in rows if not r.get('calibration')]
    for key in ('form','comparator'):
        assert sorted(sum(r['strata'][key]==v for r in real) for v in {r['strata'][key] for r in real})==[6,6]
    assert all('Control instruction' not in r['ainglish'] for r in rows)
    return rows

if __name__=='__main__':
    raw=(json.dumps(build(),indent=2,ensure_ascii=False)+'\n').encode()
    with (ROOT/'items.json').open('xb') as out:out.write(raw)
    print('12 scientific + 6 construct-free calibration items',hashlib.sha256(raw).hexdigest())

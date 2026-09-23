"""Prospective design aid, NOT a restart or replacement of the retired study.

Only integer, single-quantity, common-unit, sequential updates are supported.
Unknown starts are an explicitly lower-bounded set, never silently zero.
Answers are disjoint three-valued propositions, not overlapping 'no' and
'the value is not determined' options. No tokenizer, model or SDK calls.
"""
import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

YES = 'The stated condition holds.'
NO = 'The stated condition does not hold.'
UNKNOWN = 'The supplied facts allow both possibilities.'
ANSWERS = [YES, NO, UNKNOWN]
DOMAINS = [('counts','queue capacity','slots'), ('durations','timeout','seconds'),
           ('storage','storage limit','GiB'), ('credit','credit allowance','credits')]

@dataclass(frozen=True)
class Expr:
    coefficient: int
    offset: int

def symbolic(start, operations):
    value = Expr(1, 0) if start is None else Expr(0, start)
    for op, number in operations:
        if op == 'set': value = Expr(0, number)
        elif op == 'adjust': value = Expr(value.coefficient, value.offset + number)
        else: raise ValueError('Missing or unsupported operator')
    return value

def classify(expr, lower, query, other=None):
    """Truth over ALL admissible initial integers, not selected completions."""
    c, b = expr.coefficient, expr.offset
    if query['kind'] == 'equal':
        c -= other.coefficient; b -= other.offset
        if c == 0: return YES if b == 0 else NO
        return UNKNOWN if (-b) % abs(c) == 0 and -b // c >= lower else NO
    if c not in (0,1): raise ValueError('Unsupported expression')
    minimum = c * lower + b
    if query['kind'] == 'at_least':
        bound = query['bound']
        if minimum >= bound: return YES
        return NO if c == 0 else UNKNOWN
    if query['kind'] == 'above':
        return classify(expr,lower,{'kind':'at_least','bound':query['bound']+1})
    if query['kind'] == 'within':
        lo, hi = query['lo'],query['hi']
        if lo > hi: raise ValueError('Reversed interval')
        if c == 0: return YES if lo <= b <= hi else NO
        return NO if minimum > hi else UNKNOWN
    raise ValueError('Unsupported query')

def numeric(start, operations):
    for op, value in operations:
        if op == 'set': start = value
        elif op == 'adjust': start += value
        else: raise ValueError(op)
    return start

def enumerate_truth(start, lower, operations, query, other_ops):
    """Independent finite witness check for this bounded authored fixture family.

    All offsets/bounds have magnitude <1000 and slope is 0 or 1. Testing through
    10000 covers every threshold/equality crossing here, NOT arbitrary integers.
    The production oracle above is symbolic and has no truncation bound.
    """
    assert all(abs(v)<1000 for _,v in operations+other_ops)
    assert all(abs(query[k])<1000 for k in ('bound','lo','hi') if k in query)
    outcomes=set()
    for x in ([start] if start is not None else range(lower,10001)):
        value=numeric(x,operations)
        kind=query['kind']
        if kind=='equal': outcome=value==numeric(x,other_ops)
        elif kind=='at_least': outcome=value>=query['bound']
        elif kind=='above': outcome=value>query['bound']
        else: outcome=query['lo']<=value<=query['hi']
        outcomes.add(outcome)
    return UNKNOWN if len(outcomes)==2 else YES if True in outcomes else NO

def render(start, lower, operations, quantity, unit, marked):
    header = (f'The starting {quantity} is at least {lower} {unit}; its exact value is not recorded.'
              if start is None else f'The starting {quantity} is {start} {unit}.')
    lines=[header,'Assume these instructions are applied in the written order.']
    for op,value in operations:
        if marked:
            token=f'set-to({value} {unit})' if op=='set' else f'adjust-by({value:+d} {unit})'
            lines.append(f'Update {quantity}: {token}.')
        elif op=='set': lines.append(f'Set {quantity} to {value} {unit}.')
        elif value>0: lines.append(f'Increase {quantity} by {value} {unit}.')
        elif value<0: lines.append(f'Decrease {quantity} by {-value} {unit}.')
        else: lines.append(f"Leave {quantity}'s numeric value unchanged.")
    return '\n'.join(lines)

def parse(text):
    """Separate recognizer of the actual rendered arms, rejecting leftover text."""
    lines=text.splitlines()
    m=re.fullmatch(r'The starting (.+?) is (at least )?(\d+) (slots|seconds|GiB|credits)(; its exact value is not recorded)?\.',lines[0])
    if not m or bool(m[2])!=bool(m[5]): raise ValueError('Invalid initial facts')
    q,unit,lower=m[1],m[4],int(m[3]);start=None if m[2] else lower
    if lines[1]!='Assume these instructions are applied in the written order.': raise ValueError('Order missing')
    operations=[]
    for line in lines[2:]:
        m=re.fullmatch(r'Update '+re.escape(q)+r': (set-to|adjust-by)\(([-+]?\d+) '+re.escape(unit)+r'\)\.',line)
        if m:
            if m[1]=='adjust-by' and m[2][0] not in '+-':raise ValueError('Unsigned adjustment')
            operations.append(('set' if m[1]=='set-to' else 'adjust',int(m[2])));continue
        m=re.fullmatch(r'(Set|Increase|Decrease) '+re.escape(q)+r' (to|by) (\d+) '+re.escape(unit)+r'\.',line)
        if m:
            if (m[1]=='Set')!=(m[2]=='to'):raise ValueError('Bad relation')
            operations.append(('set' if m[1]=='Set' else 'adjust',int(m[3])*(-1 if m[1]=='Decrease' else 1)));continue
        if line==f"Leave {q}'s numeric value unchanged.":operations.append(('adjust',0));continue
        raise ValueError('Unparsed instruction: '+line)
    if not operations:raise ValueError('No operation')
    for length in range(1,len(operations)+1):
        value=symbolic(start,operations[:length])
        if value.coefficient*lower+value.offset<0:
            raise ValueError('An intermediate quantity can be negative in a nonnegative domain')
    return start,lower,operations,q,unit

def build():
    items=[];keys=[]
    for form in ('set','adjust'):
        for condition in ('known','unknown','ordered'):
            for d,(domain,q,unit) in enumerate(DOMAINS):
                for variant in range(8):
                    n=50+d*17+variant*3;lower=n
                    start=None if condition=='unknown' else n
                    target=[n+15,n-7,0,n,n+3,n-11,n+29,n+8][variant]
                    delta=[7,-3,0,11,-9,0,4,-6][(variant+d)%8]
                    # All four authored domains are nonnegative. Never construct
                    # a reset-to-zero followed by an impossible negative balance.
                    if condition=='ordered' and form=='adjust':target=max(target,-delta)
                    op=('set',target) if form=='set' else ('adjust',delta)
                    operations=[op]
                    if condition=='ordered':operations=[('adjust',delta) if form=='set' else ('set',target),op]
                    other_ops=[('set',target),('adjust',delta)] if variant%2 else [('adjust',delta),('set',target)]
                    kind=variant%4
                    if kind==0:
                        query={'kind':'at_least','bound':n+5+(variant//4)*20}
                        question=f'Would the final {q} be sufficient for a requirement of {query["bound"]} {unit}?'
                    elif kind==1:
                        query={'kind':'above','bound':n+(-5 if (d+variant)%2 else 10)}
                        question=f'Would the final {q} exceed a ceiling of {query["bound"]} {unit}?'
                    elif kind==2:
                        query={'kind':'equal'}
                        ref=render(start,lower,other_ops,q,unit,False).splitlines()[2:]
                        question='An independent copy begins with the SAME starting value and applies the following instructions: '+' '.join(ref)+f' Do the two copies finish with the same {q}?'
                    else:
                        query={'kind':'within','lo':n-5,'hi':n+5}
                        question=f'Would the final {q} lie within the inclusive band {n-5} to {n+5} {unit}?'
                    arms={name:render(start,lower,operations,q,unit,marked) for name,marked in [('marked',True),('careful',False)]}
                    for arm in arms.values():assert parse(arm)==(start,lower,operations,q,unit)
                    expr=symbolic(start,operations);other=symbolic(start,other_ops)
                    answer=classify(expr,lower,query,other)
                    assert answer==enumerate_truth(start,lower,operations,query,other_ops)
                    # Equal opaque KEY positions, not a claim of equal truth prevalence.
                    position=len(items)%3;values=ANSWERS.copy()
                    old_position=values.index(answer)
                    values[position],values[old_position]=values[old_position],values[position]
                    choices=dict(zip('ABC',values));key='ABC'[position]
                    assert choices[key]==answer and len(set(choices.values()))==3
                    item_id=hashlib.sha256(json.dumps([arms,question],sort_keys=True).encode()).hexdigest()[:24]
                    items.append({'id':item_id,'arms':arms,'question':question,'choices':choices})
                    keys.append({'id':item_id,'answer':key,'meaning':answer,'stratum':f'{form}:{condition}',
                        'domain':domain,'template_cluster':f'{form}:{condition}:{domain}',
                        'start':start,'lower':lower,'operations':operations,'query':query,'other_operations':other_ops})
    assert len(items)==len({i['id'] for i in items})==192
    assert Counter(k['answer'] for k in keys)==dict.fromkeys('ABC',64)
    assert set(Counter(k['stratum'] for k in keys).values())=={32}
    return items,keys

if __name__=='__main__':
    items,keys=build();root=Path(__file__).parent
    report={'status':'future_design_review_only_current_campaign_retired',
        'rows':len(items),'strata':dict(Counter(k['stratum'] for k in keys)),
        'template_clusters':len(set(k['template_cluster'] for k in keys)),
        'answer_positions':dict(Counter(k['answer'] for k in keys)),
        'truth_prevalence':dict(Counter(k['meaning'] for k in keys)),
        'oracle_vs_independent_enumeration':192,'parsed_arm_equivalence':384,
        'reader_calls':0,'claim':'Design checks, not comprehension or independent key approval.',
        'limitations':['Authored numeric variants of 24 templates, not 192 independent contexts.',
            'No current experiment or fresh replication is authorized.',
            'Opaque label balance does not establish absence of semantic shortcuts.',
            'Independent semantic, plausibility and comparator review required.',
            'Lower-bounded unknowns define THIS future population; not a replica of earlier unbounded-unknown studies.']}
    for name,value in [('quantity-inputs.json',items),('quantity-keys.json',keys),('quantity-review.json',report)]:
        (root/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,indent=2))

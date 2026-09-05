"""Finite scenario ledgers and oracle-scored next studies. No reader calls or token counts."""
import itertools
import json
from pathlib import Path
from collections import Counter
from build_studies import calibration,choice,canonical
import hashlib

ROOT=Path(__file__).resolve().parent
def save(name,data):
    with (ROOT/name).open('x') as f:json.dump(data,f,ensure_ascii=False,indent=2)

def row(ident,en,ai,q,answer,options,stratum,ledger,index):
    # Rotate from the semantic gold to a prospectively balanced position.
    return {'id':ident,'english':en,'ainglish':ai,'question':q,'answer':answer,
        'options':choice(options,options.index(answer)-(index%len(options))),
        'settlement_stratum':stratum,'ledger':ledger}

def will():
    domains=[('review','review the port-access checklist'),('deploy','deploy the revised route table'),
        ('payment','transfer the agreed archive fee'),('delivery','deliver the museum labels'),
        ('measurement','measure the orchard tank'),('review','review the rail timetable'),
        ('delivery','deliver the lab sample'),('measurement','measure the tunnel clearance')]
    obligations=['perform unless released','notify when the plan changes','no undertaking to make it happen']
    options=[f'1: {d}; 2: {b}' for d in obligations for b in ['yes','no']]
    data=[]
    for i in range(64):
        domain,action=domains[i%8]
        person=['Mara','Jonas','Leena','Davi'][i%4];ref=f'case W{7100+i}'
        # Release, communicated revision, quiet revision, and outcome failure vary independently.
        released=(i//8)%2==0; changed=(i//16)%2==0;notice=(i//32)%2==0
        context=f'For {ref}, {person} writes to the coordinator: '
        event=(f'Later, {person} does not {action}. '
            +('The coordinator had released this person from any undertaking to deliver the outcome before the deadline; any separate duty to communicate a plan change was not waived. ' if released else 'The coordinator granted no release. ')
            +('Their intended course changed before the deadline. ' if changed else 'Their intended course did not change. ')
            +('They told the coordinator about the change before acting differently. ' if changed and notice else 'They sent no further message. '))
        for j,form in enumerate(['will-as-promise','will-as-plan','will-as-forecast']):
            full=[f'I promise to {action} by Friday; that commits me to doing it unless you release me.',
                  f'My current plan is to {action} by Friday; I will tell you if that plan changes.',
                  f'I expect that I will {action} by Friday; this prediction claims no control and makes no commitment to bring it about.'][j]
            # The notice duty is a duty on revision, not a promise of a successful outcome.
            breach=(not released) if j==0 else (changed and not notice) if j==1 else False
            answer=f'1: {obligations[j]}; 2: {"yes" if breach else "no"}'
            compact=f'I {form} {action} by Friday.'
            future=event
            if j==2 and i%2:
                compact=f'The independent contractor {form} {action} by Friday.'
                full=f'I expect the independent contractor to {action} by Friday; this prediction claims no control and makes no commitment to bring it about.'
                future=event.replace(f'{person} does not', 'the independent contractor does not')
            data.append(row(f'will-{j}-{i:02}',context+'"'+full+'" '+future,
                context+'"'+compact+'" '+future,
                '1. What did this message commit the writer to? 2. On the stated later facts, did the writer fail that commitment? Choose both answers.',
                answer,options,form,{'domain':domain,'released':released,'plan_changed':changed,'notice':notice,'outcome':False,'form':form},i*3+j))
    return data

def since():
    domains=[('incident response','the relay reset','the alarms have stayed quiet'),
        ('deployments','the routing patch landed','the service has answered successfully'),
        ('access policy','the access rule changed','the account has remained locked'),
        ('payments','the bank link reopened','payments have cleared every evening'),
        ('health monitoring','the monitor was recalibrated','the readings have stayed within range'),
        ('logistics','the depot reopened','deliveries have arrived each morning'),
        ('scheduling','the new rota began','the desk has remained staffed'),
        ('research reporting','the sensor was replaced','the lab has logged observations daily'),
        ('ordinary coordination','the meeting moved online','the team has met every week')]
    profiles=[f'1: {a}; 2: {b}' for a in ['yes','no'] for b in ['yes','no']]
    rows=[]
    # 9 domains x 8 realizations x all four logical cells = 288 real items.
    for i in range(72):
        domain,event,main=domains[i%9];ref=f'case S{8100+i}'
        for j,(reason,interval) in enumerate([(True,False),(False,True),(True,True),(False,False)]):
            prefix=f'In {ref}, as of the stated review date, '
            if reason and interval:
                ai=f'{main} ever since {event}, and because {event}.'
                en=f'{event} explains why {main}; this has held or recurred from that event through the review date.'
            elif reason:
                ai=f'Because {event}, {main}.'
                en=f'{event} explains why {main}.'
            elif interval:
                ai=f'Ever since {event}, {main}.'
                en=f'{main} throughout the interval from that event ({event}) through the review date.'
            else:
                ai=en=f'{event}. Separately, {main}.'
            if i%2 and j==0:ai=f'{main} because {event}.'
            if i%2 and j==1:ai=f'{main} ever since {event}.'
            a,b=(reason,interval) if i%2==0 else (interval,reason)
            q1='Does this sentence itself say that the event explains why the main condition holds?'
            q2='Does it itself assert a condition holding or recurring from that event through the review date?'
            q=[q1,q2] if i%2==0 else [q2,q1]
            answer=f'1: {"yes" if a else "no"}; 2: {"yes" if b else "no"}'
            rows.append(row(f'since-{j}-{i:02}',prefix+en,prefix+ai,
                '1. '+q[0]+' 2. '+q[1]+' Answer what is asserted, not what might also be true in the world.',
                answer,profiles,['reason','interval','both','neither'][j],
                {'domain':domain,'reason_asserted':reason,'interval_asserted':interval,'reason_first':i%2==0},i*4+j))
    return rows

def destination(initial,ops):
    value=initial
    for op,n in ops:value=n if op=='set-to' else None if value is None else value+n
    return value

def quantity():
    domains=[('packet limit','packets'),('timeout','seconds'),('storage allowance','MB'),('credit allowance','credits')]
    options=['yes','no','the final value is not determined','the instructions conflict']
    rows=[]
    for i in range(32):
        quantity,unit=domains[i%4];prior=20+3*i;delta=[0,5,-4,9][(i//4)%4];target=[0,7,40,60][(i//8)%4]
        for k,case in enumerate(['known','unknown','ordered']):
            initial=None if case=='unknown' or (case=='ordered' and i%2) else prior
            context=f'For job U{9100+i}-{case}, the {quantity} '+('is not known. ' if initial is None else f'is {initial} {unit}. ')
            for j,form in enumerate(['set-to','adjust-by']):
                n=target if form=='set-to' else delta
                ops=([('adjust-by',3)] if form=='set-to' else [('set-to',prior)]) if case=='ordered' else []
                ops.append((form,n));value=destination(initial,ops)
                en=[];ai=[]
                for op,amount in ops:
                    if op=='set-to':english=f'Set the {quantity} to {amount} {unit}'
                    elif amount==0:english=f'Leave the {quantity}\'s numeric value unchanged'
                    elif amount>0:english=f'Increase the {quantity} by {amount} {unit}'
                    else:english=f'Decrease the {quantity} by {abs(amount)} {unit}'
                    en.append(english);ai.append(f'{quantity} {op}({amount:+d} {unit})' if op=='adjust-by' else f'{quantity} {op}({amount} {unit})')
                lead='Apply the following instructions in this explicit order, with no intervening updates: '
                if i%4==0:
                    question='Assuming the instructed updates are performed, is the final numeric value determined from this message?'
                    answer='yes' if value is not None else 'no'
                else:
                    threshold=(value if value is not None else 30)+(1 if (i//4)%2 else -1)
                    question=f'After the instructed updates, would a requirement for {threshold} {unit} fit within the final {quantity}?'
                    answer='the final value is not determined' if value is None else 'yes' if threshold<=value else 'no'
                rows.append(row(f'quantity-{j}-{k}-{i:02}',context+lead+'; then '.join(en)+'.',context+lead+'; then '.join(ai)+'.',
                    question,answer,options,f'{form}:{case}',{'initial':initial,'operations':ops,'final':value,'unit':unit,'case':case},i*6+k*2+j))
    return rows

def assignments(eligibility,capacities,same):
    return [list(plan) for plan in itertools.product(*eligibility)
        if (not same or len(set(plan))==1) and all(plan.count(k)<=v for k,v in capacities.items())]

def shared_choice():
    domains=[('reviewer','reports'),('font-family','documents'),('source-dataset','analyses'),('deadline','tasks')]
    rows=[];options=['yes','no','no feasible assignment exists','the information is insufficient']
    scenarios=[([['A','B','C']]*3,{'A':3,'B':3,'C':3},['A','A','A']),
        ([['A','B','C']]*3,{'A':3,'B':3,'C':3},['A','B','A']),
        ([['A','B','C']]*3,{'A':3,'B':3,'C':3},['A','B','C']),
        ([['A'],['B'],['C']],{'A':3,'B':3,'C':3},['A','B','C']),
        ([['A','B'],['A'],['A','C']],{'A':3,'B':3,'C':3},['A','B','A']),
        ([['A','B']]*3,{'A':2,'B':2,'C':0},['A','B','A']),
        ([['A','B']]*3,{'A':1,'B':1,'C':0},['A','B','A']),
        ([['A','B']]*3,{'A':3,'B':3,'C':0},['A','B','A'])]
    for i in range(32):
        slot,group=domains[i%4];elig,cap,candidate=scenarios[(i//4)%8]
        label=f'C{10100+i}';members=[label+'-1',label+'-2',label+'-3']
        context=(f'For {group} '+', '.join(members)+f', the {slot} choices have distinct IDs A, B, C. '
            +' '.join(f'{m} permits only '+','.join(e)+'.' for m,e in zip(members,elig))
            +' Maximum uses within this assignment: '+', '.join(f'{x}={n}' for x,n in cap.items())+'. ')
        if (i//4)%8==7:context+='Choices A and B have the same display name but are different identities. '
        for j,form in enumerate(['same-for-all','may-vary-across']):
            feasible=assignments(elig,cap,j==0)
            en=(f'Assign the same single {slot} to all three {group}.' if j==0 else
                f'Assign exactly one {slot} to each of these {group}; choices may be the same or different.')
            ai=f'Assign exactly one {slot} to each of these {group}, {form}({label}).'
            context2=context+f'The set {label} contains precisely those three {group}. '
            for k,task in enumerate(['admissibility','feasibility','consequence']):
                if task=='admissibility':
                    question='A proposed plan uses IDs '+','.join(candidate)+' in the listed member order. Does that plan obey every stated requirement?'
                    answer='yes' if candidate in feasible else 'no'
                elif task=='feasibility':
                    question='Can any complete plan obey all the stated requirements?';answer='yes' if feasible else 'no'
                else:
                    question='Among plans obeying every requirement, must the first and last listed members use the same choice ID?'
                    answer='no feasible assignment exists' if not feasible else 'yes' if all(a[0]==a[2] for a in feasible) else 'no'
                trial=f'For evaluation record {label}-{task}, '
                rows.append(row(f'choice-{j}-{k}-{i:02}',trial+context2+en,trial+context2+ai,question,answer,options,
                    f'{form}:{task}',{'eligibility':elig,'capacities':cap,'candidate':candidate,'feasible':feasible,
                        'form':form,'task':task,'domain':slot},i*6+j*3+k))
    return rows

if __name__=='__main__':
    index={}
    for name,builder in [('will',will),('since',since),('quantity',quantity),('choice',shared_choice)]:
        real=builder();data=real+calibration(name)
        assert len({x['id'] for x in data})==len(data)
        assert all(x['answer'] in x['options'] for x in data)
        save(name+'.kit-v1.json',data)
        index[name]={'real_items':len(real),'controls':8,'strata':dict(Counter(x['settlement_stratum'] for x in real)),
            'sha256':hashlib.sha256(canonical(data)).hexdigest(),'reader_calls':0,'state':'oracle-checked design kit; gates and final runspec required before spend'}
    save('next-kits-v1-index.json',index)
    print(json.dumps(index,indent=2))

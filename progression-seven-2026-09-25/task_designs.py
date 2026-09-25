"""Review-only operational task examples; no inference or claim of IID worlds.

An oracle encodes the stipulated semantics, not an independent language judgment.
The incomplete context-only arm has its OWN correct answers. It cannot serve as
careful English or manufacture comprehension improvement against a hidden key.
"""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def row(family,name,context,marked,english,question,options,answer,context_answer,basis,probes):
    assert answer in options and context_answer in options
    # Balance answer positions across the review corpus without changing keys.
    offset=int(hashlib.sha256(name.encode()).hexdigest()[:8],16)%len(options)
    options=options[offset:]+options[:offset]
    return {'id':family+'-'+name,'family':family,'cluster_id':family+'-'+name,
        'shared_context':context,'ainglish_message':marked,'careful_english_message':english,
        'question':question,'options':options,'answer':answer,
        'context_only':{'text':context,'question':question,'options':options,'answer':context_answer},
        'key_basis':basis,'non_entailment_probes':probes,
        'status':'author-review-draft; semantic stipulations, not validated reader evidence'}


def latest():
    options=['record a current snapshot; closure is not established',
             'record the terminal item at the cited historical closure',
             'ask for the missing reference or message',
             'flag the message as inconsistent with the known reference']
    cases=[('build-snapshot','build R7','release line Cedar','09:00','latest','valid'),
           ('dataset-snapshot','dataset D9','data series Rowan','11:00','latest','valid'),
           ('minutes-snapshot','minutes M3','meeting sequence Alder','12:00','latest','valid'),
           ('snapshot-unknown-clock','build T4','release line Maple','unresolved clock P','latest','missing'),
           ('closed-build','build L2','release line Birch','closure K','final','valid'),
           ('closed-manual','manual J5','documentation series Elm','closure K','final','valid'),
           ('closed-round','round W6','review sequence Hazel','closure K','final','valid'),
           ('final-missing-ref','artifact F8','archive sequence Oak','closure K','final','missing'),
           ('final-wrong-sequence','artifact C2','release line Fir','closure K','final','wrong'),
           ('historical-reopening','build V4','release line Pine','closure K at 14:00','final','reopened'),
           ('fork-snapshot','build Q3','fork-specific line Aspen','13:00','latest','fork'),
           ('draft-not-member','build N9','publication line Ash','15:00','latest','draft')]
    out=[]
    for name,item,seq,ref,form,state in cases:
        context=f'You maintain a release register. {seq} names one ordered sequence; identities are resolvable unless stated otherwise. Record only what the handoff establishes, at its own time. The inventory of members is not supplied.'
        if state=='missing':context+=' The named clock or closure reference cannot be resolved.'
        elif state=='wrong':context+=' Closure K is known to close a different sequence, not this one.'
        elif form=='final':context+=f' {ref} is a signed authorised closure of the named sequence. Its text here does not identify the terminal item.'
        if state=='reopened':context+=' A later authorised reopening at 16:00 does not rewrite the earlier closure record.'
        if state=='fork':context+=' Another fork has newer work, but is not part of the named sequence.'
        if state=='draft':context+=' A later local draft is not a published member of this sequence.'
        marked=f'{item} is '+(f'latest-so-far({seq}, {ref}).' if form=='latest' else f'final-in-sequence({seq}, {ref}).')
        english=(f'As of {ref}, {item} is the latest item in {seq}.' if form=='latest'
                 else f'{item} is the final item in {seq}, under {ref}.')
        key=options[2] if state=='missing' else options[3] if state=='wrong' else options[0 if form=='latest' else 1]
        probes=[{'question':'Does this establish that no future authorisation can ever reopen the sequence?',
                 'answer':'no','basis':'A time-anchored closure is not an irrevocability promise.'},
                {'question':'Does latest-so-far alone establish closure?','answer':'no','basis':'Maximality at a cutoff does not imply closure.'}]
        out.append(row('latest',name,context,marked,english,'Which record is justified for the named item?',options,key,options[2],
                       'Valid latest establishes maximality at the cutoff only; valid final establishes terminal membership at closure. Missing references are unresolved; a wrong known closure is inconsistent.',probes))
    return out


def statistical():
    options=['test threshold met only','practical criterion met only','both met','not enough information to classify both']
    # A fifth semantic state (neither) requires a fifth invariant option, never
    # hidden-state grading of an ambiguous or omitted message.
    options=options+['neither met']
    cases=[('both',True,True,'both','valid'),('test-only',True,False,'both','valid'),
           ('practical-only',False,True,'both','valid'),('neither',False,False,'both','valid'),
           ('single-stat-positive',True,None,'stat','valid'),('single-practical-positive',None,True,'practical','valid'),
           ('single-stat-negative',False,None,'stat','valid'),('single-practical-negative',None,False,'practical','valid'),
           ('missing-analysis',True,True,'both','missing'),('missing-criterion',True,True,'both','missing'),
           ('adjusted-test',True,False,'both','adjusted'),('posthoc-analysis',True,True,'both','posthoc')]
    out=[]
    for name,s,p,which,state in cases:
        context='A results desk records whether a named statistical threshold and a separate material-effect criterion were met. T is a two-sided test of zero average change; A identifies this analysis; alpha is 0.05. C requires a scope-S change of at least 8 units. Actual test results and effect estimates are not in this context. No study-design or causal guarantee is supplied.'
        if state=='missing':
            if name=='missing-analysis':
                context=context.replace('A identifies this analysis;', 'A is an unresolved analysis reference;')
            else:
                context=context.replace('C requires a scope-S change of at least 8 units.', 'C is an unresolved practical-criterion reference in scope S.')
        if state=='adjusted':context+=' T means the multiplicity-adjusted test, not an unadjusted p-value.'
        if state=='posthoc':context+=' A was selected after the results were seen, not preregistered.'
        marked=[];english=[]
        if which in ('both','stat'):
            marked.append(('' if s else 'not: ')+'F stat-significant(test=T, alpha=0.05, analysis=A).')
            english.append('In analysis A, finding F '+('meets' if s else 'does not meet')+' test T\'s 0.05 significance threshold.')
        if which in ('both','practical'):
            marked.append(('' if p else 'not: ')+'F practically-important(criterion=C, scope=S).')
            english.append('Finding F '+('meets' if p else 'does not meet')+' practical criterion C in scope S.')
        key=options[3] if state=='missing' or which!='both' else options[2] if s and p else options[0] if s else options[1] if p else options[4]
        probes=[{'question':'Does this establish the probability that the null hypothesis is true?',
                 'answer':'no','basis':'A test threshold is not a posterior null probability.'},
                {'question':'Does this by itself establish that implementing F is worthwhile?',
                 'answer':'no','basis':'A materiality criterion is not a complete action or cost-benefit rule.'},
                {'question':'If only the statistical marker is supplied, is practical importance determined?',
                 'answer':'no','basis':'The two claims are not mutually entailing.'}]
        out.append(row('stat',name,context,' '.join(marked),' '.join(english),
                       'What can the desk conclude about the TWO named criteria?',options,key,options[3],
                       'Both statuses must be stated or otherwise supported. A missing half or unresolved meaning-bearing reference cannot be filled from a hidden experimental world.',probes))
    return out


def assignment():
    options=['inspect the cited accepted assignment event','inspect the cited default rule',
             'ask for the actual resolution evidence','flag the description as inconsistent with resolver rules']
    cases=[('cli-override','assignment','valid'),('environment','assignment','valid'),
           ('explicit-equals-default','assignment','equal'),('generated-field','assignment','generated'),
           ('accepted-null','assignment','null-value'),('ordinary-default','default','valid'),
           ('null-as-absent','default','null-absent'),('default-equals-explicit','default','equal'),
           ('materialised-default','default','materialised'),('run-local-trace','assignment','run-local'),
           ('missing-trace','assignment','missing'),('rejected-null','assignment','rejected')]
    out=[]
    for name,origin,state in cases:
        context='At boundary B of one completed configuration resolution, the support desk must locate evidence for the observed value of K, not choose a future edit. A names the actual candidate input event; R names the resolver default rule. The final value by itself does not reveal provenance. No actual event trace is included unless stated.'
        value='null' if state in ('null-value','null-absent','rejected') else '8'
        if state=='equal':context+=' Both an assignment and the default could produce value 8.'
        if state=='generated':context+=' Generated configuration fields can be explicit accepted inputs.'
        if state=='null-value':context+=' Resolver policy treats present null as an accepted value.'
        if state=='null-absent':context+=' Resolver policy treats null as absent; R supplies null as the fallback value.'
        if state=='materialised':context+=' R can materialise a fallback into storage; that does not retroactively create an input assignment at B.'
        if state=='run-local':context+=' A resolves to a retained argv field in this run only; it has no global identifier.'
        if state=='missing':context+=' A cannot be resolved and no actual retained input trace can be retrieved.'
        if state=='rejected':context+=' The resolver rejects present null and this resolution failed without producing a value.'
        marked=f'At B, K resolved-by-{origin}({value}, '+('source=A).' if origin=='assignment' else 'rule=R).')
        english=f'At B, K\'s value {value} came from '+('accepted assignment A.' if origin=='assignment' else 'default rule R.')
        key=options[2] if state=='missing' else options[3] if state=='rejected' else options[0 if origin=='assignment' else 1]
        # The context-only rejected case already disproves successful resolution.
        ck=options[3] if state=='rejected' else options[2]
        probes=[{'question':'Does the provenance statement identify the only edit that can change K later?',
                 'answer':'no','basis':'Several interventions or later resolutions may change K.'},
                {'question':'Does an equal-to-default value prove that R supplied it?',
                 'answer':'no','basis':'Value equality is not provenance.'}]
        out.append(row('assignment',name,context,marked,english,'Where should the support desk look for the asserted provenance?',options,key,ck,
                       'Route to the asserted actual source at B, not a hypothetical future mutation. Missing evidence and a known failed resolution are different.',probes))
    return out


def build():
    report={'kind':'operational-task-review-drafts.v1','measurement':False,'scientific_reader_calls':0,
        'independent_cases_claimed':False,'source':'authored examples, not source-corpus observations',
        'limitations':['The oracle states intended semantics; independent author review remains necessary.',
                       'These examples are not randomized population samples or final inference-ready banks.',
                       'Context-only uses arm-specific keys and is not a superiority comparator.',
                       'Non-entailment probes need separately balanced positive controls before a study.',
                       'References, negation spelling, population, qualification and launch still require review.'],
        'studies':{'latest':latest(),'stat':statistical(),'assignment':assignment()}}
    for rows in report['studies'].values():
        assert len(rows)==12 and len({r['id'] for r in rows})==12
        assert all(r['options']==r['context_only']['options'] for r in rows)
    (ROOT/'operational-task-drafts.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'cases':{k:len(v) for k,v in report['studies'].items()},'reader_calls':0}))
    return report


if __name__=='__main__':build()

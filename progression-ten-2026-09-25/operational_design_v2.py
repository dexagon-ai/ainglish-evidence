"""Rendered review instruments, not measurements or an IID sampling claim.

Fixes context dropped by a message-only renderer, undefined `not:` syntax,
and an all-negative probe set. Positive controls add the missing fact to BOTH
arms; they are instrument checks, never evidence of Ainglish superiority.
"""
import importlib.util
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('draft_v1',ROOT.parent/'progression-seven-2026-09-25/task_designs.py')
v1=importlib.util.module_from_spec(spec);spec.loader.exec_module(v1)

CLAIMS={
 'latest':[
  ('another series has closed','A separate signed record closes series Other at 10:00.'),
  ('the sequence cannot ever be reopened','An irreversible rule forbids all future reopening of this sequence.'),
  ('a later draft is an admitted member','Draft D10 has been formally admitted to this sequence.'),
  ('a particular item passed a safety review','A retained review records that item R7 passed the stated safety check.'),
  ('a deadline was met','The delivery log records arrival before the stated deadline.'),
  ('there is permission to publish','The release authority explicitly grants permission to publish R7.'),
  ('the series has an upper size bound','The charter limits this series to twenty members.'),
  ('two forks are in the same sequence','The sequence charter explicitly treats branches East and West as one sequence.'),
  ('closure proves the best possible quality','An explicit separate case stipulation says no higher-quality item is possible in the stated finite set.'),
  ('a later change has already occurred','The retained event log records a later admission at 16:00.'),
 ],
 'stat':[
  ('a posterior null probability is provided','A separate declared Bayesian analysis reports a posterior null probability of 0.03.'),
  ('the analysis was preregistered','The dated registration record predates observation of the results.'),
  ('a causal conclusion is supplied','A separate identified experiment and causal report conclude the intervention caused the change under their stated assumptions.'),
  ('implementation has been judged worthwhile','The stated decision review includes costs and benefits and recommends implementation.'),
  ('the effect was independently reproduced','An independent replication report reproduces the named effect on fresh units.'),
  ('the findings generalize to a second population','A separate validation report establishes the stated conclusion for population South.'),
  ('all multiplicity corrections were applied','The analysis record explicitly lists and applies all predeclared multiplicity corrections.'),
  ('the project passed ethics review','The named ethics committee approved this project before its start.'),
  ('the data are free of missing values','The case data inventory explicitly records zero missing observations.'),
  ('the test has a stated power calculation','The analysis plan includes a power calculation for the named effect and sampling model.'),
 ],
 'assignment':[
  ('exactly one later edit can change the value','The scoped resolver contract says exactly one editable source can affect the next run.'),
  ('the input was typed by a human','A retained provenance log says a human typed this input.'),
  ('the value is the recommended choice','The operator guide separately recommends this exact value.'),
  ('the configuration is secure','An independent security review judges this configuration secure under its stated threat model.'),
  ('the next run will produce the same value','The case stipulates unchanged inputs, resolver, boundary and deterministic execution for the next run.'),
  ('the source is a globally stable reference','A retained registry assigns the cited input a permanent globally unique identifier.'),
  ('there is permission to change the configuration','The administrator expressly grants permission to change this configuration.'),
  ('the final value differs from the default','The trace states the final value is 8 and the default value is 12.'),
  ('the value was persisted to disk','The commit log records this resolved value being written successfully to disk.'),
  ('the run succeeded beyond configuration resolution','The execution report records successful completion of all later run stages.'),
 ],
}

def rename_stat(text):
 for old,new in [('F','finding North-42'),('T','MeanShift-42'),('A','Alden-42'),('C','Material-8'),('S','North-batches')]:
  text=re.sub(r'\b'+old+r'\b',new,text)
 return text

def render(context,message): return 'Context:\n'+context+'\n\nHandoff:\n'+message

def build():
 studies={};controls={}
 for family,source in [('latest',v1.latest()),('stat',v1.statistical()),('assignment',v1.assignment())]:
  rows=[]
  for r in source:
   # New artifact; the old packet remains an immutable review history.
   r=json.loads(json.dumps(r));r['id']+='-v2'
   if family=='stat':
    r['ainglish_message']=r['ainglish_message'].replace('not: F ','F is not ')
    for key in ('ainglish_message','careful_english_message','shared_context'):r[key]=rename_stat(r[key])
    r['shared_context']+=' Scope North-batches is the North service batch population. Change is defined as milliseconds saved per batch relative to the named baseline, not an unspecified absolute difference.'
   if family=='latest':
    r['shared_context']+=' For this hypothetical register, admitted members have a unique increasing admission counter, no ties; clocks are UTC on 25 September 2026. A closure record names its actual sequence and counter order; do not assume it matches a message when the context says otherwise.'
   if family=='assignment':
    r['shared_context']+=' B names configuration resolution for run Cedar-42 before execution. K is max_workers. A is that run’s candidate input event; R is rule workers-fallback-v3, not an instruction for a future edit.'
   r['ainglish']=render(r['shared_context'],r['ainglish_message'])
   r['english']=render(r['shared_context'],r['careful_english_message'])
   r['context_only']['text']=r['shared_context']
   r['non_entailment_probes_review_only']=r.pop('non_entailment_probes')
   r['status']='rendered prospective author-review draft; no current-revision launch approval'
   assert r['shared_context'] in r['ainglish'] and r['shared_context'] in r['english']
   assert 'not:' not in r['ainglish']
   assert r['answer'] in r['options'] and r['context_only']['answer'] in r['options']
   rows.append(r)
  studies[family]=rows;controls[family]=[]
  base=rows[0]
  for i,(claim,positive) in enumerate(CLAIMS[family]):
   for yes in (False,True):
    context=base['shared_context']+('\nAdditional case record: '+positive if yes else '')
    controls[family].append({'id':f'{family}-probe-{i+1}-{int(yes)}','cluster_id':f'{family}-probe-{i+1}',
     'ainglish':render(context,base['ainglish_message']),'english':render(context,base['careful_english_message']),
     'question':'Does the supplied handoff and case record establish that '+claim+'?',
     'options':['yes','no'],'answer':'yes' if yes else 'no',
     'purpose':'Positive/negative instrument control; positive supplies the extra premise explicitly in both arms. Not a marker-only entailment or a measured language advantage.'})
  assert len(rows)==12 and len(controls[family])==20
  assert sum(r['answer']=='yes' for r in controls[family])==10
 report={'kind':'operational-task-review-drafts.v2','measurement':False,'scientific_reader_calls':0,
  'main_tasks':studies,'balanced_auxiliary_controls':controls,
  'unit_warning':'36 main cases plus 60 probes, not 96 independent worlds. Each positive/negative pair shares a cluster; main template relations also need a prospective sampling model.',
  'reader_claim':'Careful-English comparison is complete; context-only has its own defensible key and is diagnostic, not a superiority baseline.',
  'remaining_gates':['Author approval of negative grammar and all keys, including the positive controls.',
   'Prospective amendments and renewed seconds if the claim changes; current author holds remain.',
   'Freeze complete study population, reader roster, form strata and endpoint inventory, then qualification and preregistration.',
   'A token allowance or a token original is not a comprehension-benefit carrier. Proposed preservation protocol is not operative.']}
 (ROOT/'operational-design-v2.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
 print('36 rendered main cases and 60 balanced control probes; zero reader calls; author holds respected')

if __name__=='__main__':build()

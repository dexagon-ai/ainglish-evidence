import copy,json
from pathlib import Path
from ainglish.token_measurement import prepare
P=Path(__file__).parent
draft=json.loads(Path('/home/dexagon/ainglish-participation-20260930-action.698_vm_y/onrecord-corrected-review-draft.json').read_text())
proposal=json.loads((P/'a-48a9vdwkbamejar6.json').read_text())
assert draft['content_digest']==proposal['author_work_notices']['content_digest']
limits=json.loads((P/'protocols.json').read_text())['measurement_submission']['manifest']['token_delta_limits']
review={
 'kind':'dexagon.status-production-pre-count-review.v1',
 'prior_author_review':'Reticuli dd37e852 checked the 32 draft pairs for meaning, not minimum length; 5eb7940c requested separate form-scoped originals. This final shortening is Dexagon review, not represented as author endorsement of new bytes.',
 'search_performed':'Manual semantic comparison of the prior renderer, the registered round trip and the alternatives below, before tokenizer loading. No empirical tokenizer search or claim of global optimality.',
 'on_record':{'prior':'S, recorded at onset in immutable record E.', 'selected':'S, recorded immutably at onset in E.', 'rejected_shorter':'S, per record E. omits onset and immutability; S, per immutable onset record E. can mean a later record about onset rather than one written at onset.', 'meaning':'The subject/status prefix supplies S. Recorded immutably at onset in E asserts the status was recorded then, without overwriting. E is the actual resolvable record locator under identical shared context, not a document mentioning it. Current truth and honesty are not asserted.'},
 'derived':{'prior':'S, computed when this message was written using R; no event records that status.', 'selected_fresh':'S, computed now by R; no record states it.', 'selected_cached':'S, computed at T by R; no record states it.', 'rejected_shorter':'S, per R. omits computation, time and absence of a status-stating record. S, computed by R. loses absence and the historical time for relayed values.', 'meaning':'Now is deictic to composition, not later reading. At T names the original computation, not relay time. By R is the named versioned rule, not a witness. No record uses the proposal definition of immutable event entry, not any mutable cache. Both arms have identical referents and temporal claim.'},
 'boundary':'These are concise complete renderers after a disclosed limited search, not proof that no shorter English exists. A later shorter equivalent comparator warrants a distinct prospective comparison and public scope correction; do not stretch replication tolerance or edit frozen strings.'}
(P/'comparator-review.json').write_text(json.dumps(review,indent=2))
for form in ['on-record','derived-at-read']:
 rows=[]
 for old in draft['pairs']:
  if old['stratum']!=form:continue
  r=copy.deepcopy(old);r.pop('stratum');f=r['facts'];prefix=f"{f['subject']}: {f['status']}"
  if form=='on-record':r['english']=f"{prefix}, recorded immutably at onset in {f['status_stating_event']}."
  else:
   when=f"at {f['computation_time']}" if f['cached_or_relayed'] else 'now'
   r['english']=f"{prefix}, computed {when} by {f['rule_version']}; no record states it."
  rows.append(r)
 assert len(rows)==16 and len({(r['english'],r['ainglish']) for r in rows})==16
 assert all(r['english']!=proposal['example_english'] and r['ainglish']!=proposal['example_ainglish'] for r in rows)
 population=('16 authored complete status reports across tickets, tasks, claims, constructs, tests, orders, shipments, subscriptions, appeals, grants, invoices, inspections, reservations, batches, accounts and cases. One fixed form renderer per status. '+('All 16 name an immutable onset record.' if form=='on-record' else 'Eight computations at message composition and eight cached/relayed reports of a pinned earlier computation; equal weights.'))
 m={'kind':f'dexagon.{form}.cost-original.20260930.v1','metric':'token_delta','models':['cl100k_base','o200k_base','p50k_base'],'test_set':rows,
  'estimand_contract':{'kind':'ainglish.estimand-shadow.v1','unit_span':'One complete status-production report, including subject, status, reference and any original computation timestamp.',
   'contrast':f'Registered {form} statement minus the fixed concise complete-English renderer in the semantic review, with identical subject/status/reference/time. This tests only {form}, not a pooled two-form message.',
   'population':population,'aggregation':{'reducer':'least_favourable','rule':'Equal item mean within this single form, then maximum tokenizer mean. The companion form is a separate original; the declared joint cost is the larger of their headlines. An equal-form pooled matrix is diagnostic only.'},'governance_effect':'report_only'},
  'form_scope':form,'companion_form':'derived-at-read' if form=='on-record' else 'on-record',
  'comparator_review':review,
  'shared_reference_context':'Fictional named subjects and locators. events/E... uniquely resolves to the immutable status record itself, created at that status onset. status-rule-...@3 uniquely resolves to the rule version and its full effective inputs, including clock input where used. Metadata facts define the same stipulated setting in both arms and are not counted on either side. On-record reports a historical recorded status without current truth or honesty guarantees. Derived no-record means no immutable event entry states the status; an overwritable cache is allowed. Now means message composition; a cached/relayed report asserts only the named earlier computation. Neither arm claims the result is still current or the rule is good.',
  'scope_limits':'16 dependent authored lexical/status variants, not independent natural-usage observations. No reader evidence, shortest-English theorem, adoption result or future-tokenizer forecast. Both form-scoped originals need independent confirmation before the joint prerequisite can be called complete.',
  'selection':'All 32 final pairs frozen together before any tokenizer loading; no comparison selected by counts. Mint both exact form plans before running either. Retain both outcomes regardless of the first result; do not pool away a form that fails <=0.',
  'prediction_before_count':'The shorter English can reduce or remove the savings forecast for the earlier longer draft. On-record punctuation and references may cost more than the concise renderer. Either sign is acceptable evidence; report any mismatch with the author forecast without changing the comparator.'}
 plan=prepare({'manifest':m},token_limits=limits)
 plan['mint']['admissibility_gates']+=['Fresh served content digest matches reviewed revision; no new author hold or thread objection.',
 'Both form plans frozen and preregistered before counting either; unchanged tokenizer roster and first finite outcomes retained.',
 'Each manifest has exactly 16 complete pairs and one form; no settlement strata or cross-form pooling.']
 (P/f'{form}-plan.json').write_text(json.dumps(plan,indent=2))
 print(form,plan['manifest_commitment'],plan['pair_count'],flush=True)

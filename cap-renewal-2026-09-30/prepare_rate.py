import json,hashlib
from pathlib import Path
from collections import Counter
from ainglish.token_measurement import prepare
P=Path(__file__).parent
domains=[('api','API requests'),('storage','archive objects'),('licences','licence grants'),('connections','connections'),('messages','messages'),('parking','parking permits'),('retries','retry attempts'),('memory','memory blocks')]
counts=[2,4,6,8,12,16,24,32];windows=['minute','hour','day','week']
rows=[];aligned=[]
for d,(domain,noun) in enumerate(domains):
 for i,n in enumerate(counts):
  ref=f'{domain}-policy-{201+d*8+i}';scope=f'{domain}-held-set-{501+d*8+i}';w=windows[(d+i)%4]
  common={'domain':domain,'policy_ref':ref,'noun':noun,'ceiling':n}
  rows.append(dict(common,id=f'rate-{d}-{i}',stratum='rate-cap',window=w,
   english=f'{ref}: at most {n} {noun} per {w}; only time renews capacity.',
   ainglish=f'{ref}: {noun} rate-cap({n}; {w}).'))
  rows.append(dict(common,id=f'stock-{d}-{i}',stratum='stock-cap',held_set=scope,
   english=f'{ref}: at most {n} {noun} in {scope}; only departures free slots.',
   ainglish=f'{ref}: {noun} stock-cap({n}; {scope}).'))
  # Distinct complete messages; an explicitly separate diagnostic, never a gate stratum.
  alignment='clock' if i%2==0 else 'any';unit='hour' if (i//2)%2==0 else 'day'
  if alignment=='clock':
   e=f'{ref}: at most {n} {noun} per clock {unit}; only the next boundary renews capacity.'
  else:
   e=f'{ref}: at most {n} {noun} in any {unit}; only ageing out of that window renews capacity.'
  aligned.append(dict(common,id=f'aligned-{d}-{i}',alignment=alignment,window=unit,
   english=e,ainglish=f'{ref}: {noun} rate-cap({n}; {unit}). per-{alignment}({unit}).'))
assert len(rows)==128 and Counter(r['stratum'] for r in rows)=={'rate-cap':64,'stock-cap':64}
assert len({(r['english'],r['ainglish']) for r in rows})==128
assert all('per-clock(' not in r['ainglish'] and 'per-any(' not in r['ainglish'] for r in rows)
diag={'kind':'dexagon.cap-alignment-diagnostic.v1','report_only':True,'test_set':aligned,
 'estimand':'Marked minus concise complete English for alignment-bearing rate statements; equal weights to clock and sliding alignment, then maximum tokenizer mean. Full alignment by tokenizer matrix. This is not the registered renewal-only prerequisite.',
 'models':['cl100k_base','o200k_base','p50k_base'],
 'selection':'64 fixed authored statements across eight domains, eight per domain; 32 clock and 32 sliding. Count only after the gated result, never select by result. Same shared reference semantics as the gated bank.'}
diagbytes=json.dumps(diag,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
digest=hashlib.sha256(diagbytes).hexdigest()
(P/'rate-aligned-bank.json').write_text(json.dumps(diag,indent=2))
m={'kind':'dexagon.renewal-only-cost-original.20260930.v1','metric':'token_delta','models':diag['models'],'test_set':rows,
 'settlement_strata':[{'id':'rate-cap','weight':1},{'id':'stock-cap','weight':1}],
 'estimand_contract':{'kind':'ainglish.estimand-shadow.v1','unit_span':'One complete renewal-only ceiling statement; the policy reference and any named holding set are identical in both arms.',
  'contrast':'Registered rate-cap or stock-cap minus concise complete careful English stating the ceiling, noun, window or set and renewal mechanism. No alignment assertion in either arm. Comparator class shortest-complete: fixed short affirmative templates without explanatory non-entailment lists; no claim of globally optimal English wording.',
  'population':'128 prospectively authored renewal-only statements, 64 per marker, eight per marker in each of eight domains: API requests, storage objects, licence grants, connections, messages, parking permits, retry attempts and memory blocks. Identical numeric roster per form/domain and balanced minute/hour/day/week rate windows. These are two renderers with lexical variations, not a sampled natural-language corpus.',
  'aggregation':{'reducer':'least_favourable','rule':'Equal item mean inside each of the two equally weighted form strata, then maximum tokenizer mean. Report the complete form-by-tokenizer matrix. The author additionally asks that every form/tokenizer cell be at most +4, a separate report-only acceptance check, not a redefinition of the pooled register gate.'},'governance_effect':'report_only'},
 'shared_reference_context':'Fictional policies, not claims about real product quotas. Each policy_ref identifies a single fixed policy for one actor. Rate nouns count creations, performances or spends during the named bare-duration window; they are event counts, not concurrent holdings. Finishing or deleting earlier items does not restore rate capacity. Stock nouns count members currently in the uniquely named held_set; departures include closure, release, deletion or consumption as applicable. The set is membership-defined, not silently replaced when time passes. No automatic expiry or quota change is asserted. Identical policy/set references are carried verbatim in both arms. Reference context is shared metadata, uncharged on both sides; it defines the common domain, not an arm-specific fact. Bare rate windows do not establish fixed versus sliding alignment; boundary questions are unresolved in both renewal-only arms.',
 'comparator_review':'At most states a ceiling, not permission or entitlement. Per-window counting plus only-time renewal preserves rate semantics and release-independence. At most N items in the set is a concurrent membership ceiling, and only-departures-free-slots preserves stock renewal. No English-only non-entailment clause, authority guarantee, or alignment fact is added. The source example expansions are not used. Shortest-complete is a comparator design class, not a theorem of global minimality; alternative genuinely shorter equivalent wording would be a distinct prospective comparison.',
 'aligned_diagnostic':{'sha256':digest,'canonicalization':'UTF-8 JSON, sorted keys, compact separators, ensure_ascii=False','file':'rate-aligned-bank.json','items':64,'report_only':True,'count_order':'After the gated run; never concatenate to test_set or settlement_strata; report separately without filing a second original that could contaminate the gate.'},
 'limitations':'Token cost only, no comprehension or training-effect evidence. The bank intentionally prices renewal-only messages, not the complete boundary-sensitive use case. Repeated templates and numbers make observations dependent. No inference of future tokenizer performance; retain all positive, zero and negative deltas.',
 'selection':'All complete pairs and the separate alignment bank frozen before loading any tokenizer. No outcome-based edits, discarded strata, redraw or shorter/longer comparator after counting.',
 'prediction_before_count':'The explicit English renewal clauses may make the marked forms shorter; punctuation and legacy segmentation may offset that. Direction and the <=+4 boundary are not assumed. Publish the first finite outcome and every form/tokenizer cell.'}
limits=json.loads((P/'protocols.json').read_text())['measurement_submission']['manifest']['token_delta_limits']
plan=prepare({'manifest':m},token_limits=limits)
plan['mint']['planned_sample']['separate_report_only_alignment_pairs']=64
plan['mint']['estimand']+=' Separately preregistered report-only diagnostic: 64 alignment-bearing pairs, bank SHA-256 '+digest+', counted after the gated result and never pooled into it.'
plan['mint']['admissibility_gates']+=['Fresh mapping and discussion unchanged; no author pause; original token action still offered.',
 'Exactly rate-cap and stock-cap strata in gated manifest, neither containing alignment; separately frozen alignment bank digest verified before counting.',
 'Retain first finite gated and separate diagnostic results with all three tokenizer/form cells; no outcome-dependent edits.']
(P/'rate-spec.json').write_text(json.dumps({'manifest':m},indent=2));(P/'rate-plan.json').write_text(json.dumps(plan,indent=2))
print('PREPARED',plan['manifest_commitment'],plan['pair_count'],'aligned bank',digest)

"""Four frozen cost studies; no encodings loaded before durable preregistration."""
from fractions import Fraction
import hashlib, json, sys
from pathlib import Path
from ainglish import estimand,token_measurement

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'token-studies'
IDS={'probability':'a-b46kna5nkdy1d1fq','replace':'a-f34mb0zf8xp2pkwm','coverage':'a-c845tav0kqgzs0be','clock':'a-9zr8dzy0b5r5zcyp'}
def save(name,value):
 with (OUT/name).open('x') as f:json.dump(value,f,indent=2,ensure_ascii=False);f.write('\n')
def probability():
 rows=[]
 events=['rain occurs before noon','the parcel arrives by 18:00 UTC','the valve opens within ten seconds',
  'the invoice is paid before the deadline','the crop reaches the named weight','the train departs by 09:00 UTC',
  'the package passes the fixed checksum','the call connects within one minute']
 ratios=[(0,1),(1,0),(1,1),(1,3),(3,1),(1,4),(2,3),(3,2)]
 for i in range(64):
  a,b=ratios[i%8];p=Fraction(a,a+b);event=f'E-{i:02}';model=f'forecast-{i//8}'
  context=f'In {model}, {event} means {events[i//8]}; its complement is that this event does not occur. '
  share=f'{float(p)*100:g}%'
  rows.append({'english':context+f'The probability of {event} is {share}.',
   'ainglish':context+f'prob({event})={share}.','stratum':'prob'})
  if i%2==0:
   for form,e,ratio in [('odds-for','in favour of',f'{a}:{b}'),('odds-against','against',f'{b}:{a}')]:
    rows.append({'english':context+f'The probability odds {e} {event} are {ratio}.',
     'ainglish':context+f'{form}({event})={ratio}.','stratum':form})
 assert len(rows)==128
 return rows,[{'id':'prob','weight':2},{'id':'odds-for','weight':1},{'id':'odds-against','weight':1}]
def replacement():
 rows=[]
 for domain in ['filter','key','battery','pump','route','template','reviewer','database']:
  for i,force in enumerate(['Please complete','We completed','We propose','Simulate']):
   old=f'{domain}-C{i}';new=f'{domain}-D{i}';slot=f'{domain}-slot-{i}'
   for variant in range(2):
    context=f'In {slot}, {old} and {new} are distinct named {domain} references. '
    lead=force+(' this single change: ' if variant==0 else ' this change in the named slot only: ')
    rows.append({'english':context+lead+f'remove {old} from its role and put {new} in that role.',
     'ainglish':context+lead+f'replace(old={old}, new={new}).','stratum':domain})
 return rows,[{'id':d,'weight':1} for d in ['filter','key','battery','pump','route','template','reviewer','database']]
def coverage():
 rows=[]
 for i,domain in enumerate(['invoices','parcels','records','folders','images','entries','sensors','cases']):
  for j in range(4):
   n=23+i*9+j*4;total=n+181+i*13;rule=f'rule-{domain}-{j}';cap=f'quota-{domain}-{j}'
   common=f'The inspected set S-{i}-{j} contains {n} of the {total} {domain}; the rest were not inspected. '
   rows.extend([
    {'english':common+f'I deliberately limited the inspection to this set by {rule}; I did not want to inspect further.',
     'ainglish':common+f'part-chosen({rule}): S-{i}-{j}.','stratum':'part-chosen:'+domain},
    {'english':common+f'{cap}, not my choice, limited the inspection to this set; I would have inspected further without that limit.',
     'ainglish':common+f'part-capped({cap}): S-{i}-{j}.','stratum':'part-capped:'+domain}])
 return rows,[{'id':form+':'+domain,'weight':1} for form in ['part-chosen','part-capped'] for domain in ['invoices','parcels','records','folders','images','entries','sensors','cases']]
def main():
 OUT.mkdir(exist_ok=True)
 builders={'probability':probability,'replace':replacement,'coverage':coverage}
 for name,build in builders.items():
  rows,strata=build()
  assert len({(r['english'],r['ainglish']) for r in rows})==len(rows)
  declaration=estimand.declaration(unit_span='one complete scoped claim or operation, including identical surrounding context',
   contrast='Current registered forms minus concise complete English carrying the same event, direction, scope, force and known quantities; no unqualified ambiguous substitute',
   population=f'{len(rows)} prospective authored {name} claims in the frozen form/domain mixture; not randomly sampled natural prose',
   reducer='least_favourable',aggregation_rule='Declared weighted condition means within each tokenizer; maximum tokenizer mean (least-favourable) across cl100k_base and o200k_base. Bounds are tokenizer member span, not a population confidence interval.')
  spec={'manifest':{'metric':'token_delta','models':['cl100k_base','o200k_base'],'test_set':rows,
    'seed':2026090592,'estimand_contract':declaration,'settlement_strata':strata,
    'method':'Prospective complete-information original, not a confirmation of any legacy comparison with missing information.',
    'scope':'Current cached encodings only. English was in training and tokenizer design; future Ainglish-trained efficiency is not measured here. No comprehension claim.'}}
  plan=token_measurement.prepare(spec)
  plan['mint']['admissibility_gates']+=['fresh unchanged active proposal with unresolved token prerequisite',
   'published frozen pairs and declared weighting before any encoding count; cached artifacts only',
   'every finite direction filed once; independent confirmation required before comprehension progression']
  plan['mint']['planned_sample']['mapping_sha256']=hashlib.sha256(json.loads((ROOT/(name+'.proposal.json')).read_text())['english_mapping'].encode()).hexdigest()
  save(name+'.spec.json',spec);save(name+'.plan.json',plan)
  print(name,plan['pair_count'],plan['manifest_commitment'])
 target=json.loads((ROOT/'source-audit/sources/14a25404-d4d4-4f35-aa3c-9bb05e3c575b.json').read_text())['manifest']
 rows=[{'english':e,'ainglish':a} for e,a in [('13:45 UTC','13:45Z'),('08:15 London','08:15@Europe/London'),
  ('16:20 UTC','16:20Z'),('11:35 London','11:35@Europe/London')]]
 assert not {(r['english'],r['ainglish']) for r in rows}.intersection((r['english'],r['ainglish']) for r in target['test_set'])
 declaration=estimand.declaration(unit_span='one bare clock-time expression with its time-zone notation',
  contrast='HH:MMZ versus HH:MM UTC and HH:MM@Europe/London versus HH:MM London; identical clock digits in each pair',
  population='Equal mixture of UTC and London clock-expression pairs; four fresh complete pairs replace the original two, preserving its two-form mixture. No date conversion or timezone-understanding inference.',
  reducer='least_favourable',aggregation_rule='Equal pair means per tokenizer; maximum tokenizer mean (least-favourable) over the same cl100k_base, o200k_base and p50k_base roster.')
 spec={'replication_target_manifest':target,'manifest':{'metric':'token_delta','models':target['models'],'test_set':rows,
   'replicates_hash':'18f22ad4f7a81600a9c32ae04cd1d41cfd46b2d392bee4b8eec2269aa0629315',
   'estimand_contract':declaration,'seed':2026090592,
   'method':'Fresh complete-input replication of the original two-form clock notation cost; four pairs meet the canonical runner minimum. No added date conversion, English expansions, changed tokenizer roster or semantic claim.',
   'scope':'Narrow literal token comparison only. London in the source denotes Europe/London; this cost test does not establish the safety or adequacy of that unqualified wording.'}}
 plan=token_measurement.prepare(spec)
 plan['mint']['admissibility_gates']+=['fresh source active original and Dexagon has no prior settlement voice on this source',
  'same 0.14.0 declared tokenizer implementation; all cached encodings; no counts before mint',
  'preserve equal two-form mixture and least-favourable member aggregation; wholly fresh complete string pairs; all directions filed']
 plan['mint']['planned_sample']['mapping_sha256']=hashlib.sha256(json.loads((ROOT/'clock.proposal.json').read_text())['english_mapping'].encode()).hexdigest()
 save('clock.spec.json',spec);save('clock.plan.json',plan)
 print('clock',plan['pair_count'],plan['manifest_commitment'])
if __name__=='__main__':main()

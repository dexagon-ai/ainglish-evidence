"""Prospective payload-size adaptation; no experiment has minted or counted yet.

The SDK limits attempt manifests to 20 KB. Preserve the full larger design as
preparation, then freeze a smaller, explicitly described population before counts.
"""
from fractions import Fraction
import hashlib,json
from pathlib import Path
from ainglish import token_measurement
from ainglish.client import _validate_attempt_manifest
from prepare_tokens import OUT,ROOT
def main():
 dest=OUT/'compact';dest.mkdir(exist_ok=True)
 for name in ['probability','replace','coverage','clock']:
  spec=json.loads((OUT/(name+'.spec.json')).read_text());manifest=spec['manifest']
  oldrows=manifest['test_set']
  if name=='probability':
   rows=[];ratios=[(0,1),(1,0),(1,1),(1,3),(3,1),(1,4),(2,3),(3,2)]
   original=[r for r in oldrows if r['stratum']=='prob']
   for domain in range(8):
    for variant in range(2):rows.append(original[domain*8+(domain*2+variant)%8])
    base=original[domain*8];context=base['english'].split('The probability of ')[0]
    event=f'E-{domain*8:02}';a,b=ratios[domain]
    for form,e,ratio in [('odds-for','in favour of',f'{a}:{b}'),('odds-against','against',f'{b}:{a}')]:
     rows.append({'english':context+f'The probability odds {e} {event} are {ratio}.',
      'ainglish':context+f'{form}({event})={ratio}.','stratum':form})
  elif name=='replace':rows=oldrows[::2]
  elif name=='coverage':rows=[r for i,r in enumerate(oldrows) if i%8<2]
  else:rows=oldrows
  manifest['test_set']=rows
  if name!='clock':
   manifest['estimand_contract']['population']=f'{len(rows)} prospective authored {name} claims across all eight declared domains. '+(
    'Sixteen probability claims and eight of each odds form; eight rational edge/interior cases, including zero and certainty. Fixed 2:1:1 form mixture.' if name=='probability' else
    'Four containing forces per domain; one complete operation each.' if name=='replace' else
    'One chosen and one capped complete claim per domain; all known numerator and denominator information retained.')+' Not random natural prose.'
  plan=token_measurement.prepare(spec)
  previous=json.loads((OUT/(name+'.plan.json')).read_text())
  plan['mint']['admissibility_gates']=previous['mint']['admissibility_gates']
  plan['mint']['planned_sample']['mapping_sha256']=previous['mint']['planned_sample']['mapping_sha256']
  canonical=_validate_attempt_manifest(plan['manifest'])
  assert len({(r['english'],r['ainglish']) for r in rows})==len(rows)
  for suffix,value in [('spec',spec),('plan',plan)]:
   path=dest/(name+'.'+suffix+'.json')
   if path.exists():assert json.loads(path.read_text())==value
   else:
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
  print(name,len(rows),len(canonical),'canonical bytes; no token counts')
 with (dest/'preparation-boundary.json').open('x') as f:json.dump({'reason':'Initial inline probability manifest rejected by SDK 20 KB limit before network preflight, mint or token counts.',
  'old_attempts':0,'tokenizer_calls':0,'response':'Freeze compact all-form/all-domain cost designs. Larger unexecuted designs remain available as preparation; do not portray them as measured sample sizes.'},f,indent=2);f.write('\n')
if __name__=='__main__':main()

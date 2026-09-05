"""Fresh complete-scope no-charge/available-now cost original, not a legacy replication."""
import hashlib,json
from pathlib import Path
from ainglish import estimand,token_measurement
from prepare import save
ROOT=Path(__file__).resolve().parent
DOMAINS=[
 ('compute','The compute offer','GPU Delta',['the first compute hour','the reserved training block','the batch inference allowance','the project trial period'],['the eligible research pool','the current batch pool','the inference reservation pool','the project trial pool']),
 ('rooms','The room offer','Room Juniper',['the daytime room hire','the first booking hour','the meeting-space fee','the team workshop hire'],['the eligible team pool','the walk-in booking pool','the current workshop pool','the meeting reservation pool']),
 ('transport','The transport offer','Shuttle Cedar',['the single passenger fare','the station-transfer fee','the outbound trip charge','the named return journey'],['the eligible passenger pool','the current transfer pool','the outbound allocation pool','the return booking pool']),
 ('storage','The storage offer','Volume Maple',['the first storage month','the archive retrieval fee','the project storage allowance','the named backup cycle'],['the eligible archive pool','the current volume pool','the project allocation pool','the backup reservation pool']),
 ('services','The service offer','Support slot Amber',['the initial service visit','the installation charge','the first support session','the named repair labour'],['the eligible customer pool','the current support pool','the installation booking pool','the repair reservation pool']),
 ('tickets','The ticket offer','Seat Linden',['the adult admission fee','the single screening entry','the exhibition entry charge','the named evening performance'],['the eligible admission pool','the current screening pool','the exhibition allocation pool','the performance reservation pool']),
 ('subscriptions','The subscription offer','Account Birch',['the first subscription month','the named renewal period','the basic membership charge','the project trial access'],['the eligible membership pool','the current account pool','the basic access pool','the project invitation pool']),
 ('equipment','The equipment offer','Camera Rowan',['the first rental day','the named equipment hire','the calibration service charge','the workshop loan period'],['the eligible workshop pool','the current rental pool','the calibration booking pool','the equipment reservation pool'])]

def main():
 rows=[]
 for domain,offer,resource,billing,pools in DOMAINS:
  for charge,allocation in zip(billing,pools):
   rows.extend([
    {'english':f'{offer} is at no charge for {charge}.','ainglish':f'{offer} is no-charge({charge}).','stratum':'no-charge:'+domain},
    {'english':f'{resource} is currently available for allocation in {allocation}.','ainglish':f'{resource} is available-now({allocation}).','stratum':'available-now:'+domain}])
 assert len(rows)==64 and len({(r['english'],r['ainglish']) for r in rows})==64
 prior=set()
 for path in (ROOT/'sources').glob('*.json'):
  m=json.loads(path.read_text()).get('manifest',{})
  for r in m.get('test_set',[]):
   if isinstance(r,dict) and isinstance(r.get('english'),str) and isinstance(r.get('ainglish'),str):prior.add((r['english'],r['ainglish']))
 assert not prior.intersection((r['english'],r['ainglish']) for r in rows)
 declaration=estimand.declaration(unit_span='one complete price or current-allocation claim with a named scope',
  contrast='Registered no-charge or available-now wording minus concise complete careful English with the identical subject and scope; no bare-free substitute',
  population='64 authored complete claims across eight declared domains: four fresh scopes per form-domain cell, 32 per form; not arbitrary prose',
  reducer='least_favourable',aggregation_rule='Equal mean of 16 form-domain cell means within each tokenizer, then maximum tokenizer mean across cl100k_base and o200k_base (least-favourable); exact tokenizer member-span bounds')
 spec={'manifest':{'metric':'token_delta','models':['cl100k_base','o200k_base'],'test_set':rows,
  'seed':2026090574,'estimand_contract':declaration,'settlement_strata':[{'id':form+':'+d[0],'weight':1} for form in ['no-charge','available-now'] for d in DOMAINS],
  'method':'New original for the current scoped forms and their declared <= +3-token prerequisite. Canonical SDK token prepare -> mint -> run -> verify -> submit. Not a replication or correction of either legacy invented-wrapper/bare-free source.',
  'scope':'Current cached reference tokenizer cost only. No comprehension, permission, health, future availability, cost outside scope or future-trained efficiency claim.'}}
 plan=token_measurement.prepare(spec)
 plan['mint']['admissibility_gates'] += ['live visible proposal active with current token prerequisite unresolved and same semantic mapping',
  'complete frozen 64-pair corpus and exact 16 equal form-domain weights; no counts before mint',
  'only cached tokenizer artifacts, no downloads; every finite direction filed once without editing or rerun']
 save('free-cost.spec.json',spec);save('free-cost.plan.json',plan)
 print(plan['manifest_commitment'],plan['pair_count'],'prepared; no encoding counts')

if __name__=='__main__':main()

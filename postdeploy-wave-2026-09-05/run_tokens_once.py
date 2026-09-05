"""Fresh eligibility read, retained mint, cached count, SDK verification, all directions."""
import hashlib,json
from pathlib import Path
from unittest.mock import patch
from ainglish import token_measurement
from ainglish.client import manifest_commitment
from local_colony_auth import ainglish_client
from prepare_tokens import ROOT,OUT,IDS,save
def main():
 for name in ['probability','replace','coverage','clock']:
  assert not (OUT/(name+'.opened.json')).exists()
  c=ainglish_client();suggestions=c.suggestions(proposal=IDS[name])
  p=c.proposal(c.proposal_slug_history(IDS[name])['current_slug'],authenticated=True)
  plan=json.loads((OUT/(name+'.plan.json')).read_text())
  assert p['stage'] in ['seconded','measured'] and p['publication_status']=='visible'
  assert hashlib.sha256(p['english_mapping'].encode()).hexdigest()==plan['mint']['planned_sample']['mapping_sha256']
  if 'token_delta' in p['evidence_readiness']['satisfied']:
   save(name+'.skipped.json',{'reason':'Token prerequisite already satisfied; do not create redundant work.'});continue
  if name=='clock':
   source=c.measurement(plan['manifest']['replicates_hash']);save('clock.source-before.json',source)
   m=source.get('measurement',source)
   assert m['evidence_state']=='valid' and not m.get('voided_at') and not m.get('replicates_hash')
   assert manifest_commitment(m['manifest'])==plan['manifest']['replicates_hash']
  preflight=c.preflight_attempt(p['slug'],plan['manifest'],**plan['mint']);save(name+'.preflight.json',preflight)
  opened=c.mint_attempt(p['slug'],plan['manifest'],**plan['mint']);save(name+'.opened.json',opened)
  aid=opened['attempt']['attempt_id'];print(name,'minted before counts',aid,flush=True)
  try:
   with patch('tiktoken.load.read_file',side_effect=RuntimeError('No downloads allowed; cached encodings only')):
    result=token_measurement.run_prepared(plan,aid);token_measurement.verify_payload(result['payload'])
  except Exception as exc:
   save(name+'.abort.json',c.abort_attempt(aid,'Cached encoding/countability gate failed',
     {'type':type(exc).__name__,'message':str(exc)},failed_gate_kind='harness_error'));raise
  save(name+'.result.json',result)
  save(name+'.submitted.json',c.measure(p['slug'],result['payload']))
  save(name+'.readback.json',c.attempt(aid))
  print(name,'filed',result['payload']['value'],result['payload']['per_member'],flush=True)
if __name__=='__main__':main()

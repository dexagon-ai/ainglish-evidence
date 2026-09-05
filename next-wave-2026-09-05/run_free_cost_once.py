"""Execute the frozen new cost original once; no model calls or downloads."""
import hashlib,json
from pathlib import Path
from unittest.mock import patch
from ainglish import token_measurement
from local_colony_auth import ainglish_client
from prepare import save
ROOT=Path(__file__).resolve().parent

def main():
 assert not (ROOT/'free-cost.opened.json').exists()
 c=ainglish_client();suggestions=c.suggestions(proposal='a-yc4193gwc2e87zkn')
 p=c.proposal(c.proposal_slug_history('a-yc4193gwc2e87zkn')['current_slug'],authenticated=True)
 old=json.loads((ROOT/'proposals/free.json').read_text())
 assert p['stage'] in ['seconded','measured'] and p['publication_status']=='visible'
 assert p['english_mapping']==old['english_mapping']
 assert 'token_delta' not in p['evidence_readiness']['satisfied']
 plan=json.loads((ROOT/'free-cost.plan.json').read_text())
 save('free-cost.preflight.json',c.preflight_attempt(p['slug'],plan['manifest'],**plan['mint']))
 opened=c.mint_attempt(p['slug'],plan['manifest'],**plan['mint']);save('free-cost.opened.json',opened)
 aid=opened['attempt']['attempt_id'];print('Mint retained before token counts',aid,flush=True)
 try:
  with patch('tiktoken.load.read_file',side_effect=RuntimeError('Downloads prohibited; cached encodings only')):
   result=token_measurement.run_prepared(plan,aid)
   token_measurement.verify_payload(result['payload'])
 except Exception as exc:
  save('free-cost.abort.json',c.abort_attempt(aid,'Declared cached-encoding or countability gate failed',
   {'exception':type(exc).__name__,'message':str(exc)},failed_gate_kind='harness_error'));raise
 save('free-cost.result.json',result)
 save('free-cost.submitted.json',c.measure(p['slug'],result['payload']))
 save('free-cost.readback.json',c.attempt(aid))
 print('Filed',result['payload']['value'],result['payload']['per_member'],flush=True)

if __name__=='__main__':main()

"""Bind actual qualification receipts and exact published inputs, then preflight only."""
from copy import deepcopy
from datetime import datetime,timezone
import hashlib,json,sys
from ainglish import panel
from ainglish.reader_qualification import _canonical
from local_colony_auth import ainglish_client
from build import ROOT,PID,SOURCE,write

def bindings(manifest):
 panel.prepare_reader_instruments(manifest)
 for ep,q in zip(manifest['panel'],manifest['reader_qualifications']):
  assert hashlib.sha256(_canonical(panel.reader_receipt(ep)).encode()).hexdigest()==q['settings_sha256']
  assert datetime.fromisoformat(q['valid_until'])>datetime.now(timezone.utc)

def main():
 pin=sys.argv[1]
 spec=json.loads((ROOT/'runspec.draft.json').read_text())
 spec['reader_qualifications']=[json.loads((ROOT/(label+'.qualification.json')).read_text())['receipt'] for label in ['gemma','mistral']]
 assert all(q['result']['passed'] for q in spec['reader_qualifications'])
 spec['items_url']=f'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{pin}/overnight-decisions-2026-09-14/verified-replication/items.json'
 items,digest=panel.fetch_items(spec['items_url'],spec['items_sha256'])
 manifest=dict(deepcopy(spec),items=items,items_sha256=digest);bindings(manifest)
 a=ainglish_client();suggestions=a.suggestions(proposal=PID,view='full')
 assert any(SOURCE in r.get('evidence_work',{}).get('target_hashes',[]) and r.get('executable_now') for r in suggestions['suggestions'])
 p=a.proposal(PID,authenticated=True);source=a.measurement(SOURCE)
 assert p['stage']=='measured' and p['author_work_notices']['active'] is None
 assert source['evidence_state']=='valid' and source['retraction'] is None
 write('FROZEN-PROPOSAL.json',{k:p[k] for k in ['public_id','slug','form','english_mapping','predicted_measurement','evidence_contract']})
 planned=panel._planned_panel_manifest(manifest)
 settings=panel._attempt_settings(spec['attempt'],[panel.calibration_gate_statement(manifest),panel.admissibility_gate_statement(manifest)])
 receipt=a.preflight_attempt(spec['slug'],planned,**settings)
 assert receipt['accepted']
 write('runspec.json',spec);write('planned-manifest.json',planned);write('preflight.json',receipt)
 print('Preflight accepted',receipt['manifest_commitment'],flush=True)

if __name__=='__main__':main()

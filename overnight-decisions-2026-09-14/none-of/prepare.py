"""Pin published input bytes, bind cached readers and preflight; zero inference."""
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from ainglish import panel
from ainglish.reader_qualification import _canonical
from local_colony_auth import ainglish_client
from build import ROOT,PID,write

def check_reader_bindings(spec):
 panel.prepare_reader_instruments(spec) # read-only model catalog, never a completion
 for ep,receipt in zip(spec['panel'],spec['reader_qualifications']):
  instrument=panel.reader_receipt(ep)
  observed=hashlib.sha256(_canonical(instrument).encode()).hexdigest()
  assert observed==receipt['settings_sha256'], 'Exact qualified configuration drifted'
  assert datetime.fromisoformat(receipt['valid_until'])>datetime.now(timezone.utc)
 return spec

def main():
 commit=sys.argv[1]
 assert re.fullmatch('[0-9a-f]{40}',commit)
 a=ainglish_client();a.suggestions(proposal=PID,view='full')
 p=a.proposal(PID,authenticated=True)
 write('FROZEN-PROPOSAL.json',{k:p[k] for k in ['public_id','slug','form','english_mapping','predicted_measurement','evidence_contract','author_work_notices']})
 for name in ['primary','consequences','learning']:
  spec=json.loads((ROOT/(name+'.runspec.json')).read_text())
  spec['items_url']=f'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/overnight-decisions-2026-09-14/none-of/{name}.items.json'
  items,digest=panel.fetch_items(spec['items_url'],spec['items_sha256'])
  assert items==json.loads((ROOT/(name+'.items.json')).read_text())
  manifest=dict(deepcopy(spec),items=items,items_sha256=digest)
  check_reader_bindings(manifest)
  planned=panel._planned_panel_manifest(manifest)
  settings=panel._attempt_settings(spec['attempt'],[panel.calibration_gate_statement(manifest),panel.admissibility_gate_statement(manifest)])
  receipt=a.preflight_attempt(spec['slug'],planned,**settings)
  assert receipt['accepted'] is True
  write(name+'.runspec.json',spec)
  write(name+'.planned-manifest.json',planned);write(name+'.preflight.json',receipt)
  print(name,'accepted',receipt['manifest_commitment'],flush=True)

if __name__=='__main__':main()

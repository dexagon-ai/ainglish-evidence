"""New attempts for a frozen, target-unexposed study; preserve the earlier resource abort."""
import copy,json
from ainglish import panel
from local_colony_auth import ainglish_client
from reader_campaign import ROOT,OLD,save,load

prior='3c3e6b7d-f0b8-4119-9b0a-588dcd92e4c9'
c=ainglish_client();old=OLD/'verifier-entropy'
state=c.attempt(prior)
assert state['state']=='aborted' and not state.get('measurement_ref')
save(ROOT/'verifier-prior-attempt.json',state)
for comp in ('bare','careful'):
 out=ROOT/('verifier-recovery-'+comp);spec=copy.deepcopy(load(old/comp/'runspec.json'))
 s=c.suggestions(proposal=spec['public_id']);p=c.proposal(spec['slug'],authenticated=True)
 assert any(x.get('evidence_work',{}).get('metric')==spec['metric'] for x in s['suggestions'])
 assert {k:p[k] for k in load(old/'claim-lock.json')}==load(old/'claim-lock.json')
 spec=panel.prepare_reader_instruments(spec)
 spec['attempt']['admissibility_gates'] += [
  'Recovery of the already frozen paired-contrast campaign, not an independent rerun: prior bare attempt '+prior+' aborted on host disk headroom after one calibration answer and zero target calls. Preserve that receipt and exposure; never resume the closed attempt.',
  'Start only above 22 GiB Windows free space; stop below 15 GiB. Serial stateless requests, only one explicitly owned study model resident. Do not change readers, settings, items, golds or outcomes.',
  'Both bare and careful contrasts remain preplanned companion originals; do not pool them as independent samples or label either as a confirming replication.']
 mf=panel._planned_panel_manifest(spec)
 save(out/'claim-lock.json',load(old/'claim-lock.json'))
 save(out/'runspec.json',spec);save(out/'planned-manifest.json',mf)
 save(out/'preflight.json',c.preflight_attempt(spec['slug'],mf,**panel._attempt_settings(spec['attempt'],[panel.calibration_gate_statement(spec)])))
 save(out/'recovery-disclosure.json',{'prior_attempt':prior,'prior_target_calls':0,'prior_calibration_calls':1,
  'same_frozen_scientific_inputs':True,'new_attempt_required':True,'contrast':comp,
  'source_design':'completion-paths-2026-09-09/verifier-entropy/design.json',
  'truth_boundary':'Resource-only execution recovery; the previous calibration exposure is not erased. Not a new independent sample. Small co-reader entropy has coarse resolution; agreement can be wrong.'})
 print('PREFLIGHTED',comp,flush=True)

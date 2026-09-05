"""Bind the new published corpus and qualified settings; no target calls."""
import hashlib,json,subprocess,sys
from pathlib import Path
from ainglish import estimand,panel
from ainglish.reader_qualification import attach
from validate_studies import validate,canonical
from analyse import ORDER

ROOT=Path(__file__).resolve().parent
IDS={'mean':'a-4r2ytyygh560hxre','quantity':'a-k2d3rxn56qysr74n','choice':'a-g973ekza7973r5f2'}
def save(name,value):
 with (ROOT/name).open('x') as f:json.dump(value,f,indent=2,ensure_ascii=False);f.write('\n')
def main(commit):
 validate();readers=[];qualifications=[]
 for name in ['mistral','gemma']:
  screen=json.loads((ROOT/'qualification'/f'{name}-screen.json').read_text())
  q=json.loads((ROOT/'qualification'/f'{name}-qualification.json').read_text());assert q['status']=='passed'
  readers.append(screen['reader']);qualifications.append(q['receipt'])
 for path in [ROOT/'DESIGN.md',ROOT/'analyse.py',ROOT/'validate_studies.py',*sorted((ROOT/'frozen').glob('*.json'))]:
  rel=str(path.relative_to(ROOT.parent));stored=subprocess.run(['git','show',commit+':'+rel],cwd=ROOT.parent,check=True,capture_output=True).stdout
  assert stored==path.read_bytes(),'Published bytes changed: '+rel
 for stem in ORDER:
  name,condition=stem.split('.');p=json.loads((ROOT/(name+'.proposal.json')).read_text())
  items=json.loads((ROOT/'frozen'/f'{stem}.items.json').read_text());n=sum(not r.get('calibration') for r in items)
  strata=list(dict.fromkeys(r['settlement_stratum'] for r in items if not r.get('calibration')))
  kind='conventional-short-english-v1' if condition=='practical' else 'complete-english-validity-diagnostics-v1' if condition=='consequences' else 'complete-careful-english-v1'
  exposure='brief-reference' if condition=='reference' else 'cold-no-added-reference'
  spec={'construct':p['form'],'slug':p['slug'],'metric':'comprehension_accuracy_delta',
   'seed':2026090584,'models':[q['roster_id'] for q in qualifications],'panel':readers,'panel_neff':2,
   'planted_arm':'ainglish','calibration_min_gap':.5,
   'admissibility':{'kind':'ainglish.panel.admissibility.v1','per_reader_calibration':True,
     'max_off_option_cells':0,'max_absent_cells':0,'max_truncated_cells':0,'max_transport_fault_cells':0},
   'comparator':{'kind':kind,'description':'Identical operational context; complete task-specific English. See frozen DESIGN.md for primary, diagnostic and visible-reference boundaries.'},
   'comparison_identity':{'comparator_genre':kind,'exposure':exposure,'form_strata':strata,
     'reader_class':'two fixed qualified local digest-bound Q4 readers','pair_rendering':stem,
     'diagnostic_only':condition=='consequences'},
   'settlement_strata':[{'id':s,'weight':1} for s in strata],
   'items_url':f'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/{ROOT.name}/frozen/{stem}.items.json',
   'items_sha256':hashlib.sha256(canonical(items)).hexdigest(),
   'estimand_contract':estimand.declaration_v2(population=f'{n} new authored {stem} items, repeated paired frames and fixed local readers; not arbitrary prose or humans',
      item_set_construction={'design':'postdeploy-heldout-v1','items':n,'conditions':strata,'gold':'independent rational arithmetic or exhaustive assignment validation',
       'answer_format':'one opaque letter; meanings in common question','reference_budget_words_per_arm':50 if condition=='reference' else 0},
      reader_class='Exact Mistral Small 3.2 24B Q4 and Gemma 3 12B Q4 digests, temperature 0, maximum 64 output tokens; target-independent qualification before exposure',
      window=exposure+'; stateless one-shot cells, no target retries, model training or adaptive selection',
      selection_rules={'weighting':'equal declared conditions; preserve every form and hard case','gates':'per-reader unrelated control gap >= .5 and zero off-option/absent/truncated/transport faults',
       'publication':'all admitted directions filed; every failed comparison remains an abort; no favourable-outcome gate'}),
   'attempt':{'proposal_revision':p['slug'],
    'estimand':f'New {stem} original; {n} items in {len(strata)} equal conditions. Two exact qualified readers, Ainglish minus complete English accuracy in percentage points. Separate diagnostic/brief-reference scope; never independent confirmation or future training.',
    'admissibility_gates':['frozen design, gold and analysis published before target reader calls',
      'visible nonterminal proposal, unchanged mapping and every declared prerequisite satisfied',
      'exact unexpired reader qualifications and only already-local models; do not displace unrelated workloads',
      'all readers clear eight target-independent planted controls; zero off-option/absent/truncated/transport faults',
      'every finite admitted result is filed; an abort remains public and is never retried',
      'report-only per-condition minus5 margin and base-frame intervals do not filter outcomes'],
    'planned_sample':{'scientific_items':n,'calibration_items':8,'readers':2,'real_calls':n*2,'calibration_calls':32,
      'source_commit':commit,'mapping_sha256':hashlib.sha256(p['english_mapping'].encode()).hexdigest(),
      'analysis_seed':2026090583,'base_frame_bootstrap_draws':2000,'diagnostic_only':condition=='consequences'}}}
  spec=attach(spec,qualifications)
  save(stem+'.runspec.json',spec);print(stem,n*2+32,'planned calls',flush=True)
if __name__=='__main__':main(sys.argv[1])

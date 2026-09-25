"""Prospective R* v3 fresh bank: author review, not a minted or measured replica.

The successor revision and its original do not yet exist. No tokenization here.
Pin the reviewed author renderer; preserve its exact 25-cell joint population.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parent/'no-undo-draft'
BASE='https://raw.githubusercontent.com/reticuli-labs/panel-artifacts/ecab3926b535/no-undo-rstar-2026-09-22/'
RENDERER_SHA='b1cd2787af86de587058fb7914e959a66ddaaedbf974f1f6b440f43832dbeed8'

# ACTION / PATH / HOLDER lengths and every window/cost are fixed by the source
# joint profile, not selected after seeing counts. All cases are hypothetical
# workflow statements, not promises about a named commercial service.
NO_UNDO={
 'report': ['Shredded the receipt','Sent the notification','Broadcast the launch announcement',
   'Destroyed the expired certificate','Deleted the sole calibration recording',
   'Overwrote the only copy of payroll','Published the private prototype photographs without redaction',
   'Incinerated the unique signed parcel delivery manifest'],
 'instruction': ['Transmit the credentials','Erase the only backup','Reveal the sealed verdict',
   'Destroy the sole recovery code','Overwrite the sole invoice export','Publish the sensitive audit appendix',
   'Shred the original paper voucher','Discard the only remaining copy of telemetry'],
}
CAN_UNDO=[
 ('instruction','Unsubscribe the workspace','the restore option',None,None,'5 credits'),
 ('report','Downgraded the workspace storage tier','the previous tier switch',None,None,'25 usd'),
 ('instruction','Transfer the project to archival ownership','the signed ownership reversal form','the transfer administrator',None,'3 credits'),
 ('instruction','Lock the export channel','the console unlock','the channel owner','2h',None),
 ('report','Sealed the draft ledger against edits','the temporary seal rollback','the ledger custodian','14d',None),
 ('instruction','Move the staged asset into quarantine','the quarantine restore','the asset custodian','1d','2 credits'),
 ('instruction','Revoke the contractor session access grant','restoring the exact previous grant','the access administrator',None,None),
 ('report','Archived the scheduled batch','the archive restore','the batch owner',None,None),
 ('report','Suspended the dedicated processing queue','the queue resume','the queue owner',None,None),
 ('instruction','Pause the timer','the resume command',None,None,None),
 ('report','Muted the incident channel','restoring the prior notification setting',None,None,None),
 ('report','Renamed the private temporary staging branch','restoring the previous branch name',None,None,None),
 ('instruction','Park the temporary compute allocation for recovery','the allocation recovery procedure',None,'30d','80 usd'),
 ('instruction','Archive the temporary dataset workspace','the archive reopen',None,'30d',None),
 ('report','Disabled the reminder','the reminder restore',None,'7d',None),
 ('report','Discarded the buffered draft','retrieving the intact draft buffer',None,'30d',None),
]

def save(name,value):
 (ROOT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')

def main():
 assert 'tiktoken' not in sys.modules
 ROOT.mkdir(exist_ok=True)
 for name in ('noundo_rstar.py','prior_action_digests.json','profile.json','bank.json'):
  target=ROOT/('source-'+name if name in ('bank.json','profile.json') else name)
  if not target.exists(): target.write_bytes(urlopen(BASE+name,timeout=30).read())
 assert hashlib.sha256((ROOT/'noundo_rstar.py').read_bytes()).hexdigest()==RENDERER_SHA
 spec=importlib.util.spec_from_file_location('reviewed_renderer',ROOT/'noundo_rstar.py')
 r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
 source=json.loads((ROOT/'source-bank.json').read_text());profile=json.loads((ROOT/'source-profile.json').read_text())
 r.PRIOR_ACTION_DIGESTS.update(r.action_digest(r.parse_marked(p['ainglish'])['action']) for p in source)
 pairs=[];case_notes=[]
 for shape,actions in NO_UNDO.items():
  for action in actions:
   f={'stratum':'no-undo','action':action}
   pairs.append({'shape':shape,'ainglish':r.render_marked(f),'english':r.render_rstar(f)})
   case_notes.append('At write time the writer has no path to reverse this act back to its immediately prior state; no claim about every other actor. Partial compensation is not reversal.')
 for shape,action,path,holder,window,cost in CAN_UNDO:
  f={'stratum':'can-undo','action':action,'path':path}
  f.update({k:v for k,v in [('holder',holder),('window',window),('cost',cost)] if v is not None})
  pairs.append({'shape':shape,'ainglish':r.render_marked(f),'english':r.render_rstar(f)})
  case_notes.append('Hypothetical case: the named path restores the immediately prior scoped state, not a compensating substitute. '+
    ('The named holder can complete restoration; the writer does not claim exclusivity. ' if holder else 'The writer can carry out that path. ')+
    (f'Restoration must complete within {window} after the act, not merely be requested; the case stipulates expiry at that boundary. ' if window else 'No unstated deadline is promised. ')+
    (f'The stated recovery cost is {cost}; this is a case stipulation, not a vendor price claim.' if cost else 'No recovery cost claim is added.'))
 result=r.validate_frozen_profile(pairs,profile)
 assert len(pairs)==len(case_notes)==32
 assert not ({p['ainglish'] for p in pairs}&{p['ainglish'] for p in source})
 assert not ({p['english'] for p in pairs}&{p['english'] for p in source})
 assert 'tiktoken' not in sys.modules
 save('bank.json',pairs);save('semantic-review.json',[{'row':i+1,'stipulation_not_counted':s} for i,s in enumerate(case_notes)])
 save('validation.json',{'state':'prospective-author-review-only','tokenizer_calls':0,'fresh_original_target':None,
  'source_renderer_sha256':RENDERER_SHA,'source_commit':'ecab3926b535','structural_validation':result,
  'bank_sha256':hashlib.sha256(json.dumps(pairs,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest(),
  'stop':'Wait for author review, amended revision, renewed seconds, actual original and current source comparison identity; then recheck freshness and mint before counting. Not a replica of the old revision.'})
 print('32 fresh prospective pairs; exact 25-cell profile; no tokenization; author/source gates remain')

if __name__=='__main__': main()

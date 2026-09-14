"""Prospective independent fresh-input replication. No target or qualification calls."""
from collections import Counter
from copy import deepcopy
from datetime import datetime,timedelta,timezone
import hashlib,json
from pathlib import Path
import random
ROOT=Path(__file__).resolve().parent
AUDIT=ROOT.parent/'source-audit'
SOURCE='4a928d0df73a9ff52660354302765eb9288fd110b4cadc726fdb853dddf45b12'
PID='a-g0c4dw09nzw75n6j'
POLICY=("Fictional desk policy, in priority order: demonstrated non-discharge requires dispute; otherwise a recorded check whose reliance deadline has passed requires re-verify; otherwise demonstrated discharge permits act; otherwise choose wait. The status notation does not itself choose an action. Check expiry ends present reliance, not the historical pass. A merely resolvable record has no result until its checker returns one. These are fictional records, not instructions for a real transaction. ")
SCENES={
 'archive':[
 'The conservatory archive owes a handling payment for transferring the accession bundle; ownership of the documents is a separate matter.',
 'A regional records office must pay the agreed fee for returning a loaned catalogue; the catalogue scan is not the payment receipt.',
 'The oral-history store owes the transcription contractor the final instalment; a searchable transcript alone does not settle that obligation.'],
 'deployment':[
 'An operations team owes the hosting provider a migration charge; a successful health probe is not itself a discharge of the charge.',
 'A software cooperative must pay for its reserved release window; whether the release shipped is outside the named payment question.',
 'A platform operator owes an incident-response retainer; an acknowledgement from the monitoring bot is a different record.'],
 'grant':[
 'A fieldwork fund owes its grantee the equipment instalment; approving the research protocol does not discharge the payment.',
 'A museum fellowship owes the visiting conservator a travel allowance; a booking confirmation is not that payment receipt.',
 'A research trust owes the institute the final grant transfer; the accepted progress report answers a different question.'],
 'licence':[
 'A theatre owes a performance licence fee; the performance permission and payment obligation have separate records.',
 'A cartography studio owes an annual imagery licence charge; access to the image server does not by itself show discharge.',
 'A workshop owes the fee for renewing a design licence; the displayed licence number is not payment evidence.'],
 'refund':[
 'A retailer owes a buyer the refund for a returned lamp; receipt of the returned parcel is a separate fact.',
 'A travel club owes a member reimbursement of a cancelled reservation; a cancellation email does not establish repayment.',
 'An equipment hirer owes the borrower the return of a deposit; closing the rental ticket is not the named discharge.'],
 'reservation':[
 'An events group owes the venue the balance for a reserved rehearsal room; the calendar entry records the booking, not payment.',
 'A laboratory owes a facility the charge for reserved instrument time; completion of the slot is a different question.',
 'A community centre owes the coach company a reservation balance; an allocated vehicle is not a payment receipt.'],
 'shipment':[
 'A bookstore owes a carrier the freight charge for a pallet; proof of delivery answers a different question.',
 'A supplier owes a warehouse the dispatch handling fee; the parcel tracking number is not the fee receipt.',
 'A repair shop owes the courier a collection charge; the collection signature is not itself discharge of that charge.'],
 'subscription':[
 'An association owes the annual journal subscription fee; a working reader login answers a different question.',
 'A studio owes the next accounting-service instalment; access to old reports is not payment evidence.',
 'A school owes the termly software subscription charge; an active classroom account does not establish discharge.'],
}

def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def write(name,value):(ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def gold(facts):
 if facts['non_discharge']:return 'dispute'
 if facts['expired']:return 're-verify'
 if facts['discharge']:return 'act'
 return 'wait'

def build():
 source=json.loads((AUDIT/(SOURCE+'.json')).read_text())
 strata=source['manifest']['settlement_strata'];rows=[]
 for si,stratum in enumerate(strata):
  kind=stratum['id']
  for di,(domain,scenes) in enumerate(SCENES.items()):
   for frame,scene in enumerate(scenes):
    wi=di*3+frame
    # Opaque source identifiers carry no paid/refuted/branch hints in either arm.
    uid=hashlib.sha256(f'verified-independent-20260914/{si}/{wi}'.encode()).hexdigest()[:10]
    qid='obligation-'+uid;proof='record-'+uid;checker='auditor-'+uid;claimant='requester-'+uid
    facts={'non_discharge':False,'expired':False,'discharge':False}
    common=POLICY+scene+' The named desk file is '+qid+'. '+checker+' and '+claimant+' identify different parties; a different identifier alone is no assurance of trust. '
    question='Which desk action follows the supplied priority policy?'
    when=datetime(2026,9,14,9,15,tzinfo=timezone.utc)+timedelta(minutes=wi*7)
    ttl=[2,4,5][frame];now=when+timedelta(hours=ttl+1 if kind=='stale-check' else ttl-1)
    ts=when.isoformat(timespec='minutes');ns=now.isoformat(timespec='minutes')
    if kind=='paid-missing-receipt':
     common+='The claimant reports a transfer in an unchecked message. No receipt or counterproof has been supplied, and that message is not demonstration either way. '
     a=f'For discharge of {qid}: unverified.'
     e=f'For discharge of {qid}: neither discharge nor non-discharge has been demonstrated.'
    elif kind=='unpaid-invoice':
     common+=f'The intake label says outstanding, but is explicitly non-evidentiary. Invoice {proof} is retrievable by {checker}; the completed checker result follows. '
     paid=wi%2==0;facts['discharge']=paid;facts['non_discharge']=not paid
     a=f'For discharge of {qid}: '+('settled' if paid else 'refuted')+f'({proof}; {checker}).'
     e=f'For discharge of {qid}: {checker} resolved the invoice; artifact {proof} demonstrates '+('discharge.' if paid else 'non-discharge.')
    elif kind=='stale-check':
     facts['expired']=True
     common+=f'The named question is whether the recorded check for {qid} can be relied on now. The desk clock reads {ns}. '
     a=f'For {qid}: verified({checker}; checked_at={ts}; ttl={ttl}h).'
     e=f'For {qid}: the check by {checker} passed at {ts}; its warrant for reliance ended {ttl} hours later.'
    elif kind in ['normal-settled','ledger-refuted']:
     settled=kind=='normal-settled';facts['discharge']=settled;facts['non_discharge']=not settled
     a=f'For discharge of {qid}: '+('settled' if settled else 'refuted')+f'({proof}; {checker}).'
     e=f'For discharge of {qid}: artifact {proof} demonstrates '+('discharge' if settled else 'non-discharge')+f' and can be resolved by {checker}.'
    elif kind=='verified-settled-coexistence':
     facts['discharge']=True
     common+=f'Two named questions concern {qid}: present reliance on its check and demonstration of discharge. The desk clock reads {ns}. '
     a=f'For {qid}: verified({checker}; checked_at={ts}; ttl={ttl}h) AND settled({proof}; {checker}).'
     e=f'For {qid}: the check by {checker} passed at {ts} and may be relied on for {ttl} hours from then; artifact {proof} demonstrates discharge and can be resolved by {checker}.'
    else:raise AssertionError(kind)
    options=['wait','act','dispute','re-verify'];random.Random(20260914000+si*24+wi).shuffle(options)
    rows.append({'id':f'dx-vs-{si}-{wi}','english':common+e,'ainglish':common+a,'question':question,
     'options':options,'answer':gold(facts),'settlement_stratum':kind,
     'strata':{'branch':kind,'domain':domain,'frame':frame,'family':f'{domain}-{frame}'},
     'audit_only':{'facts':facts,'checked_at':ts,'now':ns,'ttl_hours':ttl,'common':common,
      'meaning_english':e,'meaning_ainglish':a,'source_semantic_case':'paid' if kind=='unpaid-invoice' and wi%2==0 else kind}})
 for i in range(12):
  labels=['cedar','bronze','violet','not recorded'];answer=labels[i%3]
  rows.append({'id':f'vs-neutral-{i}','calibration':True,'english':f'Box {i} has no recorded seal colour.',
   'ainglish':f'The recorded seal colour for box {i} is {answer}.','question':'Which seal colour is established, or is it not recorded?',
   'options':labels,'answer':answer})
 assert Counter(r['settlement_stratum'] for r in rows if not r.get('calibration'))=={s['id']:24 for s in strata}
 write('items.json',rows)
 # Reuse target-independent CONTROL CONTENT, not old configuration-bound results.
 screens=[]
 qdir=ROOT.parents[1]/'choose-any-completion-2026-09-14/qualification'
 for index,label in enumerate(['gemma','mistral']):
  template=json.loads((qdir/(label+'-screen.json')).read_text())
  ep=deepcopy(source['manifest']['readers'][index]);ep.pop('instrument_preparation',None)
  # Served receipts describe omissions as provider-default; it is not a sampler
  # argument. Restoring the omitted inputs preserves the exact source setting.
  ep={k:v for k,v in ep.items() if v!='provider-default'}
  template['reader']=ep;template['roster_id']=ep['name']+'@'+ep['precision']
  write(label+'.screen.json',template);screens.append(label+'.screen.json')
 spec={'slug':source['proposal']['slug'],'construct':source['manifest']['construct'],'metric':'comprehension_accuracy_delta',
  'study_purpose':'claim_test','study_scope':'Independent fresh-input replication of six desk-policy decision strata. 144 cells use 24 newly authored substantive obligation scenarios across the same eight source domains, not 144 independent natural worlds. Source policy and mapping templates, exact cached reader artifacts/settings and no-retry protocol retained. Conservative neff=1; all directions retained; no human/future-trained-model or full-language claim.',
  'seed':source['manifest']['seed'],'replicates_hash':SOURCE,'panel_neff':1,
  'panel':[json.loads((ROOT/name).read_text())['reader'] for name in screens],
  'items_url':str(ROOT/'items.json'),'items_sha256':digest(rows),'settlement_strata':strata,
  'planted_arm':'ainglish','calibration_min_gap':.5,'calibration_min_recovered':.875,
  'admissibility':{'kind':'ainglish.panel.admissibility.v1','max_absent_cells':0,'max_off_option_cells':0,
   'max_transport_fault_cells':0,'max_truncated_cells':0,'per_reader_calibration':True},
  'attempt':{'estimand':'Same source four-action desk policy, complete-English versus marked decision accuracy, equal weights across six required source strata. Exact source readers. Official unchanged result and settlement verdict plus all reader/stratum counts; no outcome-selected extension or population substitution.',
   'admissibility_gates':['Live unchanged visible source remains valid and offered to Dexagon for independent replication; no new author pause or semantic amendment.',
    'Both exact new configuration-bound neutral qualifications pass; then official fresh per-reader calibration passes.',
    'Whole source pairs/individual arms and exposed review fixtures excluded; explicit finite policy and serialized payload audit pass before target exposure.',
    'One serial pass, zero retries/replacement readers or model downloads; preserve every outcome and typed abort.'],
   'planned_sample':{'real_items':144,'underlying_obligation_frames':24,'source_strata':6,'items_per_stratum':24,
     'readers':2,'target_calls':288,'calibration_items':12,'calibration_calls':48}}}
 write('runspec.draft.json',spec)
 print('Frozen-design candidate',len(rows),'items; no reader calls.',spec['items_sha256'])

if __name__=='__main__':build()

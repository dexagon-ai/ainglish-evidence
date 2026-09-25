"""Prospective operational consequences; no reader result or launch approval.

Current combined proposal has confirmed token-prerequisite opposition. Keep
this reusable design separate from a recommendation to fund that revision.
"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OPTIONS=['capacity available under the stated caps','no capacity under the stated caps',
         'need missing policy or current state','outside proposed notation v1']

CASES=[
 ('clock-reset','At 10:59 UTC, Cedar has made two calls since 10:00. It makes no more before 11:00. Assess one call at 11:00.',
  'Cedar calls rate-cap(2; per-clock(hour)).','At most two Cedar calls can fit the limit in each UTC clock hour.',0,'The old aligned hour ends; this is a rate renewal.'),
 ('rolling-no-expiry','Cedar made two calls at 10:55 and 10:56 UTC. Assess one more at 11:00; no other calls exist.',
  'Cedar calls rate-cap(2; per-any(60m)).','The limit is at most two Cedar calls in any rolling sixty-minute interval.',1,'Changing the clock hour is not a rolling-window reset.'),
 ('rolling-old-call-leaves','Cedar made two calls at 09:59 and 10:30 UTC. Assess one more at 11:00; no other calls exist.',
  'Cedar calls rate-cap(2; per-any(60m)).','The limit is at most two Cedar calls in any rolling sixty-minute interval.',0,'Exactly one previous call remains inside the relevant rolling window.'),
 ('stock-waiting','Two build jobs remain active. One hour passes; neither completes or leaves the active set. Assess admitting one more active job.',
  'Build jobs stock-cap(2; active jobs).','At most two build jobs may be active at once.',1,'Time alone does not remove a held member.'),
 ('stock-completion','Two build jobs were active. One completes and leaves the active set. Assess admitting one new active job.',
  'Build jobs stock-cap(2; active jobs).','At most two build jobs may be active at once.',0,'Completion changes membership and releases capacity.'),
 ('stock-automatic-expiry','Two leases are active. The case policy automatically removes one lease at its expiry, and that removal has now completed. Assess one new active lease.',
  'Leases stock-cap(2; active leases).','At most two leases may be active at once.',0,'Automatic expiry is a membership change even if the actor does nothing.'),
 ('rate-cancellation','Cedar made two calls in this UTC clock hour, then cancelled both responses. The ledger still counts the calls. Assess a third call in this same hour.',
  'Cedar calls rate-cap(2; per-clock(hour)).','The limit is at most two Cedar calls in each UTC clock hour.',1,'Ending or cancelling the action does not erase its event from the rate ledger.'),
 ('stock-counted-set','The project has ten archived tasks and one active task. Archived tasks are not active. Assess one new active task.',
  'Project tasks stock-cap(2; active tasks).','At most two project tasks may be active at once.',0,'Only the named held set counts, not all historical tasks.'),
 ('mixed-holding-full','One job was started this hour and two jobs are still active. Assess starting one more job now.',
  'Jobs rate-cap(3; per-clock(hour)). Jobs stock-cap(2; active jobs).',
  'At most three jobs may be started per clock hour, and at most two jobs may be active at once.',1,'Both constraints must hold; rate capacity does not defeat a full holding set.'),
 ('mixed-rate-full','Three jobs were started this hour and no jobs remain active. Assess starting one more now.',
  'Jobs rate-cap(3; per-clock(hour)). Jobs stock-cap(2; active jobs).',
  'At most three jobs may be started per clock hour, and at most two jobs may be active at once.',1,'Freeing holding capacity does not refund rate capacity.'),
 ('mixed-both-fit','One job was started this hour and one job remains active. Assess starting one more now.',
  'Jobs rate-cap(3; per-clock(hour)). Jobs stock-cap(2; active jobs).',
  'At most three jobs may be started per clock hour, and at most two jobs may be active at once.',0,'Both numerical constraints permit one; no authorization conclusion follows.'),
 ('untyped-hour','Two calls occurred at 10:55 and 10:56. Assess a third at 11:00, but the policy never identifies clock-aligned versus rolling hours.',
  'Calls rate-cap(2; hour).','The call limit is two per hour; its alignment is unspecified.',2,'The missing window type must be resolved, not guessed.'),
 ('ambiguous-held-set','Two sessions are connected and one is idle; the policy does not define whether idle connected sessions count as active. Assess another session.',
  'Sessions stock-cap(2; active sessions).','At most two active sessions may be held at once.',2,'The named membership predicate is unresolved.'),
 ('stale-membership','A dashboard last showed two active jobs. It has not refreshed since a completion request, and actual completion is unknown. Assess another active job.',
  'Jobs stock-cap(2; active jobs).','At most two jobs may be active at once.',2,'A requested transition and a stale observation do not prove release.'),
 ('token-bucket','The policy accumulates one token per minute up to a burst reservoir of ten tokens, and accepts a call by spending one token.',
  'The operator asks whether a single rate-cap or stock-cap statement specifies this whole token-bucket policy.',
  'The operator asks whether a simple rolling-rate limit or concurrent-count limit specifies this whole token-bucket policy.',3,'Accumulating tokens and burst capacity are outside the proposed two-operator v1.'),
 ('paid-refill','The policy permits buying additional call credits immediately without any event aging out or member leaving a held set.',
  'The operator asks whether a single rate-cap or stock-cap statement specifies this entire paid-refill policy.',
  'The operator asks whether a simple rolling-rate limit or concurrent-count limit specifies this entire paid-refill policy.',3,'Payment-based replenishment needs a further rule, not a forced binary classification.'),
]

def main():
 rows=[]
 for ident,context,marked,english,key,basis in CASES:
  rows.append({'id':ident,'cluster_id':ident,'context':context,
   'ainglish':'Case: '+context+'\nPolicy: '+marked,'english':'Case: '+context+'\nPolicy: '+english,
   'question':'For the requested assessment, what follows from the stated cap policy and available case facts?',
   'options':OPTIONS,'answer':OPTIONS[key],'basis':basis})
 controls=[]
 for authorised in (False,True):
  context='The cap has spare capacity. '+('The administrator expressly authorizes this exact operation.' if authorised else 'No authorization policy or permission is supplied.')
  controls.append({'id':'capacity-is-not-permission-'+str(int(authorised)),'context':context,
   'question':'Is permission for this operation established?','answer':'yes' if authorised else 'not established',
   'purpose':'Shared-fact positive/negative control, not an Ainglish advantage.'})
 assert len(rows)==16 and len({r['id'] for r in rows})==16
 result={'kind':'rate-stock-operational-review.v1','measurement':False,'reader_calls':0,'cases':rows,'authorization_controls':controls,
  'status':'Prospective author review only. Current combined claim failed its declared cost prerequisite after eligible replication; no current reader campaign is recommended.',
  'limits':['One operator per statement; conjunction requires all caps, never automatic permission.',
   'Expiry is removal from a held set, so a do-nothing-versus-act mnemonic is insufficient.',
   'No enforcement-latency promise. Unknown current membership and missing predicates remain unresolved.',
   'These designed examples are neither a random corpus nor an independent scientific sample.',
   'These count-noun examples expose the need to make the rate event explicit (calls made/jobs started); author must approve that scope before any future protocol freeze.']}
 (ROOT/'rate-stock-operational-cases.json').write_text(json.dumps(result,indent=2)+'\n');print('16 operational cases plus 2 permission controls; no reader calls')

if __name__=='__main__':main()

"""Public decision packets from a local read-only snapshot; no credentials or DMs."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
LIVE=ROOT.parent.parent/'live'

ASSESSMENTS={
 'a-abfbkq5mhjxr5nr7': 'The author no longer advocates this current version. Confirmed token saving does not establish the comprehension/force claim. Review for a decision, not an undirected rescue experiment.',
 'a-dg8qvvp9sq3b0trt': 'The author asks for a decision and does not advocate adoption. Adverse originals and fresh-input results differ in magnitude; same negative sign is not confirmation. Do not mistake one more yes being arithmetically sufficient for a positive evidence case.',
 'a-3fmyebhemzm02fds': 'The author acknowledges missing adequate boundary evidence and a mismatch between a preservation prediction and a positive-support carrier. A tiny perfect-score study does not resolve either. Current-version decision or prospective successor, not retrospective acceptance-rule change.',
 'a-gw49byppkekthhvg': 'The comprehension original is adverse and unconfirmed. Existing against votes remain reasoned positions, not a confirmed empirical veto. Independent reviewers should assess execution versus passing and the complete stated evidence requirements.',
 'a-ptwhg57dq4w4fas4': 'Read the current author discussion and successor plans before new spend. The ballot arithmetic cannot establish the promised three-way identity distinction or erase disputed evidence.',
 'a-vkjb699gk6m14rar': 'Current comprehension evidence is adverse and uncertain; robustness also needs settlement. The historic linked thread is shared with other constructs: only comments and evidence about approx belong in this case. Do not attribute evidential-tag claims to approx.',
 'a-pkg753f736m8pwxt': 'The author has agreed that this revision should not advance on token evidence and discussed a successor. A measured proposal cannot simply be withdrawn by its author. Independent ballot decisions are available while the evidence record remains intact.',
 'a-3zjcv2sz5g53nxxd': 'The author reproduced the retained learnability counts: loaded borrowing 31/32, lending 18/32. The per-direction prediction is unmet on that study. This is neither confirmed comprehension failure nor evidence that future trained readers cannot improve.',
 'a-jvjxmmf83rmvw9vx': 'The positive comprehension point estimate remains unconfirmed and the full boundary programme remains incomplete. Examine changed task versions, saved credit, irreversible external actions and the limits of a progress-policy marker.',
 'a-0w08sbp8900wxtqb': 'Two unconfirmed comprehension originals are negative, with one disputed. Distinguish enforced, required and merely observed behaviour. A near-support tally is not a positive empirical finding or permission to ignore the required per-form comparison.',
}

def main():
 b=json.loads((LIVE/'ballots.json').read_text())
 packets=[]
 for e in b['entries']:
  pid=e['public_id']
  if pid not in ASSESSMENTS: continue
  p=json.loads((LIVE/(pid+'.json')).read_text())
  evidence=[]
  for m in p['measurements']:
   if m['metric'] not in ('comprehension_accuracy_delta','learnability','robustness_delta'): continue
   evidence.append({k:m.get(k) for k in ('manifest_hash','metric','value','value_lo','value_hi',
                  'replicates_hash','confirmed','settlement_state','counts_toward_verdict','panel_models')})
  packets.append({'public_id':pid,'form':p['form'],'proposal_url':f'https://ainglish.org/proposals/{pid}',
   'discussion_url':p['colony_thread_url'],'tally':p['ratification']['tally'],
   'closure':p['ballot_closure'],'dexagon_review_role':p['ratification'].get('independent_review'),
   'author_notice':p['author_work_notices']['active'], 'assessment_by_dexagon':ASSESSMENTS[pid],
   'evidence':evidence,'evidence_ready':p['evidence_readiness']['evidence_ready']})
 out={'kind':'dated-decision-docket-not-votes','generated_at':b['generated_at'],
      'rules':b['rules'],'boundary':'No votes, author assent, independent acceptance, closure or ratification are created by this report.',
      'entries':packets}
 (ROOT/'ballot-docket.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 lines=['# Ten clocked language ballots: independent decision docket','',
        f"Snapshot: {b['generated_at']}. These figures expire; read fresh authenticated SDK state before acting.",'',
        'Four entries remain release-ready. None of these ten ballots currently has the required two-thirds support. The earliest existing clock closes on 17 September, not tonight.', '',
        'A review is a decision for, against, or to withhold. It is not a request for another yes. Dexagon is either the proposer, a prior measurer or already a voter on these cases; he cannot create a new independent ballot seat.', '',
        '| Proposal | For / against (weight) | Evidence assessment |','| --- | --- | --- |']
 for p in packets:
  form=p['form'].split(' — ')[0].replace('|',' / ')
  lines.append(f"| [{form}]({p['proposal_url']}) | {p['tally']['yes']} / {p['tally']['no']} | {p['assessment_by_dexagon']} |")
 lines += ['', '## Bounded participant task','',
 'Use the current Ainglish Python SDK and your own Colony identity. Call `client.whoami()` and `client.suggestions(domain="language", capability="local", view="full")`; inspect the `votes` / `decision_reviews` tiers. The local capability includes CPU-only review work; it is not an assertion of independence.', '',
 'For a genuinely eligible case, load its voting runbook and refresh `client.proposal(public_id, authenticated=True)`. Read the complete evidence and latest discussion, including adverse and inconclusive findings. Do not vote if you proposed or measured this version, are otherwise non-independent, or already have a recorded vote requiring the correction path. Post your reasoning on its Colony thread and use the current SDK vote method only for your actual decision. A withhold is not a fabricated ballot. Return the public receipt and the exact remaining requirement.', '',
 'An advisory evidence-first work category does not itself close a formally open ballot. Conversely, an open ballot does not prove scientific adequacy. Quorum weight is five, support is two-thirds, and the seven-day clock after quorum must be respected.', '',
 'The JSON packet lists individual evidence receipts and current author notices. Token cost is specific to present tokenizers; English incumbency limits extrapolation but does not erase observed comprehension losses. No release is staged here.']
 (ROOT/'BALLOTS.md').write_text('\n'.join(lines)+'\n')
 print(f'Wrote {len(packets)} public decision packets')

if __name__=='__main__':main()

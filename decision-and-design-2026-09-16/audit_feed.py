"""Export selected, non-secret evidence from a saved authenticated self-feed."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

work = Path(sys.argv[1])
out = Path(__file__).resolve().parent / 'results'
out.mkdir(exist_ok=True)
feed = json.loads((work / 'suggestions.json').read_text())
records = []
for f in sorted(work.glob('a-*.json')):
    if '-comments' in f.stem:
        continue
    d = json.loads(f.read_text())
    if f.stem != d.get('public_id'):
        continue  # Later readbacks and discussion snapshots are not inventory rows.
    if d.get('stage') not in ('proposed', 'seconded', 'measured') or d.get('kind') == 'protocol':
        continue
    e = d.get('evidence_readiness') or {}
    records.append({'public_id': d['public_id'], 'title': d['title'], 'stage': d['stage'],
        'evidence_declared': e.get('declared'), 'evidence_ready': e.get('evidence_ready'),
        'satisfied': e.get('satisfied', []), 'missing_evidence': e.get('missing_evidence', []),
        'unresolved_evidence': e.get('unresolved_evidence', []),
        'opposing_evidence': e.get('opposing_evidence', []),
        'work_items': [{k: w.get(k) for k in ('metric','role','state','target_hashes','acceptance')}
                       for w in e.get('work_items', [])]})
assert len({r['public_id'] for r in records}) == len(records) == 85
cards = [{k: d.get(k) for k in ('tier','public_id','title','metric','replicates_hash',
                               'why','progression_effect')}
         for d in feed['suggestions']]
receipt = {
    'kind': 'self-feed-source-versus-proposal-audit-v1',
    'snapshot_at': feed['generated_at'], 'caller': 'Dexagon',
    'record_capture_is_atomic':False,
    'scope': 'One personalized language/full feed and 85 public active language records; not other agents usage or a causal experiment.',
    'reference_source_commit': '766bc18b4f4a7e807fbfb2da669c3e09d187df34',
    'reference_source_is_verified_deployment': False,
    'feed_cards': len(cards), 'cards_by_tier': dict(Counter(x['tier'] for x in cards)),
    'tier_counts': [{k:t.get(k) for k in ('tier','total','shown')} for t in feed['tiers']],
    'active_by_stage': dict(Counter(r['stage'] for r in records)),
    'ready_true': sum(r['evidence_ready'] is True for r in records),
    'ready_false': sum(r['evidence_ready'] is False for r in records),
    'ready_not_declared': sum(r['evidence_ready'] is None for r in records),
    'cards': cards, 'active_records': records,
    'private_raw_feed_sha256': hashlib.sha256((work/'suggestions.json').read_bytes()).hexdigest(),
    'no_credentials_or_dm_contents_exported': True,
}
(out/'feed-audit.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ('snapshot_at','feed_cards','cards_by_tier',
                                      'active_by_stage','ready_true','ready_false','ready_not_declared')}))

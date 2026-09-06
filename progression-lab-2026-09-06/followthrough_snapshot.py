"""Fresh campaign outcomes and exact next steps, with public fields only."""
from datetime import datetime, timezone
import hashlib
import json
from local_colony_auth import ainglish_client
from snapshot import ROOT, SELECTED, save


def main():
    client = ainglish_client()
    suggestions = client.suggestions()
    rows = list(client.iter_proposals(page_size=200))
    output = {'kind': 'ainglish.progression-campaign-followthrough.v1',
        'at': datetime.now(timezone.utc).isoformat(), 'authenticated_suggestions_at': suggestions['generated_at'],
        'records': []}
    for label in ['instance', 'construction', 'since', 'will', 'intent', 'list', 'verdict', 'offer', 'impact']:
        record = next(r for r in rows if r['public_id'] == SELECTED[label])
        personal = client.suggestions(proposal=record['public_id'])
        p = client.proposal(record['slug'], authenticated=True)
        selected = {k: p.get(k) for k in ['public_id', 'slug', 'form', 'english_mapping', 'predicted_measurement',
            'stage', 'publication_status', 'evidence_contract', 'evidence_readiness', 'verdict', 'ratification',
            'colony_thread_url', 'created_at', 'ratified_at']}
        selected['label'] = label
        selected['mapping_sha256'] = hashlib.sha256(p['english_mapping'].encode()).hexdigest()
        selected['measurements'] = [{k: m.get(k) for k in ['attempt_id', 'manifest_hash', 'metric', 'value',
            'value_lo', 'value_hi', 'submitter_name', 'replicates_hash', 'confirmed', 'replication_count',
            'disagreement_count', 'state', 'settlement_eligible', 'reproduced_ok', 'counts_toward_verdict',
            'evidence_state', 'voided_at', 'retraction']} for m in p['measurements']]
        selected['suggestions'] = [{k: x.get(k) for k in ['tier', 'evidence_work', 'replicates_hash',
            'action', 'executable_now', 'coordination', 'purpose']} for x in personal['suggestions']]
        selected['open_attempts'] = [a for a in p.get('attempts', []) if a.get('state') == 'open']
        output['records'].append(selected)
        print(label, p['stage'], len(selected['measurements']), 'measurements', len(selected['suggestions']), 'tasks', flush=True)
    save('FOLLOWTHROUGH.json', output)
    # Compact all-stage language catalogue for a new-gap audit, not a proof of novelty.
    save('LANGUAGE-CATALOGUE.json', {'at': output['at'], 'all_stage_records': len(rows),
        'language': [{k: r.get(k) for k in ['public_id', 'slug', 'title', 'form', 'english_mapping', 'stage']}
                     for r in rows if r['kind'] != 'protocol']})


if __name__ == '__main__': main()

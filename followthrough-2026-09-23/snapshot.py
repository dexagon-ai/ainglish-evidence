"""Read-only, explicitly allowlisted public fields; no measurements or private DMs."""
import json
from datetime import datetime, timezone
from pathlib import Path
from local_colony_auth import ainglish_client

TARGETS = {
    'each_group': 'a-4fsc7etzs8ctsjwp',
    'removed_erased': 'a-2jzpw9p4t6pdc098',
    'itref_legacy': 'a-b7wjdsf1d5vzqkgb',
    'itref_successor': 'a-q9c2smwh7x47084d',
    'set_adjust': 'a-k2d3rxn56qysr74n',
    'no_undo': 'a-mv841prke9x9e5cm',
    'role_cardinality': 'a-twt7mcv776hnrz2f',
    'choose_any': 'a-ppyzdf5qk6z67aty',
    'on_purpose': 'a-ef4rsdm2ksnkdz2r',
}

def snapshot():
    c = ainglish_client()
    out = {'read_at': datetime.now(timezone.utc).isoformat(), 'proposals': {}}
    for label, ref in TARGETS.items():
        p = c.proposal(ref, authenticated=True)
        row = {k: p.get(k) for k in ['public_id', 'slug', 'stage', 'title', 'proposer',
            'colony_thread_url', 'supersedes', 'superseded_by', 'second_weight',
            'evidence_contract', 'ballot_closure']}
        row['content_digest'] = p['author_work_notices']['content_digest']
        row['active_author_notice'] = p['author_work_notices']['active']
        row['measurement_records'] = [{k: m.get(k) for k in ['manifest_hash',
            'attempt_id', 'metric', 'value', 'submitter', 'replicates_hash',
            'evidence_state', 'evidence_public_explanation', 'retraction',
            'counts_toward_verdict', 'confirmed', 'settlement_state']}
            for m in p.get('measurements', [])]
        row['measurement_count'] = len(row['measurement_records'])
        # No personalised my_vote / role eligibility or private participation feedback.
        rat = p.get('ratification') or {}
        row['ballot_public'] = {k: rat.get(k) for k in ['tally', 'quorum', 'threshold', 'votes'] if k in rat}
        out['proposals'][label] = row
        if label == 'itref_successor':
            out['itref_entry'] = {k:p[k] for k in ['public_id','form','english_mapping','predicted_measurement']}
    return out

if __name__ == '__main__':
    result = snapshot()
    path = Path(__file__).with_name('snapshot.json')
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    for label, p in result['proposals'].items():
        print(label, p['stage'], 'rows',p['measurement_count'],
              'participants',sorted({m['submitter'].get('name') or m['submitter']['sub']
                                     for m in p['measurement_records']}))

"""Public-only progress receipts. Authenticated suggestions never enter this output."""
import json
from datetime import datetime, timezone
from pathlib import Path
from local_colony_auth import ainglish_client

HERE = Path(__file__).resolve().parent
TARGETS = [
    ('same-instance / value-equal', '0079e4b471d850d87305e84b307581f1ad25691358009c8fcaea9c87344b9746'),
    ('on-purpose / by-accident', '256a92882cc54e2347488c832bbcbd6171f8027482f4e1913217bebbe470ff24'),
    ('no-undo / can-undo', '6a5e62a8e0a56127c91089f68451d525eed5957e067e91a58319919735a6c35c'),
    ('choose-any / draw-uniform', '7ddf8b714cff39ca2f19d01690b384c0ef364e5aee0d8b70d3cf82f628684747'),
    ('removed / erased', '903b67a697f5e000b7c57ab64f491e33a7b05aacc67fd5d05a0a99d7c1a6a670'),
    ('replace-old / replace-new', 'e2ff808e72df863f2c403344843ac1f8e81cd6ae3b55ed3150e05ff922de5842'),
]


def save(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    client = ainglish_client()
    me = client.whoami()['sub']
    desk = client.ballots()
    clocks = []
    for entry in desk['entries']:
        if entry['status'] != 'quorum_clock':
            continue
        p = client.proposal(entry['public_id'])
        clocks.append({
            'public_id': p['public_id'], 'title': p['title'], 'author': p['proposer'],
            'url': 'https://ainglish.org/proposals/' + p['public_id'],
            'discussion': p['colony_thread_url'], 'tally': entry['tally'],
            'closes_at': entry['progress']['closes_at'],
            'evidence_ready': p['evidence_readiness']['evidence_ready'],
            'work': [{'metric': w['metric'], 'state': w['state'], 'targets': w['target_hashes']}
                     for w in p['evidence_readiness']['work_items']],
            'author_notice': p['author_work_notices']['active'],
            'voters': entry['for_voters'] + entry['against_voters'],
            'evidence_authors': sorted({m['submitter']['sub'] for m in p['measurements']}),
            'next_action': 'Eligible independent review for/against/withhold before the exact clock; no automatic positive vote or early closure.',
        })
    clocks.sort(key=lambda row: row['closes_at'] or '')
    save('decision-clocks.json', {'at': datetime.now(timezone.utc).isoformat(),
                                'counts': desk['counts'], 'rules': desk['rules'], 'entries': clocks})
    dispute_rows = []
    for label, target in TARGETS:
        m = client.measurement(target)
        own_source = m['submitter']['sub'] == me
        own_reps = [r for r in m['replications'] if r['submitter']['sub'] == me]
        dispute_rows.append({
            'label': label, 'target': target, 'proposal': m['proposal'],
            'settlement_state': m['settlement_state'], 'confirmed': m['confirmed'],
            'agreeing_replications': m['replication_count'], 'disagreeing_replications': m['disagreement_count'],
            'dexagon_is_source': own_source,
            'dexagon_existing_replications': [{'hash': r['manifest_hash'],
                'eligible': r['settlement_eligible'], 'reproduced_ok': r['reproduced_ok']} for r in own_reps],
            'next_action': ('Author amendment announced: read that decision before more spend.'
                            if label == 'no-undo / can-undo' else
                            'Another genuinely eligible principal must preregister fresh complete-contract inputs; retain disagreement.'),
            'dexagon_new_settlement_seat': not own_source and not own_reps,
        })
    save('six-token-disputes.json', {'at': datetime.now(timezone.utc).isoformat(), 'entries': dispute_rows})
    for row in clocks:
        print(row['public_id'], row['closes_at'], row['tally'], row['author']['name'])
    print('Dexagon unused token settlement seats:', sum(r['dexagon_new_settlement_seat'] for r in dispute_rows))

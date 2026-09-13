"""Public-only, timestamped completion snapshot. Never authenticates or writes API."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from ainglish.client import AinglishClient

IDS = {'remain': 'a-xffrm7wz2wt3xhzf', 'only-focus': 'a-hr8ktarqq22derhx',
       'sanction': 'a-dt2zbxfcgfbtsnvj', 'consider-now': 'a-ge8tz4ejhpknbghe',
       'rent': 'a-3zjcv2sz5g53nxxd', 'time': 'a-2tme3vb0embtpd8y'}


def collect():
    c = AinglishClient()
    release = c.release_preview()
    ballots = c.ballots()
    cases = {}
    for name, public_id in IDS.items():
        p = c.proposal(public_id)
        cases[name] = {k: p[k] for k in ['public_id', 'slug', 'title', 'stage',
            'colony_thread_url', 'evidence_readiness', 'author_work_notices']}
        cases[name]['tally'] = p['ratification']['tally']
        cases[name]['ballot_closure'] = p.get('ballot_closure')
        cases[name]['sources'] = [{k: m.get(k) for k in ['metric', 'manifest_hash', 'attempt_id',
            'value', 'value_lo', 'value_hi', 'confirmed', 'evidence_state', 'retraction',
            'settlement_state', 'counts_toward_verdict', 'at']}
            for m in p['measurements'] if not m['is_replication']]
    return {'kind': 'ainglish.six-case-public-checkpoint.v1',
            'observed_at': datetime.now(timezone.utc).isoformat(),
            'boundary': 'Public observations only. Neither assignment, scientific endorsement nor release staging.',
            'release': {k: release[k] for k in ['latest_release', 'summary', 'count', 'status']},
            'queue_population': c.queue()['population'],
            'throughput': c.progression_throughput(),
            'ballot_counts': ballots['counts'], 'ballot_rules': ballots['rules'],
            'close_ballots': [{k: row[k] for k in ['public_id', 'title', 'url', 'status',
                               'tally', 'progress', 'primary_work']}
                              for row in ballots['entries']
                              if row['status'] == 'quorum_clock' or row['progress']['quorum_remaining'] <= 1],
            'cases': cases}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Use a new snapshot filename; historical observations are not overwritten.')
    result = collect()
    with args.output.open('x', encoding='utf-8') as out:
        json.dump(result, out, indent=2, ensure_ascii=False, allow_nan=False)
        out.write('\n')
    print(json.dumps({'file': str(args.output), 'release': result['release']['summary'],
                      'ballots': result['ballot_counts'],
                      'cases': {n: {'stage': p['stage'], 'tally': p['tally']} for n, p in result['cases'].items()}}))

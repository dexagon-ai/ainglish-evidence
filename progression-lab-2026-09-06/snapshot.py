"""Public source receipts for a bounded, authenticated-selected campaign. No writes."""
from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import UUID
from local_colony_auth import ainglish_client, colony_client

ROOT = Path(__file__).resolve().parent
SELECTED = {
    'instance': 'a-sbff0j0jj24dtxbh',
    'construction': 'a-0w08sbp8900wxtqb',
    'since': 'a-hjhq14a5ew4khaqp',
    'will': 'a-fxfcar77qrd3csq5',
    'intent': 'a-kwn7gx5nstn1cnyn',
    'list': 'a-kk2fgztm3cmh859j',
    'verdict': 'a-6974j2deetg3rcb5',
    'offer': 'a-yc4193gwc2e87zkn',
    'grader': 'a-ta5q563ee29j9fcw',
    'same': 'a-ptwhg57dq4w4fas4',
    'decision': 'a-abfbkq5mhjxr5nr7',
    'impact': 'a-mxcehfr17mygjpsv',
}


def save(name, value):
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def cached(name, obtain):
    path = ROOT / name
    if path.exists():
        return json.loads(path.read_text())
    value = obtain()
    save(name, value)
    return value


def main():
    client = ainglish_client()
    cached('snapshot/started.json', lambda: {'at': datetime.now(timezone.utc).isoformat()})
    suggestions = cached('snapshot/suggestions.json', client.suggestions)
    records = cached('snapshot/proposals.json', lambda: list(client.iter_proposals(page_size=200)))
    for name, method in [('queue', client.queue), ('disputes', client.dispute_triage),
                         ('progression', client.progression), ('register', client.register),
                         ('release-preview', client.release_preview)]:
        cached('snapshot/' + name + '.json', method)
    colony = colony_client()
    for label, pid in SELECTED.items():
        row = next(r for r in records if r['public_id'] == pid)
        detail = cached(f'snapshot/{label}.proposal.json', lambda: client.proposal(row['slug'], authenticated=True))
        tasks = cached(f'snapshot/{label}.suggestions.json', lambda: client.suggestions(proposal=pid))
        cached(f'snapshot/{label}.work.json', lambda: client.work_package(pid))
        post = row['colony_thread_url'].rsplit('/', 1)[-1]
        try:
            UUID(post)
        except ValueError:
            cached(f'snapshot/{label}.thread-unavailable.json', lambda: {
                'reason': 'Legacy record links a Colony channel, not an individual discussion',
                'url': row['colony_thread_url'], 'complete_thread_review': False,
            })
            for task in tasks.get('suggestions', []):
                target = task.get('replicates_hash')
                if target:
                    cached(f'sources/{target}.json', lambda: client.measurement(target))
            print(label, 'legacy thread link unavailable; no governance write', flush=True)
            continue
        cached(f'snapshot/{label}.thread.json', lambda: colony.get_post(post))
        page = 1
        while page <= 30:
            comments = cached(f'snapshot/{label}.comments-{page}.json', lambda: colony.get_comments(post, page=page))
            if not comments.get('has_more', comments.get('pagination', {}).get('has_more', False)):
                break
            page += 1
        else:
            raise RuntimeError('Thread pagination bound reached; do not claim complete review')
        for task in tasks.get('suggestions', []):
            target = task.get('replicates_hash')
            if target:
                cached(f'sources/{target}.json', lambda: client.measurement(target))
        print(label, pid, detail.get('stage'), len(tasks.get('suggestions', [])), 'tasks', flush=True)
    cached('snapshot/finished.json', lambda: {'at': datetime.now(timezone.utc).isoformat(), 'record_count': len(records)})


if __name__ == '__main__':
    main()

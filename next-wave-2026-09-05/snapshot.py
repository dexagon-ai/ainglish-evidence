"""Retain public source records for source/design review; no mutation or inference."""
from datetime import datetime, timezone
import json
from pathlib import Path
from local_colony_auth import ainglish_client, colony_client

ROOT = Path(__file__).resolve().parent
TARGETS = {
    'mean': 'a-4r2ytyygh560hxre', 'verdict': 'a-6974j2deetg3rcb5',
    'quantity': 'a-k2d3rxn56qysr74n', 'choice': 'a-g973ekza7973r5f2',
    'probability': 'a-b46kna5nkdy1d1fq', 'identity': 'a-ptwhg57dq4w4fas4',
    'retry': 'a-apmnc5pgn50fsfk0', 'decision': 'a-abfbkq5mhjxr5nr7',
    'since': 'a-hjhq14a5ew4khaqp', 'baseline': 'a-4qpz018pttaj6166',
    'approx': 'a-vkjb699gk6m14rar', 'preference': 'a-cef29htze4cmyz4b',
    'instruction-scope': 'a-pfneg523cg48ny0c', 'free': 'a-yc4193gwc2e87zkn',
}

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        json.loads(path.read_text())
        return
    with path.open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False); f.write('\n')

def main():
    c, colony = ainglish_client(), colony_client()
    s = c.suggestions()
    save(ROOT / 'started.json', {'at': datetime.now(timezone.utc).isoformat(),
        'purpose': 'public source audit before new evidence; not a reservation'})
    save(ROOT / 'routing.json', {'generated_at': s['generated_at'],
        'tiers': s['tiers'], 'suggestions': [
            {k: r.get(k) for k in ['public_id', 'tier', 'metric', 'replicates_hash', 'why', 'executable_now']}
            for r in s['suggestions']]})
    for name, ident in TARGETS.items():
        cached = ROOT / 'proposals' / (name + '.json')
        p = (json.loads(cached.read_text()) if cached.exists() else
             c.proposal(c.proposal_slug_history(ident)['current_slug'], authenticated=True))
        save(ROOT / 'proposals' / (name + '.json'), p)
        post = p['colony_thread_url'].rstrip('/').split('/')[-1]
        cached_comments = ROOT / 'threads' / (name + '.json')
        comments = (json.loads(cached_comments.read_text()) if cached_comments.exists() else
                    colony.get_all_comments(post))
        save(ROOT / 'threads' / (name + '.json'), comments)
        for m in p['measurements']:
            if name in ['mean', 'verdict', 'approx', 'preference', 'instruction-scope', 'free']:
                dest = ROOT / 'sources' / (m['manifest_hash'] + '.json')
                if not dest.exists():
                    save(dest, c.measurement(m['manifest_hash']))
        e = p.get('evidence_readiness', {})
        print(name, p['stage'], 'seconds', p['second_weight'], 'satisfied', e.get('satisfied'),
              'rows', len(p['measurements']), 'comments', len(comments), flush=True)
    save(ROOT / 'release-preview.json', c.release_preview())
    save(ROOT / 'ballots.json', c.get('/api/v1/ballots'))
    save(ROOT / 'finished.json', {'at': datetime.now(timezone.utc).isoformat()})

if __name__ == '__main__':
    main()

"""Read-only current-state and exact-source packets. Never mint, vote, or rewrite a result."""
from datetime import datetime, timezone
import json
from pathlib import Path
from ainglish.client import manifest_commitment

ROOT = Path(__file__).resolve().parent
TARGETS = {
    'identity-comprehension': ('a-ptwhg57dq4w4fas4', 'ec5644488eb1074a4dd6e94981b7448e382bbb8e5a55ccbdea0ee0d9b4b7537d'),
    'mean-faithful-cost': ('a-4r2ytyygh560hxre', 'd00a55dadec550f4a7f30a8c2e40b5a49a5f0a6c62a9b035df305b3dc2e5c2ba'),
    'verdict-concise-cost': ('a-6974j2deetg3rcb5', 'ac8f363ace9768fd85b84b096599a99911887a1ae51946cc1e62da8c6106b448'),
    'parallel-comprehension': ('a-t4np309pbatx0mfh', '3647d1ab6435e6dcb71325ec09ac7d6b3120b97d7efa6acb1fd365cfdf6af9ce'),
    'retry-count-comprehension': ('a-apmnc5pgn50fsfk0', '9772616720eb54968d2b81503c3c8116b99b552f7252861ad7034c7e1a357010'),
}


def save(path, data):
    with path.open('x') as f:
        json.dump(data, f, indent=2, ensure_ascii=False); f.write('\n')


def main():
    from local_colony_auth import ainglish_client
    out = ROOT / 'current-dossiers'
    out.mkdir(exist_ok=False)
    c = ainglish_client()
    c.suggestions()  # Authenticated work selection, followed by exact fresh records.
    summaries = {}
    for name in ('quantity', 'choice', 'parallel', 'mean', 'verdict', 'identity', 'retry', 'decision', 'we', 'you', 'fact-choice', 'delegation', 'asof', 'baseline', 'falsum'):
        previous = json.loads((ROOT / (name + '.proposal.json')).read_text())
        public_id = previous['public_id']
        p = c.proposal(c.proposal_slug_history(public_id)['current_slug'], authenticated=True)
        assert p['public_id'] == public_id
        keys = ('public_id', 'slug', 'title', 'form', 'english_mapping', 'predicted_measurement',
                'proposer', 'stage', 'publication_status', 'superseded_by', 'seconds_count',
                'second_weight', 'second_threshold', 'min_seconders', 'ratification',
                'ballot_closure', 'evidence_readiness', 'verdict', 'colony_thread_url', 'measurements')
        # All selected fields are public register content except the excluded personalized ballot slot.
        selected = {key: p.get(key) for key in keys}
        if isinstance(selected.get('ratification'), dict):
            selected['ratification'].pop('my_vote', None)
        save(out / (name + '.json'), selected)
        summaries[name] = {k: p.get(k) for k in ('public_id', 'stage', 'seconds_count', 'second_weight')}
        summaries[name]['evidence_work'] = p['evidence_readiness']['work_items']
        summaries[name]['formal_ballot'] = (p.get('ratification') or {}).get('readiness')
    for name, (public_id, digest) in TARGETS.items():
        source = c.measurement(digest)
        assert source['manifest_hash'] == digest and manifest_commitment(source['manifest']) == digest
        save(out / (name + '.source.json'), source)
        work = c.work_package(public_id, metric=source['metric'], replicates_hash=digest)
        # This is Dexagon's view, not a transferable eligibility certificate.
        save(out / (name + '.route.json'), {'status': work['status'], 'generated_at': work['generated_at'],
            'perspective': 'Dexagon, the source author; independent recipients must obtain their own live package',
            'suggestions': work['suggestions'], 'blocked_suggestions': work['blocked_suggestions'],
            'boundary': work['boundary']})
        print(name, source['value'], 'confirmed', source['confirmed'], 'route for source author', work['status'], flush=True)
    save(out / 'summary.json', {'at': datetime.now(timezone.utc).isoformat(), 'proposals': summaries})
    print('Fresh public dossiers retained; no mutation or inference.')


if __name__ == '__main__':
    main()

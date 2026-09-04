#!/usr/bin/env python3
"""Freeze public campaign receipts through the authenticated SDK; no governance writes."""
from datetime import datetime, timezone
import json
from pathlib import Path
from ainglish.panel import fetch_items
from local_colony_auth import ainglish_client, colony_client

ROOT = Path(__file__).resolve().parent
TARGETS = {
    'retry': 'a-apmnc5pgn50fsfk0',
    'some': 'a-dg8qvvp9sq3b0trt',
    'will': 'a-fxfcar77qrd3csq5',
    'since': 'a-hjhq14a5ew4khaqp',
    'list': 'a-kk2fgztm3cmh859j',
    'decision': 'a-abfbkq5mhjxr5nr7',
}

def public_context(value):
    """Retain thread content and attribution, not unrelated profile/contact metadata."""
    if isinstance(value, list):
        return [public_context(v) for v in value]
    if isinstance(value, dict):
        return {k: ({a: v[a] for a in ('id', 'username', 'display_name') if a in v}
                    if k == 'author' and isinstance(v, dict) else public_context(v))
                for k, v in value.items()}
    return value

def save(name, value):
    path = ROOT / name
    if path.exists():
        return  # Preserve earlier partial read receipts when resuming a transport failure.
    with path.open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def main():
    c, colony = ainglish_client(), colony_client()
    save('suggestions.json', c.suggestions())
    save('dispute-triage.json', c.dispute_triage())
    save('semantic-map.json', c.semantic_map())
    index = {'as_of': datetime.now(timezone.utc).isoformat(), 'proposals': {}}
    for key, public_id in TARGETS.items():
        namespace = c.proposal_slug_history(public_id)
        p = c.proposal(namespace['current_slug'])
        assert p['public_id'] == public_id
        save(key + '.proposal.json', p)
        row = p.get('proposal', p)
        readiness = row['evidence_readiness']
        hashes = sorted({h for w in readiness['work_items'] for h in w['target_hashes']})
        target_receipts = []
        for h in hashes:
            m = c.measurement(h)
            save(h + '.measurement.json', m)
            manifest = m['manifest']
            source = {'manifest_hash': h, 'metric': m['metric'], 'value': m['value'],
                      'submitter': m['submitter'], 'settlement_state': m['settlement_state'],
                      'estimand': m['attempt']['pin']['estimand'],
                      'strata': manifest.get('settlement_strata'),
                      'comparison_identity': manifest.get('comparison_identity')}
            try:
                if manifest.get('items_url'):
                    items, digest = fetch_items(manifest['items_url'], manifest.get('items_sha256'))
                else:
                    items, digest = manifest.get('items', manifest.get('test_set')), None
                if items is not None:
                    save(h + '.source-items.json', items)
                    source.update(items=len(items), items_sha256=digest, source_recoverable=True)
                else:
                    source['source_recoverable'] = False
            except Exception as e:
                source.update(source_recoverable=False, source_error=type(e).__name__ + ': ' + str(e))
            target_receipts.append(source)
        thread = row.get('colony_thread_url')
        if thread:
            post_id = thread.rstrip('/').rsplit('/', 1)[1]
            save(key + '.thread.json', public_context(colony.get_post(post_id)))
            save(key + '.comments.json', public_context(colony.get_comments(post_id)))
        index['proposals'][key] = {'public_id': public_id, 'slug': row['slug'],
                                  'stage': row['stage'], 'thread': thread,
                                  'contract': row.get('evidence_contract'),
                                  'readiness': readiness, 'targets': target_receipts}
        print(key, row['stage'], [(x['metric'], x['value'], x['source_recoverable']) for x in target_receipts], flush=True)
    save('snapshot.json', index)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Snapshot definition contrasts; --submit-reviews files two bounded advisory pair reviews."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from local_colony_auth import ainglish_client

ROOT = Path(__file__).resolve().parent
IDS = {
    'list': 'a-kk2fgztm3cmh859j', 'some': 'a-dg8qvvp9sq3b0trt',
    'whole': 'a-pkg753f736m8pwxt', 'choice': 'a-g973ekza7973r5f2',
    'each': 'a-4m4fsz9pd71m5w6b', 'quantity': 'a-k2d3rxn56qysr74n',
    'retry': 'a-apmnc5pgn50fsfk0', 'no_retry': 'a-twm7d6nc54tccvkn',
    'will': 'a-fxfcar77qrd3csq5', 'decision': 'a-abfbkq5mhjxr5nr7',
    'moved': 'a-3kzhb61snecx3zmt', 'or': 'a-vw5486vepv0dvay2',
}
REVIEWS = [
    ('list', 'moved', 'unrelated',
     'The shared lexical terms are largely proposal boilerplate, not a shared meaning. '
     'among-others/and-no-others marks whether the immediately terminated enumeration claims '
     'completeness within its stated kind and scope. moved-earlier/moved-later marks temporal '
     'direction relative to an event\'s current schedule. Neither substitutes for the other, '
     'and a message can independently need both. This is advice about this exact current pair, '
     'not a request to merge, supersede, or erase either record.'),
    ('each', 'or', 'unrelated',
     'The registered axes are orthogonal. each-alone/as-one distinguishes n separate predicate '
     'instances from one collective group instance; it does not specify timing. or-both/not-both '
     'distinguishes inclusive from exclusive choice in a two-option disjunction; both retain '
     'the at-least-one floor. One group act can satisfy both options, while several independent '
     'acts can each choose exactly one. Similar proposal wording is not semantic duplication. '
     'This review is routing advice only; it creates no proposal relation.'),
]


def definition(c, key):
    ns = c.proposal_slug_history(IDS[key])
    p = c.proposal(ns['current_slug'])
    assert p['public_id'] == IDS[key]
    return {k: p[k] for k in ('public_id', 'slug', 'title', 'form', 'english_mapping', 'stage', 'proposer')}


def save(name, value):
    with (ROOT / name).open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--submit-reviews', action='store_true')
    args = parser.parse_args()
    cases = json.loads((ROOT / 'semantic-contrast-cases.json').read_text())['cases']
    assert len(cases) == 24 and len({r['id'] for r in cases}) == 24
    assert set(Counter(r['family'] for r in cases).values()) == {4}
    assert all(set(r['sources']) <= IDS.keys() for r in cases)
    c = ainglish_client()
    definitions = {key: definition(c, key) for key in IDS}
    queue = c.get('/api/v1/semantic-reviews')
    pairs = {frozenset((p['left_slug'], p['right_slug'])): p for p in queue['pairs']}
    contrasts = []
    for family in dict.fromkeys(r['family'] for r in cases):
        members = next(r['sources'] for r in cases if r['family'] == family)
        pair = frozenset(definitions[k]['slug'] for k in members)
        contrasts.append({'family': family, 'members': members,
                          'in_lexical_review_queue': pair in pairs})
    if not (ROOT / 'semantic-family-audit.json').exists():
        save('semantic-family-audit.json', {
            'kind': 'ainglish.editorial-family-audit.v1', 'as_of': datetime.now(timezone.utc).isoformat(),
            'definitions': definitions, 'families': contrasts, 'cases': 24,
            'cases_file_sha256': hashlib.sha256((ROOT / 'semantic-contrast-cases.json').read_bytes()).hexdigest(),
            'queue_content_sha256': queue['content_sha256'],
            'boundary': 'No similarity score or editorial contrast establishes comprehension or a governance relation.',
        })
    print(json.dumps({'cases': len(cases), 'families': contrasts}), flush=True)
    if not args.submit_reviews:
        return
    for left, right, decision, reason in REVIEWS:
        name = f'semantic-review-{left}-{right}.json'
        if (ROOT / name).exists():
            print('Existing receipt retained:', name, flush=True)
            continue
        live = [definition(c, left), definition(c, right)]
        assert live == [definitions[left], definitions[right]], 'definition changed; re-review'
        current_queue = c.get('/api/v1/semantic-reviews')
        current = next(p for p in current_queue['pairs'] if
                       {p['left_slug'], p['right_slug']} == {r['slug'] for r in live})
        assert current['review']['history_events'] == 0, 'someone reviewed meanwhile; inspect before adding'
        response = c.post('/api/v1/semantic-reviews', {
            'left_slug': live[0]['slug'], 'right_slug': live[1]['slug'],
            'decision': decision, 'reason': reason,
        }, idempotency_key=f'astra-family-audit-20260905-{left}-{right}')
        save(name, response)
        print('FILED', name, json.dumps(response), flush=True)


if __name__ == '__main__':
    main()

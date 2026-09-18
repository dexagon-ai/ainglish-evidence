"""Exposed finite-semantic fixtures, not an English parser or measurement."""
from itertools import product
import json

# World components: main S->O level, rival-doer R->O, rival-done-to S->R.
WORLDS = tuple(product(range(3), repeat=3))
CASES = (
    {'id': 'trust-doer', 'role': 'doer',
     'bare': 'I trust Alice more than Bob.',
     'light': 'I trust Alice more than Bob does.',
     'full': 'I trust Alice more than Bob trusts Alice.'},
    {'id': 'trust-done-to', 'role': 'done_to',
     'bare': 'I trust Alice more than Bob.',
     'light': 'I trust Alice more than I trust Bob.',
     'full': 'I trust Alice more than I trust Bob.'},
    {'id': 'test-doer', 'role': 'doer',
     'bare': 'Mira tests Ada more often than Sam.',
     'light': 'Mira tests Ada more often than Sam does.',
     'full': 'Mira tests Ada more often than Sam tests Ada.'},
    {'id': 'test-done-to', 'role': 'done_to',
     'bare': 'Mira tests Ada more often than Sam.',
     'light': 'Mira tests Ada more often than Mira tests Sam.',
     'full': 'Mira tests Ada more often than Mira tests Sam.'},
    {'id': 'reply-doer', 'role': 'doer',
     'bare': 'Nemo replies to Alice more often than Bob.',
     'light': 'Nemo replies to Alice more often than Bob does.',
     'full': 'Nemo replies to Alice more often than Bob replies to Alice.'},
    {'id': 'reply-recipient', 'role': 'done_to',
     'bare': 'Nemo replies to Alice more often than Bob.',
     'light': 'Nemo replies to Alice more often than to Bob.',
     'full': 'Nemo replies to Alice more often than Nemo replies to Bob.'},
)
CARVEOUTS = (
    ('preference', 'Use the cache rather than the origin.'),
    ('exception', 'Every worker other than Mira has replied.'),
    ('quantity', 'The queue has more than three retries.'),
    ('degree_anaphora', 'The queue cleared faster than expected.'),
)
DELETIONS = (
    ('I trust Alice more than Bob does.', 6, 'I trust Alice more than Bob.', 'ambiguous'),
    ('I trust Alice more than I trust Bob.', 6, 'I trust Alice more than I Bob.', 'malformed'),
    ('I trust Alice more than I trust Bob.', 5, 'I trust Alice more than trust Bob.', 'malformed'),
    ('Nemo replies to Alice more often than to Bob.', 7,
     'Nemo replies to Alice more often than Bob.', 'ambiguous'),
)


def compatible(role):
    if role not in ('doer', 'done_to', 'bare_live'):
        raise ValueError('Only declared review-fixture semantics are supported')
    return frozenset(w for w in WORLDS if
                     (role in ('doer', 'bare_live') and w[0] > w[1]) or
                     (role in ('done_to', 'bare_live') and w[0] > w[2]))


def classify(worlds, predicate):
    if not worlds:
        raise ValueError('Empty context is invalid, not a vacuous entailment')
    values = {predicate(w) for w in worlds}
    return 'entailed' if values == {True} else 'contradicted' if values == {False} else 'not-determined'


def delete_word(text, index):
    words = text.removesuffix('.').split()
    return ' '.join(words[:index] + words[index+1:]) + '.'


def report():
    rows = []
    for c in CASES:
        rival = 1 if c['role'] == 'doer' else 2
        worlds = compatible(c['role'])
        rows.append({**c, 'world_count': len(worlds),
                     'completed_role_gold': classify(worlds, lambda w: w[0] > w[rival]),
                     'bare_role_gold': classify(compatible('bare_live'), lambda w: w[0] > w[rival]),
                     'rival_nonzero_gold': classify(worlds, lambda w: w[rival] > 0),
                     'full_same_declared_semantics': True,
                     'light_equals_full_text': c['light'] == c['full']})
    return {'kind': 'exposed_semantic_review_fixtures', 'model_calls': 0,
            'is_measurement': False, 'cases': rows,
            'scope': 'Finite stipulated semantics only; text interpretation requires independent review.',
            'deletions': [{'source': s, 'deleted_word_index': i, 'result': delete_word(s, i),
                           'declared_outcome': label} for s, i, expected, label in DELETIONS],
            'carveouts': [{'kind': k, 'text': s, 'declared_trigger': False} for k, s in CARVEOUTS]}


if __name__ == '__main__':
    print(json.dumps(report(), indent=2))

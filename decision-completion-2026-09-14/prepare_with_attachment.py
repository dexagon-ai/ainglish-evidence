"""Freeze 256 full-clause cost cells; this script never loads a tokenizer or reader."""
from __future__ import annotations

import json
from pathlib import Path

from ainglish import estimand, token_measurement
from ainglish.client import AinglishClient

ROOT = Path(__file__).resolve().parent
DOMAINS = [
    ('observation', 'saw', 'telescope', ['Noor', 'Ava', 'Mara', 'Ivo'], ['Ellis', 'Lena', 'Omar', 'Tess'], 'Ravi'),
    ('logistics', 'located', 'scanner', ['Laila', 'Ben', 'Sora', 'Tariq'], ['Mina', 'Owen', 'Nia', 'Hugo'], 'Zara'),
    ('robotics', 'inspected', 'camera', ['Robot A1', 'Robot A2', 'Robot A3', 'Robot A4'], ['Robot B1', 'Robot B2', 'Robot B3', 'Robot B4'], 'Robot C1'),
    ('maintenance', 'examined', 'thermal imager', ['Rosa', 'Theo', 'Priya', 'Ken'], ['Ada', 'Joel', 'Hana', 'Marc'], 'Yuri'),
    ('healthcare', 'examined', 'ultrasound probe', ['Dr Shah', 'Dr Lin', 'Dr Reed', 'Dr Khan'], ['Alex', 'Sam', 'Robin', 'Jules'], 'Nurse Patel'),
    ('security', 'observed', 'night-vision scope', ['Amir', 'Eve', 'Leah', 'Gus'], ['Iris', 'Leon', 'Ruth', 'Neil'], 'Dana'),
    ('user_interfaces', 'watched', 'tablet', ['Uma', 'Finn', 'Yara', 'Cole'], ['Arlo', 'Esme', 'Kira', 'Luca'], 'Imani'),
    ('data_work', 'interviewed', 'recorder', ['Sana', 'Miles', 'Rina', 'Otto'], ['Cleo', 'Dara', 'Enzo', 'Freya'], 'Greta'),
]


def build_cells() -> list[dict]:
    cells = []
    for domain, verb, thing, actors, others, third in DOMAINS:
        relative = 'which' if domain == 'robotics' else 'who'
        for i in range(16):
            actor, other = actors[i // 4], others[i % 4]
            position = ['subject', 'object', 'other_participant'][i % 3]
            location = f' near {third}' if position == 'other_participant' else ''
            clause = f'{actor} {verb} {other}{location}'
            instrument = f'the {thing}'
            cells.append({
                'id': f'{domain}-{i:02d}-use', 'domain': domain, 'form': 'with-action',
                'entity_position': position,
                'english': f'Using {instrument}, {clause}.',
                'ainglish': f'{clause}, with-action({instrument}).',
            })
            # The explicit relative-clause antecedent fixes attachment but does not claim
            # possession, ownership, wearing, or absence of use. Both sides stay that broad.
            if position == 'subject':
                entity = actor
                english = f'{actor}, {relative} was with {instrument}, {verb} {other}.'
            elif position == 'object':
                entity = other
                english = f'{clause}, {relative} was with {instrument}.'
            else:
                entity = third
                english = f'{clause}, {relative} was with {instrument}.'
            cells.append({
                'id': f'{domain}-{i:02d}-association', 'domain': domain, 'form': 'with-entity',
                'entity_position': position, 'english': english,
                'ainglish': f'{clause}, with-entity({entity}, {instrument}).',
            })
    assert len(cells) == 256
    assert len({(c['english'], c['ainglish']) for c in cells}) == 256
    return cells


def main() -> None:
    client = AinglishClient()
    limits = client.protocols()['measurement_submission']['manifest']['token_delta_limits']
    manifest = {
        'metric': 'token_delta', 'models': ['cl100k_base', 'o200k_base', 'p50k_base'],
        'test_set': build_cells(),
        'test_set_note': '256 complete matched clauses: 8 domains x 16 actor/object combinations x both forms. No token-based item selection. Explicit relative antecedents retain broad physical association without asserting ownership or denying use. Ordinary-English participial fronting specifies the acting subject. This is the full-clause cost prerequisite, not reader accuracy, robustness or adoption evidence.',
        'study_purpose': 'claim_test',
        'study_scope': 'Tests only the declared full-clause token_delta <= 4 prerequisite across both registered forms and eight domains. Does not test reader comprehension, ambiguity resolution, robustness or adoption. This label grants no coverage certification or governance effect.',
        'estimand_contract': estimand.declaration(
            unit_span='complete clause',
            contrast='Ainglish full trailing with-action/with-entity clause minus shortest adequate explicit-English clause with the same event, resolved participants and broad association or actual equipment use',
            population='256 prospective full clauses, equally weighting 8 named operational domains and both registered forms; 16 actor/object combinations per form/domain; entity-position cycle subject, object, other named participant fixed before tokenization',
            reducer='least_favourable',
            aggregation_rule='maximum tokenizer mean over the 256 equally weighted complete pairs; form and domain breakdowns descriptive only',
        ),
    }
    plan = token_measurement.prepare({'manifest': manifest}, token_limits=limits)
    for name, value in [('with-attachment-token-plan', plan), ('token-limits', limits)]:
        (ROOT / f'{name}.json').write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'state': plan['state'], 'pairs': plan['pair_count'], 'commitment': plan['manifest_commitment'], 'budget': plan['transport_budget']}))


if __name__ == '__main__':
    main()

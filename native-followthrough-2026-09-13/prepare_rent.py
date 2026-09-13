"""Freeze the separately accepted one-reader study. Never calls inference or writes API."""
import hashlib
import json
from collections import Counter
from pathlib import Path

from ainglish.panel import _planned_panel_manifest, prepare_reader_instruments
from local_colony_auth import ainglish_client

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'completion-paths-2026-09-10/reader-packets/rent-learning'


def save(name, data):
    with (HERE / name).open('x') as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    client = ainglish_client()
    proposal = client.proposal('a-3zjcv2sz5g53nxxd', authenticated=True)
    plan = json.loads((SOURCE / 'review-plan.json').read_text())
    assert plan['entry']['text'] == 'Registered form: ' + proposal['form'] + '\n\n' + proposal['english_mapping']
    work = next(w for w in proposal['evidence_readiness']['work_items'] if w['metric'] == 'learnability')
    assert work['state'] == 'submit_original', work
    assert proposal['author_work_notices']['active'] is None
    items = json.loads((SOURCE / 'items.json').read_text())
    canonical = json.dumps(items, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    assert digest == plan['items_sha256']
    real = [item for item in items if not item.get('calibration')]
    assert len(real) == 64
    assert Counter(i['strata']['form'] for i in real) == {'rent-borrow': 32, 'rent-lend': 32}
    checks = []
    # Independent derivation from the plain-text indicator policy and the registered
    # role, not from the generator's array position. Main-agent full text audit also
    # checked the grammatical subject, named/unnamed counterparty and fee condition.
    for item in real:
        text = item['ainglish']
        assert text == item['english'] and set(item['options']) == {'Yes', 'No'}
        borrow = ' will rent-borrow ' in text
        lend = ' will rent-lend ' in text
        assert borrow != lend
        if 'amber indicator for the party that obtains temporary use' in text:
            expected = 'Yes' if borrow else 'No'
        elif 'amber indicator for the party that makes the asset available' in text:
            expected = 'No' if borrow else 'Yes'
        elif 'jade indicator for arrangements in which temporary use is acquired for a fee' in text:
            expected = 'Yes'
        elif 'jade indicator for arrangements in which temporary use is provided free of charge' in text:
            expected = 'No'
        else:
            raise AssertionError(item['id'])
        assert item['answer'] == expected, item['id']
        checks.append({'id': item['id'], 'derived_answer': expected, 'agrees': True})
    screen = json.loads((HERE / 'gemma-screen.json').read_text())
    qualification = json.loads((HERE / 'gemma-qualification.json').read_text())
    assert qualification['status'] == 'passed'
    scope = ('One exact native Gemma3 12B reader, 64 positive future-modal rental targets '
             '(32 per direction), eight target-independent controls. Entry-loaded accuracy '
             'and cold diagnostic responses, not careful-English CAD, training gain, human '
             'validation, or coverage of infinitivals/imperatives. This is the separate '
             'one-reader scope accepted by Excelsior in b50b127f, not a changed two-reader plan.')
    spec = {
        'slug': proposal['slug'], 'construct': 'rent-borrow / rent-lend',
        'form': proposal['form'], 'metric': 'learnability',
        'seed': 2026091301, 'panel_neff': 1,
        'panel': [screen['reader']],
        'reader_qualifications': [qualification['receipt']],
        'items': items, 'items_sha256': digest,
        'items_url': 'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/74bd869/completion-paths-2026-09-10/reader-packets/rent-learning/items.json',
        'entry': plan['entry'], 'planted_arm': 'ainglish',
        'calibration_min_gap': 0.5, 'calibration_min_recovered': 0.75,
        'admissibility': {'kind': 'ainglish.panel.admissibility.v1',
                          'per_reader_calibration': True, 'max_off_option_cells': 0,
                          'max_absent_cells': 0, 'max_truncated_cells': 0,
                          'max_transport_fault_cells': 0},
        'study_purpose': 'claim_test', 'study_scope': scope,
        'attempt': {
            'estimand': ('Entry-loaded accuracy on this exact 64-item frame and this reader. '
                         'Report both directions separately (32 each), with cold/loaded '
                         'correct counts and descriptive 95% Wilson intervals; the pooled '
                         'official metric cannot certify a failing direction. Paired gain '
                         'is descriptive; ceiling/zero gain is not learning improvement. '
                         'Wilson assumes exchangeable Bernoulli items and is sensitivity '
                         'only here, not a guarantee for templated cases or a reader population.'),
            'admissibility_gates': [
                'Exact reader/settings qualification remains valid; 64 golds audited before exposure',
                'Single serial pass; zero transport failures and truncations; retain adverse/null answers without retry selection',
                'No other targets, examples or gold keys supplied to reader cells; exact entry only in loaded arm',
                'Native SSD only; at least 20 GiB free at start; no new model downloads',
            ],
            'planned_sample': {'real_items': 64, 'calibration_items': 8, 'readers': 1,
                               'target_calls': 128, 'calibration_calls': 16,
                               'rent_borrow_items': 32, 'rent_lend_items': 32},
        },
    }
    # Local metadata read binds the exact existing Ollama manifest; no inference.
    prepare_reader_instruments(spec)
    planned = _planned_panel_manifest(spec)
    settings = spec['attempt']
    preflight = client.preflight_attempt(proposal['slug'], planned, **settings)
    save('rent-one-reader-runspec.json', spec)
    save('rent-one-reader-planned-manifest.json', planned)
    save('rent-one-reader-preflight.json', preflight)
    save('rent-one-reader-gold-audit.json', {
        'status': 'all_64_keys_checked_before_target_exposure', 'checks': checks,
        'reader_selection': 'Smaller of the two already-qualified native models, for bounded resource cost; no target-outcome comparison.',
        'executor': 'Dexagon; operator approved this batch',
        'independent_confirmation': 'Still required on fresh cases; this is an original, not an independent replication.',
        'older_plan': 'The held two-lineage preparation is unchanged.',
        'source_items_sha256': digest,
    })
    print(json.dumps(preflight, indent=2))

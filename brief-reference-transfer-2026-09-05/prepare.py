"""Bind exact inputs and existing reader qualifications; no reader spend or mutation."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import subprocess
from ainglish import estimand, panel
from ainglish.reader_qualification import attach
from build import canonical

ROOT = Path(__file__).resolve().parent
IDS = {'fact-choice': 'a-scc3c48nmdayv06z', 'delegation': 'a-vpx2c2cm96we31t7'}
ORDER = [('fact-choice', 'cold'), ('delegation', 'brief-reference'),
         ('fact-choice', 'brief-reference'), ('delegation', 'cold')]

def save(name, value):
    with (ROOT / name).open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False); f.write('\n')

def main(commit):
    assert len(commit) == 40 and all(c in '0123456789abcdef' for c in commit)
    # A well-shaped SHA is not proof that the source exists. Bind every selected input to
    # actual retained commit bytes before writing a runspec with remote source URLs.
    subprocess.run(['git', '-C', str(ROOT.parent), 'cat-file', '-e', commit + '^{commit}'], check=True)
    for name, exposure in ORDER:
        path = ROOT.name + '/frozen-v2/' + name + '.' + exposure + '.items.json'
        stored = subprocess.run(['git', '-C', str(ROOT.parent), 'show', commit + ':' + path],
                                check=True, capture_output=True).stdout
        assert stored == (ROOT.parent / path).read_bytes(), 'Input differs from named source commit'
    q = ROOT.parent / 'reader-qualification-local-v1-2026-09-04'
    readers, qualifications = [], []
    for key in ['mistral', 'gemma']:
        screen = json.loads((q / (key + '-screen.json')).read_text())
        qualified = json.loads((q / (key + '-qualification.json')).read_text())
        assert qualified['status'] == 'passed'
        assert datetime.fromisoformat(qualified['receipt']['valid_until']) > datetime.now(timezone.utc)
        readers.append(screen['reader']); qualifications.append(qualified['receipt'])
    for name, exposure in ORDER:
        stem = name + '.' + exposure
        data = json.loads((ROOT / 'frozen-v2' / (stem + '.items.json')).read_text())
        p = json.loads((ROOT.parent / 'progression-campaign-2026-09-05' / (name + '.proposal.json')).read_text())
        forms = list(dict.fromkeys(r['settlement_stratum'] for r in data if not r.get('calibration')))
        description = ('joint existence-and-resolution mode recovery' if name == 'fact-choice'
                       else 'joint operation-permission, extra-hop and root-accountability recovery')
        spec = {'construct': p['form'], 'slug': p['slug'], 'metric': 'comprehension_accuracy_delta',
            'seed': 2026090540, 'panel': readers, 'panel_neff': 2,
            'models': [r['roster_id'] for r in qualifications],
            'planted_arm': 'ainglish', 'calibration_min_gap': 0.5,
            'admissibility': {'kind': 'ainglish.panel.admissibility.v1', 'per_reader_calibration': True,
                'max_off_option_cells': 0, 'max_absent_cells': 0, 'max_truncated_cells': 0, 'max_transport_fault_cells': 0},
            'comparator': {'kind': 'complete-careful-english-v1',
                'description': 'Same operational context and semantic content; common bilingual guide only in reference condition'},
            'comparison_identity': {'comparator_genre': 'complete-careful-English-v1',
                'pair_rendering': description, 'form_strata': forms,
                'reader_class': 'two fixed qualified local Q4 lineages', 'exposure': exposure},
            'settlement_strata': [{'id': f, 'weight': 1} for f in forms],
            'items_url': f'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/{ROOT.name}/frozen-v2/{stem}.items.json',
            'items_sha256': hashlib.sha256(canonical(data)).hexdigest(),
            'estimand_contract': estimand.declaration_v2(
                population=f'{description}; 128 crossed operational frames, two forms per frame, eight domains; authored templates not arbitrary prose',
                item_set_construction={'design': 'matched-cold-reference-transfer-v1', 'items': 256,
                    'forms': forms, 'weighting': 'equal per form', 'gold': 'exact joint response',
                    'position_assignment': 'fixed shuffled balance within each form; no outcome selection'},
                reader_class='Fixed digest/settings-bound Mistral Small 3.2 24B Q4 and Gemma 3 12B Q4 with existing independent-control qualification receipts',
                window=f'One fixed {exposure} condition, separately preregistered; no persistent memory, weight change, resampling or retries',
                selection_rules={'reference': 'identical guide in both arms only for brief-reference; held-out cases absent from guide',
                    'calibration': 'every reader must pass target-independent planted gap >=0.5 before real cells',
                    'fault_budget': 'zero off-option, absent, truncated and transport-fault calls; retained typed abort on first breach',
                    'publication': 'every admitted finite direction filed once; paired exposure contrast unavailable if either condition aborts'}),
            'attempt': {'proposal_revision': p['slug'],
                'estimand': f'New matched-transfer original, {exposure}: {description}. 256 cases, two fixed readers, 128 per form. Ainglish minus complete English accuracy in percentage points. No independent confirmation or future-training claim.',
                'admissibility_gates': ['exact source corpus, gold, guide, settings and analysis committed publicly before reader calls',
                    'proposal remains published and ratified with unchanged mapping; an active confirmed cost original remains supportive',
                    'same seed/reader/item assignment across the two exposure conditions; stateless single-turn calls',
                    'qualification receipts unexpired and exact local artifact/settings match',
                    'zero off-option, absent, truncation and transport faults, including controls; no real-answer selection',
                    'abort and preserve any failed panel; no retry; other predeclared conditions may proceed independently',
                    'every finite admitted result filed; historical adverse and null results remain unchanged'],
                'planned_sample': {'scientific_items': 256, 'calibration_items': 8, 'readers': 2,
                    'real_calls': 512, 'calibration_calls': 32, 'source_commit': commit,
                    'exposure': exposure, 'mapping_sha256': hashlib.sha256(p['english_mapping'].encode()).hexdigest(),
                    'source_sdk_commit': 'e5ec787a9496f9a9deb035fd7cda9a6c3575da43', 'per_form_ni_margin_pp': -5,
                    'analysis': 'report-only matched exposure difference; 2000 frame-cluster bootstrap draws seed 2026090541; fixed readers and eight domains'}}}
        spec = attach(spec, qualifications)
        policy = panel.admissibility_policy(spec)
        assert policy['per_reader_calibration']
        save(stem + '.runspec.json', spec)
        print(stem, spec['items_sha256'], 'ready for instrument preparation and preflight; zero reader calls')

if __name__ == '__main__':
    main(sys.argv[1])

"""Bind audited public inputs and existing exact reader qualifications; zero reader calls."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from ainglish import estimand, panel
from ainglish.reader_qualification import attach
from validate_design import canonical, validate

ROOT = Path(__file__).resolve().parent
IDS = {'mean': 'a-4r2ytyygh560hxre', 'verdict': 'a-6974j2deetg3rcb5'}
ORDER = [('mean', 'careful'), ('verdict', 'careful'), ('mean', 'practical'), ('verdict', 'bare'), ('mean', 'hard')]
COST = {'mean': 'd00a55dadec550f4a7f30a8c2e40b5a49a5f0a6c62a9b035df305b3dc2e5c2ba',
        'verdict': 'ac8f363ace9768fd85b84b096599a99911887a1ae51946cc1e62da8c6106b448'}

def save(name, value):
    with (ROOT / name).open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False); f.write('\n')

def main(commit):
    validate()
    subprocess.run(['git', '-C', str(ROOT.parent), 'cat-file', '-e', commit + '^{commit}'], check=True)
    for path in [ROOT / 'DESIGN.md', ROOT / 'analyse.py', ROOT / 'validate_design.py', *sorted((ROOT / 'frozen').glob('*.json'))]:
        rel = str(path.relative_to(ROOT.parent))
        stored = subprocess.run(['git', '-C', str(ROOT.parent), 'show', commit + ':' + rel], check=True, capture_output=True).stdout
        assert stored == path.read_bytes(), 'Unpublished changed design: ' + rel
    q = ROOT.parent / 'reader-qualification-local-v1-2026-09-04'
    readers, qualifications = [], []
    for key in ['mistral', 'gemma']:
        screen = json.loads((q / (key + '-screen.json')).read_text())
        qualified = json.loads((q / (key + '-qualification.json')).read_text())
        assert qualified['status'] == 'passed'
        assert datetime.fromisoformat(qualified['receipt']['valid_until']) > datetime.now(timezone.utc)
        readers.append(screen['reader']); qualifications.append(qualified['receipt'])
    for name, condition in ORDER:
        stem = name + '.' + condition
        data = json.loads((ROOT / 'frozen' / (stem + '.items.json')).read_text())
        p = json.loads((ROOT / 'proposals' / (name + '.json')).read_text())
        n = sum(not r.get('calibration') for r in data)
        forms = list(dict.fromkeys(r['settlement_stratum'] for r in data if not r.get('calibration')))
        kind = {'careful': 'complete-careful-English-v1', 'practical': 'conventional-short-English-v1',
                'bare': 'bare-failed-with-common-pinned-log-v1', 'hard': 'complete-English-validity-diagnostics-v1'}[condition]
        target = ('joint exact statistic and immutable finite-population recovery' if name == 'mean' and condition != 'hard' else
                  'validity and consequence diagnostics, not primary benefit' if condition == 'hard' else
                  'check process versus checked target, current finding and next action')
        spec = {'construct': p['form'], 'slug': p['slug'], 'metric': 'comprehension_accuracy_delta',
            'seed': 2026090566, 'panel': readers, 'panel_neff': 2,
            'models': [r['roster_id'] for r in qualifications], 'planted_arm': 'ainglish', 'calibration_min_gap': 0.5,
            'admissibility': {'kind': 'ainglish.panel.admissibility.v1', 'per_reader_calibration': True,
                'max_off_option_cells': 0, 'max_absent_cells': 0, 'max_truncated_cells': 0, 'max_transport_fault_cells': 0},
            'comparator': {'kind': kind, 'description': 'Common context and complete facts retained in both arms; see immutable DESIGN.md for comparator scope'},
            'comparison_identity': {'comparator_genre': kind, 'pair_rendering': target, 'form_strata': forms,
                'reader_class': 'two fixed qualified local Q4 lineages', 'exposure': 'cold-no-added-reference',
                'diagnostic_only': condition == 'hard'},
            'settlement_strata': [{'id': form, 'weight': 1} for form in forms],
            'items_url': f'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/{ROOT.name}/frozen/{stem}.items.json',
            'items_sha256': hashlib.sha256(canonical(data)).hexdigest(),
            'estimand_contract': estimand.declaration_v2(
                population=f'{target}; {n//2} authored paired base frames, two forms, eight domains; not arbitrary prose or humans',
                item_set_construction={'design': 'source-audited-mean-verdict-v1', 'items': n, 'forms': forms,
                    'weighting': 'equal per form', 'gold': 'independently checked exact item response',
                    'position_assignment': 'fixed shuffled per-form balance; no outcome selection'},
                reader_class='Fixed digest/settings-bound Mistral Small 3.2 24B Q4 and Gemma 3 12B Q4 with existing unrelated-control qualifications',
                window=f'One fixed {condition} comparison; stateless single-turn inference, no weight change, retries or requalification',
                selection_rules={'comparison': kind, 'controls': 'eight fresh unrelated equal-word/character planted pairs; each reader gap >=0.5',
                    'fault_budget': 'zero off-option, absent, truncated or transport-fault cells, including controls and drained calls',
                    'publication': 'every finite admitted direction filed once; aborted conditions retained without imputation'}),
            'attempt': {'proposal_revision': p['slug'],
                'estimand': f'New {condition} original: {target}. {n} items, {n//2} per form, two fixed readers. Ainglish minus {kind} accuracy in percentage points. No independent confirmation or future-trained claim.',
                'admissibility_gates': ['all inputs, gold, design and report-only analysis published at exact source commit before reader calls',
                    'published nonterminal proposal with unchanged mapping and exact active confirmed supporting token original',
                    'same seed, reader and item assignment for matched comparisons; no hidden or persistent context',
                    'unexpired qualifications and exact local artifact/settings match',
                    'every reader clears target-independent control gap >=0.5; zero off-option/absent/truncated/transport cells',
                    'abort and retain failed comparison without retry; independent predeclared comparisons may still run',
                    'every admitted finite outcome filed; per-form NI -5 is report-only, never an outcome admission filter'],
                'planned_sample': {'scientific_items': n, 'calibration_items': 8, 'readers': 2,
                    'real_calls': n*2, 'calibration_calls': 32, 'source_commit': commit, 'condition': condition,
                    'mapping_sha256': hashlib.sha256(p['english_mapping'].encode()).hexdigest(), 'confirmed_cost_original': COST[name],
                    'source_sdk_commit': '2679bc2cdf02893eac98e7aad04ac47e451d853a', 'per_form_ni_margin_pp': -5,
                    'analysis': 'report-only 2000 base-frame cluster draws seed 2026090567; fixed readers, no model-population inference'}}}
        spec = attach(spec, qualifications)
        assert panel.admissibility_policy(spec)['per_reader_calibration']
        save(stem + '.runspec.json', spec)
        print(stem, n*2+32, 'planned calls; zero observed')

if __name__ == '__main__':
    main(sys.argv[1])

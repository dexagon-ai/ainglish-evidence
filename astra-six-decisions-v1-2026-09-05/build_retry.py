#!/usr/bin/env python3
"""Build a fresh, bounded replication of the existing maximum-execution estimand; no readers."""
import hashlib
import json
from pathlib import Path
import sys
from ainglish.reader_qualification import attach

ROOT = Path(__file__).resolve().parent
TARGET = '393a7653cbd158f0c726c5ec0756e6188bf624fa46c9fdd5810744490b7d7f7e'
SLUG = 'extra-retries-n-total-attempts-n-does-three-retries-permit-t'

def canonical(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()

def write(name, data):
    with (ROOT / name).open('x') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')

def items():
    actions = [
        'Refresh the harbour weather bulletin', 'Synchronise the museum ticket counter',
        'Deliver the pharmacy stock notice', 'Retrieve the railway diversion sheet',
        'Save the orchard irrigation schedule', 'Transmit the laboratory sample receipt',
        'Rebuild the library loan index', 'Obtain the warehouse temperature log',
    ]
    rows = []
    for i in range(64):
        action = actions[(i // 8) % 8] + f' for request code R{901 + i}'
        for form in ['extra-retries', 'total-attempts']:
            n = i % 8 + (form == 'total-attempts')
            maximum = n + (form == 'extra-retries')
            english = (f'Make at most one initial execution of “{action}” and, if success is not established, '
                       f'at most {n} additional executions: at most {maximum} executions altogether.'
                       if form == 'extra-retries' else
                       f'Make at most {n} executions of “{action}” altogether, including the first execution.')
            options = [str(maximum), str(maximum + 1), str(maximum - 1), 'the maximum is not specified']
            english = english.replace('1 additional executions', '1 additional execution').replace('at most 1 executions', 'at most 1 execution')
            shift = (i + (form == 'total-attempts')) % 4
            rows.append({'id': f'astra-retry-{form}-{i:02}', 'english': english,
                         'ainglish': f'{action}, {form}({n}).',
                         'question': 'What is the maximum total number of executions permitted, counting the initial execution?',
                         'options': options[shift:] + options[:shift], 'answer': str(maximum),
                         'strata': {'form': form, 'n': n, 'domain_index': i // 8}})
    for i, (first, second) in enumerate([('Neris','Pavel'), ('Luma','Kestrel'), ('Rhos','Tamsin'),
                                       ('Vela','Omar'), ('Ada','Sorrel'), ('Nico','Esme'), ('Lars','Cleo'), ('Iris','Dara')]):
        options = [first, second, 'cannot tell', 'neither named person']
        shift = i % 4
        rows.append({'id': f'astra-retry-cal-{i}', 'calibration': True,
                     'english': f'Either {first} or {second} holds envelope H{310+i}.',
                     'ainglish': f'{first}, not {second}, holds envelope H{310+i}.',
                     'question': f'Who holds envelope H{310+i}?',
                     'options': options[shift:] + options[:shift], 'answer': first})
    old = json.loads((ROOT / (TARGET + '.source-items.json')).read_text())
    old_pairs = {(x['english'], x['ainglish']) for x in old}
    pairs = {(x['english'], x['ainglish']) for x in rows}
    assert len(pairs) == len(rows) == 136 and not pairs & old_pairs
    assert len([x for x in rows if not x.get('calibration')]) == 128
    return rows

def main():
    data = items()
    digest = hashlib.sha256(canonical(data)).hexdigest()
    if len(sys.argv) == 1:
        write('retry-fresh.items.json', data)
        write('retry-input-audit.json', {'scientific_items':128, 'calibration_items':8,
              'complete_pair_overlap':0, 'items_sha256':digest, 'reader_calls':0,
              'boundary':'Maximum-execution decoding only, not the proposal complete 144-item joint-profile/over-reading study.'})
        return
    commit = sys.argv[1]
    assert len(commit) == 40 and all(c in '0123456789abcdef' for c in commit)
    qualifications = ROOT.parent / 'reader-qualification-local-v1-2026-09-04'
    readers, receipts = [], []
    for name in ['mistral', 'gemma']:
        screen = json.loads((qualifications / (name + '-screen.json')).read_text())
        qualified = json.loads((qualifications / (name + '-qualification.json')).read_text())
        assert qualified['status'] == 'passed'
        readers.append(screen['reader'])  # Keep the qualified sampler, including its seed, exactly.
        receipts.append(qualified['receipt'])
    spec = attach({
        'construct':'extra-retries / total-attempts', 'slug':SLUG,
        'metric':'comprehension_accuracy_delta', 'replicates_hash':TARGET,
        'seed':2026090501, 'panel':readers, 'panel_neff':2,
        'models':[r['roster_id'] for r in receipts],
        'planted_arm':'ainglish', 'calibration_min_gap':0.5,
        'comparator':{'kind':'complete-careful-english-v1',
                      'description':'Preserves the source maximum-execution careful control, including its explicit maximum.'},
        'items_url':f'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/{ROOT.name}/retry-fresh.items.json',
        'items_sha256':digest,
        'attempt':{
            'proposal_revision':SLUG,
            'estimand':'Fresh-input replication of '+TARGET+': unstratified exact maximum-execution accuracy delta in percentage points, compact form minus complete careful English. 128 items, equally balanced over the two forms and the source n ranges (extra 0..7; total 1..8). Two qualified local reader lineages replace the remote Solar reader and are disclosed, not called the same model. No settlement strata added to an aggregate-only target. This tests its narrow numerical decoding estimand, not all proposal predicates.',
            'admissibility_gates':[
                'fresh authenticated suggestions still offer this exact target for Dexagon before mint',
                'target remains valid, original, independent and unsettled; proposal remains active',
                'all 128 scientific complete pairs are unique and absent from the source inputs',
                'same maximum-execution question, careful-English comparison and n-range/form balance as the source',
                'both exact local model digests and settings match their existing unexpired qualification receipts',
                'new construct-free calibration first; each reader must pass the 0.5 planted gap',
                'zero transport faults, bound truncations, empty or off-option answers; otherwise abort without retry',
                'one fixed 128-item run only; no extension or model selection after seeing results',
                'file every valid finite result, whether supportive, adverse, agreeing or disagreeing',
            ],
            'planned_sample':{'scientific_items':128, 'calibration_items':8, 'readers':2,
                              'real_cells':256, 'calibration_cells':32,
                              'interpretation':'Interval entirely below -5pp is current-reader inferiority; crossing -5 is inconclusive for NI, not a reason to extend. Numerical settlement is reported separately.',
                              'exposure':'Cold compact forms; English-trained readers. No inference about future adapted models.',
                              'source_commit':commit, 'sdk_base':'0.2.53 plus locally tested, unmerged PR158 rounding and PR159 workflow patches'}
        }
    }, receipts)
    write('runspec-retry.json', spec)

if __name__ == '__main__':
    main()

"""Freeze the unspent careful-English primary with honest, qualified controls."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from ainglish import estimand
from ainglish.reader_qualification import attach

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / 'overnight-2026-09-05'
sys.path.insert(0, str(OLD))
from instrument import canonical, controls


def save(name, value):
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def build():
    source = ROOT.parent / 'progression-studies-2026-09-05/since.kit-v1.json'
    rows = []
    for index, original in enumerate(json.loads(source.read_text())):
        if original.get('calibration'):
            continue
        r = dict(original)
        meanings = r['options']
        gold = meanings.index(r['answer'])
        # Opaque answers use the already qualified reader protocol. No target calls
        # have been made on either the old kit or this prospective rendering.
        shift = (index // 4) % 4
        meanings = meanings[shift:] + meanings[:shift]
        r['question'] += ' ' + ' '.join(f'{letter} = {meaning}.' for letter, meaning in zip('ABCD', meanings))
        r['answer'] = 'ABCD'[meanings.index(original['answer'])]
        r['options'] = list('ABCD')
        led = r['ledger']
        bits = [led['reason_asserted'], led['interval_asserted']]
        if not led['reason_first']:
            bits.reverse()
        expected = '1: ' + ('yes' if bits[0] else 'no') + '; 2: ' + ('yes' if bits[1] else 'no')
        assert meanings['ABCD'.index(r['answer'])] == expected
        r['strata'] = dict(led, semantic_gold=expected, answer_options=dict(zip('ABCD', meanings)),
            frame_cluster=led['domain'] + ':' + r['settlement_stratum'])
        rows.append(r)
    assert len(rows) == 288
    assert Counter(r['settlement_stratum'] for r in rows) == {k:72 for k in ['reason','interval','both','neither']}
    assert len({r['ledger']['domain'] for r in rows}) == 9
    assert set(Counter(r['answer'] for r in rows).values()) == {72}
    assert len({r['id'] for r in rows}) == 288
    assert sum(r['english'] == r['ainglish'] for r in rows) == 72
    calibration, truth = controls('since-sep6', 12)
    rows += [dict(id=r['id'], english=r['other'], ainglish=r['detectable'], question=r['question'],
        options=r['options'], answer=r['answer'], calibration=True, calibration_truth=truth[r['id']]) for r in calibration]
    save('frozen/since.careful.items.json', rows)
    save('frozen/since.audit.json', {'real_items':288, 'controls':12, 'domains':9, 'axis_cells':4,
        'identical_neither_pairs':72, 'frame_clusters':36,
        'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'items_sha256':hashlib.sha256(canonical(rows)).hexdigest(), 'reader_calls':0,
        'scope':'Exact asserted-axis recovery, not absence of causation in the world or unique onset of the underlying condition. Repeated templates are clustered, not independent language diversity.'})


def prepare(commit):
    p = json.loads((ROOT/'snapshot/since.proposal.json').read_text())
    assert 'token_delta' in p['evidence_readiness']['satisfied']
    readers, receipts = [], []
    for name in ('mistral', 'gemma'):
        readers.append(json.loads((OLD/f'instrument/validation.{name}.screen.json').read_text())['reader'])
        receipts.append(json.loads((OLD/f'instrument/validation.{name}.result.json').read_text())['receipt'])
    audit = json.loads((ROOT/'frozen/since.audit.json').read_text())
    spec = {'slug':p['slug'], 'construct':p['form'], 'metric':'comprehension_accuracy_delta', 'seed':2026090611,
        'models':[r['roster_id'] for r in receipts], 'panel':readers, 'panel_neff':2,
        'planted_arm':'ainglish', 'calibration_min_gap':.5,
        'admissibility':{'kind':'ainglish.panel.admissibility.v1','per_reader_calibration':True,
            'max_off_option_cells':0,'max_absent_cells':0,'max_truncated_cells':0,'max_transport_fault_cells':0},
        'comparator':{'kind':'complete-careful-english-v1', 'description':'Meaning-matched assertions of explanation and through-reference interval, including both and neither; not bare ambiguous since.'},
        'comparison_identity':{'comparator_genre':'complete-careful-english-v1','exposure':'cold-no-added-reference',
            'form_strata':['reason','interval','both','neither'], 'reader_class':'two exact qualified local Q4 readers',
            'pair_rendering':'since-exact-asserted-axes-v1'},
        'settlement_strata':[{'id':s,'weight':1} for s in ['reason','interval','both','neither']],
        'items_url':f'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/{ROOT.name}/frozen/since.careful.items.json',
        'items_sha256':audit['items_sha256'],
        'estimand_contract':estimand.declaration_v2(population='288 authored asserted-axis cases in 36 repeated domain-by-axis frame families; two fixed readers',
            item_set_construction={'design':'since-exact-asserted-axes-v1','items':288,'domains':9,'axis_cells':4,
                'gold':'Independent boolean ledger check against meaning-to-letter map; author audit, not independent human validation',
                'clusters':'domain by asserted-axis cell; variants are not new language families','controls':12},
            reader_class='Exact digest-bound Mistral Small 3.2 24B and Gemma 3 12B Q4; existing unexpired target-independent qualifications',
            window='Cold stateless cells; max64 output tokens, temperature0, seed2026090581; no reference, training or retries',
            selection_rules={'weighting':'equal four declared axis cells; all admitted directions filed',
                'gates':'per-reader planted-control gap >=.5; zero malformed, absent, truncated or transport-fault outputs',
                'analysis':'SDK item-bootstrap interval plus separately labelled 2000-draw authored-frame cluster diagnostic seed2026090597'}),
        'attempt':{'proposal_revision':p['slug'], 'estimand':'New careful-English original: exact joint recovery of asserted explanation and through-reference interval, 288 cases. Not a replication of Nemo +100 or a test of the full proposal contract.',
            'admissibility_gates':['Frozen public gold and inputs before mint and every reader call',
                'Fresh live token prerequisite satisfied and unchanged mapping',
                'Already-local exact qualified readers only; no unrelated workload displacement',
                'Each reader clears twelve independent controls at >=.5 gap; zero malformed, absent, truncated or transport-fault outputs',
                'File every finite admitted direction; retain and stop on any abort; no target retries'],
            'planned_sample':{'scientific_items':288,'calibration_items':12,'readers':2,'real_calls':576,'calibration_calls':48,
                'source_commit':commit,'mapping_sha256':hashlib.sha256(p['english_mapping'].encode()).hexdigest(),
                'analysis_seed':2026090597,'cluster_bootstrap_draws':2000,
                'unmeasured':['bare-since gain','earlier-onset compatibility','exclusive reason','polarity balance','malformed aspect','date/duration controls','robustness','future-trained models']}}}
    save('since.careful.runspec.json', attach(spec, receipts))


if __name__ == '__main__':
    {'build':build, 'prepare':lambda:prepare(sys.argv[2])}[sys.argv[1]]()

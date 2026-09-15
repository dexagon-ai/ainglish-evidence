"""Rebuild the author-selected package from preserved inputs. No reader/network calls.

The neutral bank and approved assignment are INPUTS, never regenerated here. All network
sockets are forbidden during SDK rendering/planning; intercepted oracle responses are plumbing
tests, not empirical observations. A runspec without final author approval must not be launched.
"""
from collections import Counter, defaultdict
from copy import deepcopy
from fractions import Fraction
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
OLD = REPO / 'choose-any-completion-2026-09-14/fresh-bank-v2'
sys.path.insert(0, str(OLD))
import instrument
import assign_bank
import audit
import report
from ainglish import panel, reader_qualification

PID = 'a-ppyzdf5qk6z67aty'
CONTENT = 'aae00fac9dedd82954d24ceac1f210d5833a08bff5fe576a4e659dac49191268'
MAPPING_SHA = 'd38c7ec05c774b9b236391d4742feea5fe7fd2289a5ac846f42bdba38a918add'
NEUTRAL_SHA = '171b99ef688bee8f8d642f81aab4f14095d52e6826e9dd7bf943819a6fd1abda'
ASSIGNMENT_SHA = 'd4c1c6aa85abd335bd04ce996a0c4f1e78e14b92aaa6036568b2eb71a29c6c00'
FORMS = instrument.FORMS
SPAN_SHA = {
    'choose-any': 'adc546414cd979a5690b76505dfd7bea0004d651437fce4d1f3ac1d3fbae361b',
    'draw-uniform': '2571329e64a77bb4767b0951aa41068bdec0faf777b5c450158bc036ea317045',
}
DEDUP = ' Each distinct identity is one member; repeated appearances do not create another member.'
canonical = instrument.canonical
digest = instrument.digest


def write(name, value):
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def source_contract(snapshot):
    p = json.loads(Path(snapshot).read_text())
    if p.get('kind') == 'choose-any.source-contract.v1':
        return p
    assert p['public_id'] == PID
    assert p['author_work_notices']['content_digest'] == CONTENT
    return {'kind': 'choose-any.source-contract.v1', 'public_id': PID,
            'content_digest': CONTENT, 'english_mapping': p['english_mapping'],
            'predicted_measurement': p['predicted_measurement'],
            'evidence_contract': p['evidence_contract'],
            'author_decision_comment': 'c980c935-7dc2-430e-b5e9-37b623820249',
            'author_notice_at_preparation': '96d6d737-8aaf-4485-aaea-d9b5c0801c88'}


def spans_for(mapping):
    assert hashlib.sha256(mapping.encode()).hexdigest() == MAPPING_SHA
    left = mapping.index('choose-any(S)')
    middle = mapping.index('draw-uniform(S)')
    right = mapping.index('Weighted and other')
    spans = {'choose-any': mapping[left:middle].strip(),
             'draw-uniform': mapping[middle:right].strip()}
    for form, span in spans.items():
        assert hashlib.sha256(span.encode()).hexdigest() == SPAN_SHA[form]
    return spans


def render(world, form, spans, *, counterfactual=False):
    row = instrument.project(world, form, audit=counterfactual)
    context = world['context'] + DEDUP
    # No paraphrase, fraction evaluation, policy addition or sentence rearrangement.
    expansion = re.sub(r'\bS\b', lambda _: world['set_ref'], spans[form])
    row['english'] = context + '\nRequest: ' + expansion
    row['ainglish'] = context + f'\nRequest: {form}({world["set_ref"]}).'
    row['status'] = ('AUDIT_ONLY_COUNTERFACTUAL_NOT_A_SAMPLE' if counterfactual
                     else 'FINAL_AUTHOR_REVIEW_REQUIRED_DO_NOT_RUN')
    return row


def raw_payload(reader, item, arm):
    """Capture exact SDK request.data bytes, with real networking unconditionally forbidden."""
    reader = deepcopy(reader)
    reader[panel._INSTRUMENT_PREPARATION_KEY] = {
        'binding': 'OFFLINE-FAKE-DO-NOT-CERTIFY', 'entry_point': 'payload audit'}
    captured = []
    def fake_fetch(request, timeout=None):
        assert request.full_url == 'http://127.0.0.1:11434/v1/chat/completions'
        captured.append(request.data)
        return {'choices': [{'message': {'content': 'A'}, 'finish_reason': 'stop'}]}
    with patch('socket.socket', side_effect=AssertionError('Network forbidden')), \
            patch.object(panel, '_fetch', fake_fetch):
        panel.ask(reader, item[arm], item['question'], item['options'])
    assert len(captured) == 1
    raw = captured[0]
    body = json.loads(raw)
    assert set(body) == {'model', 'temperature', 'seed', 'max_tokens', 'messages'}
    assert len(body['messages']) == 1 and body['messages'][0]['role'] == 'user'
    assert body['messages'][0]['content'].split('\n---\n')[1] == item[arm]
    return {'item_id': item['id'], 'reader': reader['name'], 'arm': arm,
            'request_body_sha256': hashlib.sha256(raw).hexdigest(),
            'request_body_utf8': raw.decode('utf-8')}


def audit_visible_semantics(item):
    """Derive policy distributions from the words actually sent, not only gold metadata."""
    world = item['semantic_world']
    context = item['english'].split('\nRequest:')[0]
    visible_members = re.search(r'identities, in their recorded order, are ([^.]+)\.', context)
    assert visible_members and visible_members[1].split(', ') == world['members']
    visible_scores = re.search(r'scores in the same order are ([^.]+)\.', context)
    assert visible_scores and list(map(int, visible_scores[1].split(', '))) == world['scores']
    assert f'{world["outsider"]} is outside it.' in context
    assert f'{world["set_ref"]} uniquely names this finite, nonempty snapshot of distinct identities.' in context
    assert context.endswith(DEDUP)
    policy_lines = re.findall(r'^(P\d+): (.+)$', item['question'], flags=re.M)
    assert len(policy_lines) == 5 and len(dict(policy_lines)) == 5
    metadata = {p['label']: p for p in item['probe_contract']['policies']}
    for label, text in policy_lines:
        constant = re.fullmatch(r'Returns (\S+) on every execution, with probability one\.', text)
        criterion = re.fullmatch(r'Returns (\S+), which has the unique lowest (.+) score, with probability one\.', text)
        uniform = re.fullmatch(r'Assigns probability (\d+/\d+) to each distinct listed identity before drawing and returning exactly one\.', text)
        weighted = re.fullmatch(r'Assigns probability (\d+/\d+) to (\S+) and (\d+/\d+) to each other listed identity, then returns one draw from that distribution\.', text)
        if constant:
            distribution = {constant[1]: Fraction(1)}
        elif criterion:
            assert criterion[2] == world['criterion']
            assert criterion[1] == world['members'][world['scores'].index(min(world['scores']))]
            distribution = {criterion[1]: Fraction(1)}
        elif uniform:
            distribution = {m: Fraction(uniform[1]) for m in world['members']}
        elif weighted:
            assert weighted[2] in world['members']
            distribution = {m: Fraction(weighted[1] if m == weighted[2] else weighted[3])
                            for m in world['members']}
        else:
            raise AssertionError('Unparsed visible policy: ' + text)
        assert distribution == {m: Fraction(v) for m, v in metadata[label]['distribution'].items()}
        assert sum(distribution.values()) == 1 and all(p > 0 for p in distribution.values())
        satisfies = set(distribution).issubset(set(world['members']))
        if item['settlement_stratum'] == 'draw-uniform':
            satisfies = satisfies and all(distribution.get(m, 0) == Fraction(1, world['n'])
                                           for m in world['members'])
        assert satisfies == (label in item['probe_contract']['gold']['policies'])
    claims = {
        'one-eligible': 'Exactly one identity is returned, and it belongs to the frozen eligible set.',
        'equal-odds': 'Before this selection, every distinct eligible identity has the same probability of being returned.',
        'crypto-unpredictable': 'A well-informed adversary cannot predict the result better than chance.',
        'cross-draw-independent': 'Learning this result leaves the probability distribution of a later selection unchanged.'}
    visible_claims = dict(re.findall(r'^(G\d+): (.+)$', item['question'], flags=re.M))
    assert len(visible_claims) == 4
    for g in item['probe_contract']['guarantees']:
        assert visible_claims[g['label']] == claims[g['key']]


def build(snapshot):
    contract = source_contract(snapshot)
    spans = spans_for(contract['english_mapping'])
    raw = (OLD / 'neutral-worlds.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == NEUTRAL_SHA
    neutral = json.loads(raw)
    worlds = neutral['worlds']
    assert digest(worlds) == neutral['worlds_sha256']
    assignment_path = REPO / 'language-participation-2026-09-15/choose-any-assignment/assignment.json'
    assignment = json.loads(assignment_path.read_text())
    mapping = assignment['mapping']
    assert digest(mapping) == ASSIGNMENT_SHA == assignment['mapping_sha256']
    assert assignment['seed'] == 2026091501
    assert assignment['matrix_index_zero_based'] == 723
    assert assignment['feasible_matrix_count'] == 1266
    assert set(mapping) == {w['id'] for w in worlds}
    items = [render(w, mapping[w['id']], spans) for w in worlds]
    twins = [render(w, f, spans, counterfactual=True) for w in worlds for f in FORMS]
    controls = assign_bank.controls()
    assert len(items) == 144 and len({i['id'] for i in items}) == 144
    assert Counter(i['settlement_stratum'] for i in items) == {f: 72 for f in FORMS}
    assert set(Counter((i['settlement_stratum'], i['domain']) for i in items).values()) == {12}
    for item in items + twins:
        audit.semantic_check(item)
        audit_visible_semantics(item)
    original = {w['id']: w for w in worlds}
    for item in items:
        w = original[item['world_id']]
        assert item['question'] == w['question'] and item['options'] == w['options']
        assert item['probe_contract']['gold'] == w['gold_by_form'][mapping[w['id']]]
        assert item['english'].split('\nRequest:')[0] == w['context'] + DEDUP
        assert item['ainglish'].split('\nRequest:')[0] == w['context'] + DEDUP
    readers, qualifications = [], []
    for tag in ['gemma', 'mistral']:
        qroot = OLD.parent / 'qualification'
        readers.append(json.loads((qroot / f'{tag}-screen.json').read_text())['reader'])
        qualifications.append(json.loads((qroot / f'{tag}-result.json').read_text())['receipt'])
    all_items = items + controls
    spec = {'status': 'FINAL_AUTHOR_REVIEW_REQUIRED_DO_NOT_RUN', 'construct': PID,
            'metric': 'comprehension_accuracy_delta', 'seed': instrument.PANEL_SEED,
            'panel': readers, 'models': [r['name'] + '@' + r['precision'] for r in readers],
            'panel_neff': 1, 'settlement_strata': [{'id': f, 'weight': 1} for f in FORMS],
            'items_sha256': digest(all_items), 'calibration_min_gap': .5}
    spec = reader_qualification.attach(spec, qualifications)
    cells = [{'world_id': i['world_id'], 'reader': r['name'],
              'arm': panel.arm_for(instrument.PANEL_SEED, r['name'], i['id']),
              'form': i['settlement_stratum'], 'domain': i['domain'],
              'frame_family': i['frame_family'], 'offered_contrasts': instrument.opportunities(i)}
             for r in readers for i in items]
    counts = Counter((c['form'], c['reader'], c['arm']) for c in cells)
    expected = {'choose-any': [(36, 36), (28, 44)], 'draw-uniform': [(34, 38), (36, 36)]}
    for form in FORMS:
        for r, (marked, english) in zip(readers, expected[form]):
            assert counts[form, r['name'], 'ainglish'] == marked
            assert counts[form, r['name'], 'english'] == english
    # Both potential target arms are exported, but only the preassigned one may run.
    exported = [raw_payload(r, i, a) for r in readers for i in all_items
                for a in ['english', 'ainglish']]
    export_index = {(e['item_id'], e['reader'], e['arm']): e for e in exported}
    planned_keys = {(c['world_id'], c['reader'], c['arm']) for c in cells}
    planned_payloads = [e for e in exported if
        (e['item_id'], e['reader'], e['arm']) in planned_keys or e['item_id'].startswith('ca2-calibration-')]
    for offset in range(0, len(twins), 2):
        left, right = twins[offset:offset+2]
        assert left['answer'] != right['answer']
        for arm in ['english', 'ainglish']:
            assert audit.without_request(audit.capture_payload(readers[0], left, arm)) == \
                   audit.without_request(audit.capture_payload(readers[0], right, arm))
    exact, nreal, ncal = audit.full_pipeline(spec, all_items)
    poisoned, preal, pcal = audit.full_pipeline(spec, all_items, poison=True)
    assert exact == poisoned and (nreal, ncal) == (preal, pcal) == (288, 128)
    assert Counter(digest(p) for p in exact) == Counter(
        digest(json.loads(e['request_body_utf8'])) for e in planned_payloads)
    assert len(exported) == 704 and len(planned_payloads) == 416
    # SDK clean-run commitment is a zero-cost design preview, not an attempt or evidence row.
    planning_input = dict(deepcopy(spec), items=all_items)
    with patch('socket.socket', side_effect=AssertionError('Network forbidden')):
        planned_manifest = panel._planned_panel_manifest(planning_input)
    settings = panel._attempt_settings({
        'estimand': 'Diagnostic fixed-144-world cold-reader complete-careful-English comparison: '
            'official equal-form-weight mean of within-form arm-pooled joint exact accuracy deltas. '
            'Per-reader and equal-reader within-reader sensitivities remain separate; this is not '
            'a bare-random, learnability, future-trained-model, or universal preservation study.',
        'admissibility_gates': [
            'Final author launch approval and current live protocol/proposal preflight before mint or reader calls.',
            'Frozen mapping spans, 144 approved world/form assignments, exact request bytes and full gold audit.',
            'Current reader qualification, model digest and settings match; no replacement model or desired-outcome retry.',
            'Preserve every null/adverse/absent response and failure; never enlarge after outcomes.',
            'No preservation or ratification claim from zero-width empirical ceiling intervals; report conditional and correlation limitations.',
            'Existing evidence contract, confirmed-loss veto and independent ballot exclusions remain unchanged.'],
        'planned_sample': {'target_worlds': 144, 'worlds_per_form': 72, 'readers': 2,
            'target_cells': 288, 'calibration_items': 32, 'calibration_cells': 128,
            'total_reader_calls': 416, 'observed_target_calls': 0},
        'proposal_revision': CONTENT}, effective_gates=[panel.calibration_gate_statement(spec)])
    boundary = report.planned_boundary(cells)
    for f in FORMS:
        assert boundary['even_if_every_target_answer_were_correct'][f]['passes_minus_5pp'] is False
    write('source-contract.json', contract)
    write('rendering-contract.json', {'kind': 'choose-any.rendering-contract.v1',
        'status': 'AUTHOR_FINAL_REVIEW_REQUIRED_NO_TARGET_CALLS', 'english_mapping_sha256': MAPPING_SHA,
        'spans': spans, 'span_utf8_sha256': SPAN_SHA,
        'substitution': 'Only re.sub(r"\\bS\\b", set_ref, span); preserve all sentences, names, and 1/|set_ref|.',
        'shared_context_addition': DEDUP,
        'shared_context_addition_reason': 'Explicit identity-based deduplication in both arms; no world/member/policy change. Final author must check this exact wording.',
        'neutral_raw_sha256': NEUTRAL_SHA, 'neutral_worlds_sha256': digest(worlds),
        'approved_assignment_sha256': ASSIGNMENT_SHA, 'assignment_seed': 2026091501,
        'panel_seed': instrument.PANEL_SEED, 'target_items_sha256': digest(items),
        'items_with_calibration_sha256': digest(all_items)})
    write('items.json', all_items)
    write('audit-only-counterfactuals.json', {'status': 'AUDIT_ONLY_NOT_ADDITIONAL_SAMPLES', 'items': twins})
    write('reader-config-review.json', spec)
    write('planned-cells.json', {'status': 'FROZEN_DESIGN_NO_INFERENCE', 'cells': cells})
    write('exported-reader-payloads.json', {'status': 'INTERCEPTED_SERIALIZATION_NOT_INFERENCE', 'payloads': exported})
    write('planned-http-requests.json', {'status': 'INTERCEPTED_SERIALIZATION_NOT_INFERENCE', 'payloads': planned_payloads})
    write('unbound-design-preview.json', planned_manifest)
    write('attempt-settings-review.json', settings)
    write('PLANNED-PRECISION.json', boundary)
    structural = {'status': 'FILE_AND_INTERCEPTED_HTTP_CHECKS_PASS_NOT_READER_QUALIFICATION',
        'sdk_version': importlib.metadata.version('ainglish'), 'target_worlds': 144,
        'audit_only_counterfactuals': 288, 'calibration_items': 32,
        'potential_serialized_requests_exported': len(exported),
        'planned_serialized_requests': len(planned_payloads),
        'synthetic_pipeline_target_cells': nreal, 'synthetic_pipeline_calibration_cells': ncal,
        'synthetic_results_discarded_not_evidence': True, 'observed_target_reader_calls': 0,
        'minted_attempts': 0, 'new_qualifications': 0, 'answer_metadata_poisoning_preserves_all_requests': True,
        'old_neutral_questions_menus_and_form_golds_unchanged': True,
        'finite_audit_view_bounds': {a: audit.bound(twins, lambda i: audit.visible(i, a))
                                   for a in ['english', 'ainglish']},
        'unpaired_context_only_bound': audit.bound(items, lambda i: audit.visible(i, 'english')),
        'scope': 'Paired counterfactual view collisions detect direct form leakage, not every exploitable association. Unique unpaired contexts can be memorised; no universal no-leak theorem.'}
    write('STRUCTURAL-AUDIT.json', structural)
    dependencies = [OLD / n for n in ['instrument.py', 'assign_bank.py', 'audit.py', 'report.py',
                                      'neutral-worlds.json']] + [assignment_path]
    write('dependency-hashes.json', {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in dependencies})
    print(json.dumps({'status': structural['status'], 'items_sha256': digest(all_items),
                      'planned_reader_calls': 416, 'actual_target_reader_calls': 0,
                      'conditional_all_correct_lower_pp': {f: boundary['even_if_every_target_answer_were_correct'][f]['lower_delta_pp'] for f in FORMS}}))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--proposal-snapshot', default=str(ROOT / 'source-contract.json'))
    args = ap.parse_args()
    build(args.proposal_snapshot)

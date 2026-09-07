"""Re-derive all planned descriptive slices; no inference or changed scoring."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'overnight-runtime-2026-09-06'))
from runtime import Journal, save_new

def read(name):
    return json.loads((ROOT / name).read_text())

def main():
    attempt = '375ec2a9-5f94-4a18-915f-aa4008857ce2'
    cases = {r['id']: r for r in read('cases.json')}
    path = f'execution/offer.attempt-{attempt}.cells.json'
    envelope = read(path)
    cells = envelope['rows']
    assert len(cells) == 256
    events = Journal._validate((ROOT / 'execution/wire.jsonl').read_text())
    begins = [e['data'] for e in events if e['kind'] == 'begin']
    ends = [e['data'] for e in events if e['kind'] == 'end']
    assert len(begins) == len(ends) == 288
    assert [r['call_id'] for r in begins] == [r['call_id'] for r in ends]
    assert all(a['request_hash'] == b['request_hash'] for a, b in zip(begins, ends))
    assert len({(r['reader'], r['item_id']) for r in cells}) == 256
    groups = defaultdict(list)
    for cell in cells:
        case = cases[cell['item_id']]
        meaning = case['choice_meanings'][cell['answer']]
        assert cell['expected'] == case['answer']
        assert cell['correct'] == (meaning == case['gold'])
        axis = case['asserted_axis']
        row = {'joint_correct': cell['correct'], 'asserted_axis_correct': meaning[axis] == case['gold'][axis],
               'unasserted_axis_invented': None if case['other_revealed'] else meaning[1-axis] != 'not determined'}
        labels = {'form': case['form'], 'domain': case['domain'], 'reader': cell['reader'],
                  'polarity': 'affirmed' if case['affirmed'] else 'negated',
                  'other_axis': 'revealed' if case['other_revealed'] else 'unreported',
                  'form/polarity/information': '/'.join([case['form'], str(int(case['affirmed'])), str(int(case['other_revealed']))]),
                  'domain/form/polarity/information': '/'.join([case['domain'], case['form'], str(int(case['affirmed'])), str(int(case['other_revealed']))])}
        for axis_name, label in labels.items():
            groups[axis_name, label, cell['arm']].append(row)
    summaries = []
    for (axis, label, arm), rows in sorted(groups.items()):
        unknown = [r for r in rows if r['unasserted_axis_invented'] is not None]
        summaries.append({'axis': axis, 'label': label, 'arm': arm, 'calls': len(rows),
            'joint_correct': sum(r['joint_correct'] for r in rows),
            'asserted_axis_correct': sum(r['asserted_axis_correct'] for r in rows),
            'unknown_axis_calls': len(unknown),
            'unknown_axis_inventions': sum(r['unasserted_axis_invented'] for r in unknown)})
    result = read('execution/result.json')
    proposal = read('execution/after.json')
    filed = next(r for r in proposal['measurements'] if r['attempt_id'] == attempt)
    assert filed['attempt']['state'] == 'completed' and filed['evidence_state'] == 'valid'
    assert filed['value'] == result['value'] and filed['manifest_hash'] == filed['attempt']['measurement_ref']
    audit = {'kind': 'ainglish.price-allocation-analysis.v1', 'model_calls_repeated': 0,
        'calls_started_and_finished': 288, 'scientific_calls': 256, 'cases': 128,
        'source_hash': filed['manifest_hash'], 'attempt': attempt, 'filed_value_pp': result['value'],
        'filed_interval_pp': [result['value_lo'], result['value_hi']],
        'filed_strata': result['stratum_results'], 'counts_toward_verdict_at_readback': filed['counts_toward_verdict'],
        'slices': summaries, 'wire_sha256': hashlib.sha256((ROOT / 'execution/wire.jsonl').read_bytes()).hexdigest(),
        'limits': ['Slices are unadjusted descriptive call counts, not separate decisive hypothesis tests.',
          'Random counterbalancing does not guarantee equal arm counts in each fine slice; missing arms are not imputed.',
          'The filed scalar equally weights form strata; these raw descriptive ratios do not replace it.',
          'No bare-wording comparison, direct permission/health question, edit robustness or future trained-model advantage was measured.']}
    save_new(ROOT / 'ANALYSIS.json', audit)
    lines = ['# Price versus availability: qualified original', '',
        f"Filed source `{filed['manifest_hash']}`; completed attempt `{attempt}`.", '',
        'All 128 predeclared cases and 256 target calls are retained, plus 32 passing calibration calls. '
        'There were no absent, unparsed, truncated or uncertain calls and no retries. '
        'The neutral reader qualifications were a separate earlier 56-call screen.', '',
        f"The filed Ainglish-minus-careful-English accuracy difference is **{result['value']:+.3f} percentage points**, "
        f"with the preregistered item-bootstrap interval **[{result['value_lo']:+.4f}, {result['value_hi']:+.4f}]**. "
        'The interval spans both harm and benefit; it does not establish the predicted non-inferiority margin. '
        'It is not evidence that the construct is permanently unsuitable.', '',
        'The equal-form-weighted absolute joint accuracy is 34.69% for Ainglish and 39.71% for careful English. '
        'These low absolute accuracies are important: a clean output channel is not the same as understanding the target. '
        'This is a cold-reading study of two specific current quantized models. English training and tokenizer incumbency '
        'limits future extrapolation but does not erase this current result.', '',
        '| Form | Ainglish joint accuracy | Careful-English joint accuracy | Difference |',
        '|---|---:|---:|---:|']
    for r in result['stratum_results']:
        lines.append(f"|{r['id']}|{r['arms']['ainglish']:.2%}|{r['arms']['english']:.2%}|{r['value']:+.2f} pp|")
    lines += ['', '## Complete descriptive slices', '',
        'Each row below reports actual calls, not an arm-rebalanced population estimate. '
        'The complete fine domain/form/polarity/information cross-product is in ANALYSIS.json, including sparse cells. '
        'Unknown-axis inventions mean choosing yes or no for an axis the record does not settle; hidden world metadata never supplies a reader-visible answer.', '',
        '| Axis | Slice | Arm | Joint correct | Asserted axis correct | Invented unknown axis |',
        '|---|---|---|---:|---:|---:|']
    for r in summaries:
        if r['axis'] == 'domain/form/polarity/information':
            continue
        lines.append(f"|{r['axis']}|{r['label']}|{r['arm']}|{r['joint_correct']}/{r['calls']}|{r['asserted_axis_correct']}/{r['calls']}|{r['unknown_axis_inventions']}/{r['unknown_axis_calls']}|")
    lines += ['', '## What happens next', '',
        'The live readback is valid, awaiting independent replication, and does not yet count toward the verdict. '
        'An independent original or replication must retain the full joint consequence task and honest unknowns. '
        'This original does not complete the proposal’s bare-free gain, permission/health, or editing-robustness predictions. '
        'No vote, rejection, confirmation or full-claim-completion claim was made.', '',
        'Files: frozen cases/items/plan and derived preflight; execution intent and opened/completed attempt; '
        'hash-chained raw calls; SDK cells and measurement; public after-readback; ANALYSIS.json with all diagnostic slices.']
    with (ROOT / 'RESULTS.md').open('x') as out:
        out.write('\n'.join(lines) + '\n')
    print(json.dumps({k: v for k, v in audit.items() if k != 'slices'}, indent=2))

if __name__ == '__main__':
    main()

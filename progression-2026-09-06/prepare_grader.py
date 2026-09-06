"""Fresh full-information original; do not confirm a lossy source's estimand."""
import hashlib
import json
from ainglish import estimand, token_measurement
from since_study import ROOT, save

SUBJECTS = ['The balance checker','The library licence review','The attendance audit','The voltage verifier',
    'The translation evaluator','The risk rating review','The migration checker','The navigation test',
    'The coolant monitor review','The warehouse label audit','The schema validator check','The ranking evaluator',
    'The damage classifier review','The tariff compliance check','The duplicate-image audit','The search relevance test']


def main():
    source = json.loads(next((ROOT/'sources/grader').glob('4c12baf4*.json')).read_text())
    p = json.loads((ROOT/'snapshot/grader.proposal.json').read_text())
    pairs = []
    for i, subject in enumerate(SUBJECTS):
        common = f'Case G96-{i:02}: '
        # Do not add mechanism-specific facts to only the English arm. This is
        # exactly the definition, applied to the same subject in the same force.
        pairs.append({'english':common+subject+' has an evaluator that shares state with the evaluated party; a pass certifies agreement with itself, not correctness.',
            'ainglish':common+subject+' is grader=graded.'})
    old_arms = {r[a] for r in source['manifest']['test_set'] for a in ['english','ainglish']}
    assert not old_arms.intersection(r[a] for r in pairs for a in ['english','ainglish'])
    manifest = {'metric':'token_delta','models':['cl100k_base','o200k_base'],'test_set':pairs,'seed':2026090612,
        'estimand_contract':estimand.declaration(unit_span='one complete scoped statement',
            contrast='The current registered grader=graded definition applied to the same subject; no English-only mechanism, provenance, numbers or facts',
            population='16 prospectively authored complete pairs, one per named subject; not random natural prose',
            reducer='least_favourable',aggregation_rule='Equal pair mean in each cached encoding; maximum tokenizer mean across cl100k_base and o200k_base.'),
        'method':'New original with a narrower complete-information comparison. It does not numerically confirm, retire or overwrite the earlier source 4c12baf4, whose specific mechanism facts were not preserved in its compact arm.',
        'scope':'Literal current-tokenizer cost, not comprehension or future-trained performance. English training/tokenizer advantages remain relevant context.'}
    plan = token_measurement.prepare({'manifest':manifest})
    plan['mint']['admissibility_gates'] += ['Frozen public pairs before any tokenizer count; no downloads, cached encodings only',
        'Fresh visible active proposal and unchanged registered mapping', 'All admitted directions filed; independent settlement still required']
    plan['mint']['planned_sample']['mapping_sha256'] = hashlib.sha256(p['english_mapping'].encode()).hexdigest()
    save('grader.plan.json',plan)
    print('Frozen grader original',plan['manifest_commitment'],'no counts')


if __name__ == '__main__':main()

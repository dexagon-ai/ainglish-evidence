"""Independent finite input/gold checks, not a rescore of missing raw answers."""
from collections import Counter
from fractions import Fraction
import json
import re
import statistics
from since_study import ROOT, save


def main():
    rows = json.loads((ROOT/'new-replications/mean.replication.items.json').read_text())
    checked = []
    for r in rows:
        if r.get('calibration'): continue
        d = r['strata']; probe = d['probe']
        if probe != 'categorical':
            numbers = [Fraction(v.strip()) for v in re.search(r'observations ([^.]+)\.',r['english'])[1].split(',')]
            value = sum(numbers)/len(numbers) if d['form']=='mean-of' else statistics.median(numbers)
            reported = Fraction(d['reported_value'])
            assert value == reported, (r['id'],value,reported)
        if probe == 'above_most': expected = 'yes' if sum(v < reported for v in numbers) > len(numbers)/2 else 'no'
        elif probe == 'observed_centre': expected = 'yes' if reported in numbers else 'no'
        elif probe == 'exact_recheck': expected = 'yes'
        else: expected = 'no'
        assert r['answer'] == expected, (r['id'],expected,r['answer'])
        assert r['english'].split('\nReport:')[0] == r['ainglish'].split('\nReport:')[0]
        checked.append(r['id'])
    parallel = [r for r in json.loads((ROOT/'new-replications/parallel.replication.items.json').read_text()) if not r.get('calibration')]
    for r in parallel:
        assert r['answer'] == ('yes' if r['polarity']=='parallel' else 'no')
        assert r['ainglish'].endswith('in-'+r['polarity']+'.')
        assert r['question'] == 'May the second listed action begin before the first has reached a terminal outcome?'
    assert len(checked) == 160 and len(parallel) == 200
    assert Counter(r['polarity'] for r in parallel)=={'parallel':100,'sequence':100}
    assert set(Counter(r['domain'] for r in parallel).values()) == {50}
    assert set(Counter(r['render_style'] for r in parallel).values()) == {40}
    save('new-replications/gold-audit.json',{'mean_checked':len(checked),'parallel_checked':len(parallel),
        'mean_probes':dict(Counter(r['strata']['probe'] for r in rows if not r.get('calibration'))),
        'boundary':'Arithmetical centres, meaning-matched context and finite stated gold checked. Does not reconstruct actual missing option answers, certify all natural-language interpretations, or declare protocol agreement.'})
    print('Checked 160 mean/median and 200 wait-edge gold rows; no changed keys or scores.')


if __name__ == '__main__':main()

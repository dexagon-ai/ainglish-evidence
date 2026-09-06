"""Audit retained answers and predeclared cluster diagnostics; no reader calls."""
from collections import Counter
from datetime import datetime, timezone
import importlib.util
import json
from ainglish.client import manifest_commitment
from since_study import ROOT, OLD, save


def main():
    module = importlib.util.spec_from_file_location('retained_analysis',OLD/'analyze.py')
    analysis = importlib.util.module_from_spec(module); module.loader.exec_module(analysis)
    result = json.loads((ROOT/'since.careful.result.json').read_text())
    aid = result['attempt_id']
    cells = json.loads((ROOT/f'since.careful.attempt-{aid}.cells.json').read_text())['rows']
    data = json.loads((ROOT/'frozen/since.careful.items.json').read_text())
    items = {r['id']:r for r in data if not r.get('calibration')}
    assert len(cells) == 576 and len({(r['reader'],r['item_id']) for r in cells}) == 576
    for r in cells:
        assert r['expected'] == items[r['item_id']]['answer']
        assert r['correct'] == (r['answer'].upper() == r['expected'])
    weights = {s['id']:s['weight'] for s in result['manifest']['settlement_strata']}
    study = {'items':items,'cells':cells,'weights':weights}
    recomputed = analysis.weighted(cells,items,weights)
    assert abs(recomputed['value']-result['value']) < .011
    server = json.loads((ROOT/'since.careful.server.json').read_text())
    assert server['state'] == 'completed'
    assert manifest_commitment(result['manifest']) == server['pin']['manifest_commitment']
    controls = {r['id']:r for r in data if r.get('calibration')}
    control_cells = json.loads((ROOT/f'since.careful.attempt-{aid}.calibration.cells.json').read_text())['rows']
    accuracy = {}
    for reader in {r['reader'] for r in control_cells}:
        accuracy[reader] = {}
        for arm, truth in [('ainglish','detectable'),('english','other')]:
            subset = [r for r in control_cells if r['reader'] == reader and r['arm'] == arm]
            accuracy[reader][arm] = sum(r['answer'].upper() == controls[r['item_id']]['calibration_truth'][truth] for r in subset)/len(subset)
    axes = {}
    for condition in weights:
        axes[condition] = {}
        for arm in ['english','ainglish']:
            counts = Counter()
            for cell in cells:
                item = items[cell['item_id']]
                if item['settlement_stratum'] != condition or cell['arm'] != arm:
                    continue
                meaning = item['strata']['answer_options'][cell['answer'].upper()]
                bits = [part.strip().split(': ')[1] == 'yes' for part in meaning.split(';')]
                if not item['ledger']['reason_first']: bits.reverse()
                counts['cells'] += 1
                counts['reason_errors'] += bits[0] != item['ledger']['reason_asserted']
                counts['interval_errors'] += bits[1] != item['ledger']['interval_asserted']
            axes[condition][arm] = dict(counts)
    report = {'at':datetime.now(timezone.utc).isoformat(), 'attempt_id':aid,'manifest_hash':manifest_commitment(result['manifest']),
        'filed_value_pp':result['value'],'filed_interval_pp':[result['value_lo'],result['value_hi']],
        'filed_arms':result['arms'],'conditions':result['stratum_results'],'reader_results':result['per_member'],
        'recomputed':recomputed,'cluster_diagnostic':analysis.bootstrap([study]),'axis_errors':axes,
        'control_semantic_accuracy':accuracy,'raw_wire_outputs':sum(1 for _ in (ROOT/'raw-reader-outputs.jsonl').open()),
        'resample_down':result['resample_down'],
        'warning':'SDK half-sample sensitivity warning is retained. The raw adverse interval is not a claim of resolved evidence. Both arms have low exact two-axis recovery; a failure may include the compound question format. No model/arm inference was rerun.',
        'scope':'Fixed authored frames and two current readers; partial declared plan, not humans, full-contract completion or future Ainglish-trained performance.'}
    assert report['raw_wire_outputs'] == 624
    save('since.analysis.json',report)
    print(json.dumps({k:report[k] for k in ['manifest_hash','filed_value_pp','filed_interval_pp','filed_arms','cluster_diagnostic','control_semantic_accuracy']},indent=2))


if __name__ == '__main__':main()

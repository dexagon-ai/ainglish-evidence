"""Verify public inputs and retained correctness attestations, never invent raw output."""
from collections import Counter, defaultdict
import json
from pathlib import Path
from ainglish import panel
from since_study import ROOT, save


def weighted(row):
    attestation = row['interval_provenance_attestation']
    index = {r['id']:r['stratum'] for r in attestation['items']}
    counts = defaultdict(lambda:[0,0])
    for c in attestation['cells']:
        k = (index[c['item_id']],c['arm'])
        counts[k][0] += c['correct']; counts[k][1] += 1
    weights = {s['id']:s['weight'] for s in row['manifest']['settlement_strata']}
    arms = {a:sum(w*counts[s,a][0]/counts[s,a][1] for s,w in weights.items())/sum(weights.values()) for a in ['english','ainglish']}
    return {'arms':arms,'value':100*(arms['ainglish']-arms['english']), 'counts':{s:{a:counts[s,a] for a in ['english','ainglish']} for s in weights}}


def main():
    reports = {}
    for name in ['mean','parallel']:
        rows, inputs = {}, {}
        for role in ['original','replication']:
            row = json.loads((ROOT/f'new-replications/{name}.{role}.json').read_text())
            rows[role] = row
            items, digest = panel.fetch_items(row['manifest']['items_url'],row['manifest']['items_sha256'])
            save(f'new-replications/{name}.{role}.items.json',items)
            inputs[role] = [r for r in items if not r.get('calibration')]
            result = weighted(row)
            assert abs(result['value']-row['value']) < .011
            assert all(abs(result['arms'][a]-row['arms'][a]) < .00011 for a in result['arms'])
            assert len(row['interval_provenance_attestation']['cells']) == len(inputs[role])*2
            attested = {r['id'] for r in row['interval_provenance_attestation']['items']}
            assert attested == {r['id'] for r in inputs[role]}
            reports[name+'.'+role] = {'attempt_id':row['attempt_id'],'manifest_hash':row['manifest_hash'],
                'items_url':row['manifest']['items_url'],'items_sha256':digest,'items':len(inputs[role]),
                'recomputed_from_submitted_correctness':result,
                'raw_answer_boundary':'The public bootstrap attestation retains correct/incorrect flags, not raw reader text or actual option answers. It supports arithmetic re-derivation, not independent rescoring.'}
        pairs = lambda xs:{(r['english'],r['ainglish']) for r in xs}
        arms = lambda xs:{r[a] for r in xs for a in ['english','ainglish']}
        overlap = {'complete_pairs':len(pairs(inputs['original'])&pairs(inputs['replication'])),
                   'individual_arms':len(arms(inputs['original'])&arms(inputs['replication']))}
        assert overlap == {'complete_pairs':0,'individual_arms':0}
        reports[name+'.comparison'] = {'original':rows['original']['manifest_hash'],
            'replication':rows['replication']['manifest_hash'], 'overlap':overlap,
            'protocol_comparison':rows['replication']['replication_comparison'],
            'qualification_boundary':'Replication manifest does not attach source qualification receipts; no claim that a public raw-call journal was audited.'}
    save('new-replications/arithmetic-and-identity-audit.json',reports)
    print(json.dumps({k:{x:v[x] for x in ['items','recomputed_from_submitted_correctness'] if x in v} for k,v in reports.items()},indent=2))


if __name__ == '__main__':
    main()

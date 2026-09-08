"""Recount already-filed public inputs. This is not a new measurement or replication."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from ainglish import token_measurement
from local_colony_auth import ainglish_client

ROOT = Path(__file__).resolve().parent / 'source-audit'
ROOT.mkdir(exist_ok=True)
c = ainglish_client()
targets = {
    'interval-endpoints': 'e5274f09c6700c8ce9d3908908f8472353bbf5abf308ef62bdcbbe0f08449b1c',
    'outcome-compact-confirmation': '1e8222d512a2c0fda9cf4f483ef5e7be3f55e6f450fa13845147672c6f566f58',
    'replacement-cost': 'e2ff808e72df863f2c403344843ac1f8e81cd6ae3b55ed3150e05ff922de5842',
    'postpone-cost': '731894e988bbb6a473703d55ba259d137fe53ace009c7e792345edd2e036161a',
    'replied-no-original': '69debfe93b28a7062486f4b8cfc7311c3e21fba9b99217347fa300ad24493e30',
    'replied-no-replica': 'fc91e45de176720265baf3e5fe6fe3d8895015c7d8ca00a9e636c48332738b10',
}
audits = []
rows = {}
for name, target in targets.items():
    path = ROOT / (name + '.json')
    if path.exists():
        row = json.loads(path.read_text())
        assert row['manifest_hash'] == target
    else:
        row = c.measurement(target)
        with path.open('x') as f:
            json.dump(row, f, indent=2, ensure_ascii=False)
    rows[name] = row
    payload = {k: row[k] for k in ['metric', 'manifest', 'value', 'value_lo', 'value_hi', 'panel_models', 'per_member', 'stratum_results', 'replicates_hash'] if row.get(k) is not None}
    # API envelopes can expose a null optional field; the canonical submission omits it.
    if row['manifest'].get('replicates_hash'):
        payload['replicates_hash'] = row['manifest']['replicates_hash']
    if 'stratum_results' in payload:
        payload['stratum_results'] = [{k: s[k] for k in ['id', 'value', 'value_lo', 'value_hi', 'arms'] if k in s}
                                     for s in payload['stratum_results']]
    receipt = token_measurement.verify_payload(payload)
    audits.append({'label': name, 'manifest_hash': target, 'verification': receipt,
                   'per_member': row['per_member'], 'confirmed': row['confirmed'],
                   'evidence_state': row.get('evidence_state', 'valid'),
                   'settlement_eligible': row.get('settlement_eligible'),
                   'reproduced_ok': row.get('reproduced_ok'),
                   'strata_pair_counts': dict(Counter(x.get('stratum', 'unstratified') for x in row['manifest']['test_set']))})
    print(name, receipt['pair_count'], receipt['headline_value'], 'exact recount', flush=True)

def fingerprints(row):
    return {hashlib.sha256(json.dumps([i['english'], i['ainglish']], ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
            for i in row['manifest']['test_set']}

original, replica = rows['replied-no-original'], rows['replied-no-replica']
report = {'at': datetime.now(timezone.utc).isoformat(), 'audits': audits,
          'replied_no': {'source_replica_complete_pair_overlap': len(fingerprints(original) & fingerprints(replica)),
                         'declared_allowance': 3, 'original': original['value'], 'replica': replica['value'],
                         'both_above_allowance': original['value'] > 3 and replica['value'] > 3,
                         'chronology_scope': 'Pair novelty relative to the cited original is verified. This alone cannot establish novelty relative to the replicator’s own prior exploratory corpus; a retained freeze/mint/encoding chronology was requested.'},
          'limits': 'Reproducibility/source-integrity audit on already exposed inputs, no new attempt or inference. API-only count/weight metadata is removed from the verification input while retained verbatim in each public source snapshot; numeric submission fields are unchanged. Numerical correctness is not semantic equivalence, independence, or a general-language finding. No historic result or evidence state is changed by this file.'}
with (ROOT / 'report.json').open('x') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

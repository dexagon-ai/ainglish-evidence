"""A source-row census. Never count held or different-estimand rows as disagreements."""
from collections import Counter
from datetime import datetime, timezone
import json
from local_colony_auth import ainglish_client
from snapshot import ROOT, cached, save


def classify(row):
    comparison = row.get('replication_comparison') or {}
    if row.get('voided_at') or row.get('retraction'):
        return 'retracted'
    if row.get('evidence_state') not in (None, 'valid'):
        return 'inactive_evidence'
    if comparison.get('distinct') or comparison.get('governance_effect') == 'distinct_estimand':
        return 'different_estimand'
    if comparison.get('held') or comparison.get('commensurability', {}).get('held_on'):
        return 'comparison_hold'
    if row.get('settlement_eligible') is True:
        if row.get('reproduced_ok') is True:
            return 'eligible_agreement'
        if row.get('reproduced_ok') is False:
            return 'eligible_disagreement'
        return 'eligible_outcome_not_recorded'
    if row.get('settlement_eligible') is False:
        return 'non_counting_replication'
    return 'eligibility_not_recorded'


def main():
    client = ainglish_client()
    pages = cached('census/replication-pages.json', lambda: list(client.measurement_pages(role='replication', page_size=200)))
    rows = [row for page in pages for row in page['measurements']]
    assert len({r['attempt_id'] for r in rows}) == len(rows)
    findings = []
    for row in rows:
        comparison = row.get('replication_comparison') or {}
        findings.append({'attempt_id': row['attempt_id'], 'manifest_hash': row['manifest_hash'],
            'target_hash': row.get('replicates_hash'), 'metric': row['metric'],
            'classification': classify(row), 'reproduced_ok': row.get('reproduced_ok'),
            'counts_toward_verdict': row.get('counts_toward_verdict'),
            'reported_value': row['value'], 'floor_cells': row.get('floor_cells'),
            'comparison': comparison, 'source_url': row['url']})
    result = {'at': datetime.now(timezone.utc).isoformat(), 'source': '/api/v1/measurements?role=replication',
        'sweep': pages[0]['sweep'], 'rows': len(rows), 'counts': dict(Counter(r['classification'] for r in findings)),
        'interpretation': 'Current server receipts, not an independent reimplementation of settlement. Attempt ids identify rows; hashes may be shared. Missing eligibility is unknown. A reported value mismatch is not itself an eligible disagreement. No historical population is silently substituted for this dated sweep.',
        'records': findings}
    save('census/RECONCILIATION.json', result)
    print(json.dumps({'rows': result['rows'], 'counts': result['counts']}))


if __name__ == '__main__': main()

"""Freeze a content-matched, concise-English cost original; no tokenizer calls."""
import json
from pathlib import Path
from ainglish import estimand, token_measurement

ROOT = Path(__file__).resolve().parent
FRAMES = [('smoke suite', 'deployment'), ('signature check', 'release bundle'),
          ('inventory audit', 'stock ledger'), ('schema validator', 'export file'),
          ('sensor check', 'temperature probe'), ('permission test', 'access rule'),
          ('replica monitor', 'archive mirror'), ('balance check', 'payment batch')]

def save(name, value):
    with (ROOT / name).open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False); f.write('\n')

def main():
    rows = []
    for i in range(32):
        check, target = FRAMES[i % 8]
        prefix = f'Scheduled {check} on {target} R{6300+i}: '
        for form, english in [('verdict-fail', 'completed; judged the target defective'),
                              ('no-verdict', 'no target judgment')]:
            rows.append({'english': prefix + english + '.', 'ainglish': prefix + form + '.', 'stratum': form})
    assert len(rows) == len({(r['english'], r['ainglish']) for r in rows}) == 64
    declaration = estimand.declaration(
        unit_span='one complete scheduled-check status report',
        contrast='Registered outcome tag minus concise disambiguated English in the same check/target context; no bare failed arm and no explanation only on the marked side',
        population='64 new status reports, 32 per tag; eight check/target frames each repeated in four named records; template population, not arbitrary human prose',
        reducer='least_favourable',
        aggregation_rule='For each reference encoding, equal-weight means of the two form strata; headline is maximum tokenizer mean; bounds are member-span, not a confidence interval')
    spec = {'manifest': {'metric': 'token_delta', 'models': ['cl100k_base', 'o200k_base', 'p50k_base'],
        'test_set': rows, 'seed': 2026090531, 'estimand_contract': declaration,
        'settlement_strata': [{'id': x, 'weight': 1} for x in ['verdict-fail', 'no-verdict']],
        'method': 'New original. Canonical SDK prepare, preflight, mint before encoding, run_prepared, verify, measure. Exact common context is unchanged between arms; complete concise outcome phrases replace the tags.',
        'comparator_genre': 'complete-concise-status-english-v1',
        'semantic_audit': 'verdict-fail reports a completed check judgment of target defect, not a guarantee the check is correct. no target judgment says neither that the target passed nor why the scheduled check failed to judge. Check and target are named identically in both arms. No extra diagnostic explanation appears in either arm.',
        'scope': 'Current-tokenizer cost only. This is not comprehension, future-trained efficiency, a replication of invalid originals, or a correction carrying another attempt identity.'}}
    plan = token_measurement.prepare(spec)
    plan['mint']['admissibility_gates'] += [
        'fresh proposal remains active and token prerequisite requires an original',
        'cached encodings only; no model or tokenizer download',
        'freeze all 64 pairs and form weights before mint; no outcome-driven rewrite or sample selection',
        'file every finite direction, including failure of the <=2 prerequisite; original is not independent confirmation']
    assert len(json.dumps(plan['manifest'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()) <= 20000
    save('verdict-token.spec.json', spec); save('verdict-token.plan.json', plan)
    print(plan['manifest_commitment'], plan['pair_count'], 'prepared; no token counts')

if __name__ == '__main__':
    main()

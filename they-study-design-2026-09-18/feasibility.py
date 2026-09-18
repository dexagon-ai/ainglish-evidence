"""Numeric-only commitment and feasibility campaign; never calls a reader/API."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'decision-and-design-2026-09-16'


def cdf(k, n, p):
    if k < 0: return 0.0
    if k >= n: return 1.0
    if p == 0: return 1.0
    if p == 1: return 0.0
    return min(1.0, math.fsum(math.exp(math.lgamma(n+1)-math.lgamma(i+1)-math.lgamma(n-i+1)
                                    + i*math.log(p)+(n-i)*math.log1p(-p)) for i in range(k+1)))


def diagnostics():
    rows = []
    # This is a conservative all-reader-pass diagnostic, NOT power for the
    # averaged-bound decision in PLAN.md. That distinction is retained on wire.
    for n in (128, 512, 1024):
        for ceiling in (.05, .10):
            allowed = [k for k in range(n+1) if cdf(k, n, ceiling) <= .025]
            cutoff = max(allowed, default=-1)
            for rate in (0, .01, .025, .05, .07, .10):
                power = cdf(cutoff, n, rate)
                rows.append({'worlds_per_endpoint': n, 'error_ceiling': ceiling,
                             'per_reader_alpha': .025, 'max_errors_passing_per_reader_bound': cutoff,
                             'synthetic_true_error_rate_per_reader': rate,
                             'one_reader_bound_pass_probability': power,
                             'two_readers_both_pass_lower_bound_without_reader_independence': max(0, 2*power-1),
                             'ten_endpoints_all_twenty_reader_bounds_pass_lower_bound': max(0, 1-20*(1-power))})
    return {'method': 'Binomial CDF, log-gamma finite sum; one-sided exact per-reader bound inversion.',
            'scope': 'Synthetic per-reader sufficient-condition diagnostic, not exact power of averaged bounds, full study or language performance.',
            'rows': rows}


def plan():
    ledger = {'explicit_controls': 2560, 'core_cad': 4096, 'paired_accuracy_safety': 4096,
              'paired_nonclaims': 20480, 'bare_descriptive': 512, 'official_calibration': 64}
    return {'state': 'REVIEW_CANDIDATE_NO_TARGET_BANK_OR_EXECUTION', 'model_calls': 0,
            'candidate_worlds_per_form': 1024, 'scenario_count': 12, 'synthetic_pairs_per_case': 1000,
            'source_sha256': {n: hashlib.sha256((SOURCE/n).read_bytes()).hexdigest()
                              for n in ('bootstrap_oc.cpp', 'prepare_bootstrap.py')},
            'model_call_envelope_per_study': ledger, 'maximum_per_study': sum(ledger.values()),
            'original_and_replica_maximum': 2*sum(ledger.values()),
            'qualification_included': False, 'target_bank_created': False, 'reader_seats_accepted': False,
            'protocol_operative': False, 'stop': 'No language execution until independent author/design/protocol/resource decisions are complete.'}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('command', choices=['prepare', 'run'])
    ap.add_argument('--work', type=Path, required=True); args = ap.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    if args.command == 'prepare':
        (ROOT/'design.json').write_text(json.dumps(plan(), indent=2)+'\n')
        print('Review candidate written; commit this source and plan before running.')
        return
    frozen = json.loads((ROOT/'design.json').read_text())
    assert frozen == plan(), 'design/source changed after freeze'
    start = datetime.now(timezone.utc).isoformat()
    binary = args.work/'bootstrap_oc'
    subprocess.run(['g++', '-O3', '-std=c++17', str(SOURCE/'bootstrap_oc.cpp'), '-o', str(binary)], check=True)
    subprocess.run([sys.executable, str(SOURCE/'prepare_bootstrap.py'), '--output', str(args.work/'matrices'), '--sizes', '1024'], check=True)
    cmd = [str(binary), str(args.work/'matrices/matrix-n1024-run0.bin'), str(args.work/'matrices/matrix-n1024-run1.bin'), '1000', 'all']
    with (ROOT/'cad-n1024.csv').open('x') as out:
        run = subprocess.Popen(cmd, text=True, stdout=subprocess.PIPE)
        for line in run.stdout:
            out.write(line); out.flush()
            print(line.strip(), flush=True)
        if run.wait() != 0: raise RuntimeError('numeric campaign failed; partial output retained')
    (ROOT/'auxiliary-binomial-diagnostics.json').write_text(json.dumps(diagnostics(), indent=2)+'\n')
    (ROOT/'execution.json').write_text(json.dumps({'began_at': start, 'completed_at': datetime.now(timezone.utc).isoformat(),
        'python': sys.version, 'matrix_receipts': json.loads((args.work/'matrices/matrix-receipts.json').read_text()),
        'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(), 'model_calls': 0}, indent=2)+'\n')


if __name__ == '__main__': main()

"""Run the prespecified synthetic sensitivity grid with three CPU processes at most."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

WORK = Path(sys.argv[1]).resolve()
SOURCE = Path(__file__).resolve().parent
SIZES = (300, 600, 1200)
TRIALS = 1000


def run(n):
    command = [str(WORK / 'bootstrap_oc'),
               str(WORK / 'matrices' / f'matrix-n{n}-run0.bin'),
               str(WORK / 'matrices' / f'matrix-n{n}-run1.bin'), str(TRIALS), 'all']
    lines = []
    process = subprocess.Popen(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in process.stdout:
        lines.append(line)
        if not line.startswith('scenario,'):
            print(json.dumps({'finished_case': line.split(',')[0], 'worlds_per_form': n}), flush=True)
    error = process.stderr.read()
    code = process.wait()
    if code != 0:
        raise RuntimeError(f'Native simulation n={n} failed: {error[:500]}')
    (WORK / f'oc-n{n}.csv').write_text(''.join(lines))
    return n


design = {
    'kind': 'synthetic-operating-characteristic-design-v1',
    'created_before_grid_execution': datetime.now(timezone.utc).isoformat(),
    'not_a_language_preregistration': True, 'model_calls': 0,
    'sizes_worlds_per_form': SIZES, 'forms': 2, 'readers': 2, 'bootstrap_draws': 2000,
    'simulation_pairs_per_case': TRIALS, 'scenario_count': 12, 'cpu_process_limit': 3,
    'methods': 'Actual SDK SHA counter draws; current pooled estimator; proposed common-mask per-form quantiles; marginal intervals only.',
    'interval_reporting': 'Half-away-from-zero at four decimal places for decisions, overlap and coverage. Raw quantiles retained for SDK parity tests. Coverage allows 1e-10 percentage points for floating-point representation only.',
    'correction_before_publication': 'An initial internal run accumulated expected cell probabilities, causing false coverage failures at the zero estimand. Replaced with exact homogeneous probabilities or analytic allocation-weighted reader means, added zero-truth/perfect-guard tests, and reran the entire unchanged scenario grid. No target inference occurred.',
    'scenario_definition': 'The complete fixed list and RNG streams are in bootstrap_oc.cpp.',
    'scope': 'CAD preservation and interval intersection only. Does not simulate token benefit, qualification, author auxiliary safety endpoints, human validity or actual ratification.',
    'stop_rule': 'Complete every named case with the same 1,000 study pairs; no outcome-based enlargement or selective case omission.',
    'source_sha256': {name: hashlib.sha256((SOURCE / name).read_bytes()).hexdigest()
                      for name in ('bootstrap_oc.cpp', 'prepare_bootstrap.py', 'run_oc.py')},
}
(WORK / 'oc-design.json').write_text(json.dumps(design, indent=2) + '\n')
with ThreadPoolExecutor(max_workers=3) as pool:
    for result in as_completed([pool.submit(run, n) for n in SIZES]):
        print(json.dumps({'completed_size': result.result()}), flush=True)

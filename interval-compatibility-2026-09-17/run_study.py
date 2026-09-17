"""Run all prespecified CPU-only cases; preserve complete per-size logs."""
import argparse
import csv
from datetime import datetime,timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--build',type=Path,required=True)
    args=parser.parse_args();build=args.build.resolve();output=HERE/'results'
    if output.exists():raise SystemExit('Refusing to overwrite an existing campaign.')
    # Ensure the experiment source/plan are committed before the first trial.
    subprocess.run(['git','diff','--exit-code','HEAD','--',str(HERE)],check=True,stdout=subprocess.DEVNULL)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    source_files=[HERE/'PLAN.md',HERE/'compatibility.cpp',HERE/'test_compatibility.py',HERE/'run_study.py',
                  HERE.parent/'decision-and-design-2026-09-16/bootstrap_oc.cpp',
                  HERE.parent/'decision-and-design-2026-09-16/prepare_bootstrap.py']
    plan=subprocess.check_output([str(build/'compatibility'),'--plan'],text=True)
    matrix_receipts=json.loads((build/'matrices/matrix-receipts.json').read_text())
    for r in matrix_receipts['matrices']:
        assert sha(build/f"matrices/matrix-n{r['n_worlds_per_form']}-run{r['run']}.bin")==r['sha256']
    output.mkdir()
    design={'kind':'ainglish.numeric-compatibility-sensitivity.v1','started_at':datetime.now(timezone.utc).isoformat(),
            'source_commit':commit,'source_sha256':{str(f.relative_to(HERE.parent)):sha(f) for f in source_files},
            'binary_sha256':sha(build/'compatibility'),'compiler':subprocess.check_output(['g++','--version'],text=True).splitlines()[0],
            'sizes':[32,128,512],'trials_per_case':500,'cases':list(csv.DictReader(io.StringIO(plan))),
            'matrix_receipts':matrix_receipts,'reader_calls':0,'formal_governance_measurement':False}
    (output/'design.json').write_text(json.dumps(design,indent=2)+'\n')
    rows=[]
    for n in design['sizes']:
        path=output/f'compatibility-n{n}.csv'
        with path.open('w') as out,(output/f'compatibility-n{n}.stderr.txt').open('w') as err:
            subprocess.run([str(build/'compatibility'),str(build/f'matrices/matrix-n{n}-run0.bin'),
                            str(build/f'matrices/matrix-n{n}-run1.bin'),'500','all'],stdout=out,stderr=err,check=True)
        parsed=list(csv.DictReader(path.open()))
        assert len(parsed)==12 and [x['case'] for x in parsed]==[x['case'] for x in design['cases']]
        rows.extend(parsed);print('Completed',n,'all 12 cases',flush=True)
    (output/'all-cases.json').write_text(json.dumps(rows,indent=2)+'\n')
    receipt={'completed_at':datetime.now(timezone.utc).isoformat(),'cases':len(rows),
             'simulated_pairs':len(rows)*500,'reader_calls':0,'source_commit':commit,
             'csv_sha256':{f.name:sha(f) for f in output.glob('*.csv')}}
    (output/'completion.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)


if __name__=='__main__':main()

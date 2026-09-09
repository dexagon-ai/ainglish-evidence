"""Mint once, run a source-specific causal regression, retain and submit its outcome."""
import hashlib,json,os,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from local_colony_auth import ainglish_client,colony_client

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'retirement'
REPO=ROOT.parent
WEB=Path('/home/dexagon/codex/worktrees/web-retirement-audit-20260909')
VENDOR=Path('/home/dexagon/codex/worktrees/web-cost-settlement-20260908/vendor')
DEPLOY='ddaeda4728bb96587a8e672641163d08d4049fdb'
SLUG='author-retirement-close-an-unratified-language-version-2'
PID='a-b5zwpb706751xmby'
DATABASE='ainglish_retirement_20260909_9e3f'

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False)
def command(args,cwd=WEB):
    return subprocess.run(args,cwd=cwd,text=True,capture_output=True,timeout=600)
def git(*args):
    r=command(['git',*args],REPO);r.check_returncode();return r.stdout.strip()
def docker(*cmd,db=False):
    args=['docker','run','--rm','--user',f'{os.getuid()}:{os.getgid()}',
        '--network','ainglish-symfony-workbench_default' if db else 'none',
        '-v',f'{WEB}:/app','-v',f'{VENDOR}:/app/vendor:ro',
        '-v',f'{ROOT}:/evidence:ro','-w','/app','-e','APP_ENV=test']
    if db:args+=['-e',f'DATABASE_URL=mysql://aing:aing@db:3306/{DATABASE}?serverVersion=mariadb-10.6.27&charset=utf8mb4']
    return command(args+['agent-museum-php:latest',*cmd])

def prepare():
    census=read(OUT/'input-census.json');boundary=read(OUT/'source-boundary.json')
    manifest={'kind':'ainglish.retirement-causal-regression.v1','metric':'unclaimed_verdict_flips',
        'models':['retirement-causal-guard-audit-v1'],'formula_version':1,
        'against':{'repository':'ai-nglish/ainglish-symfony','implementation':boundary['implementation'],
            'current_deployment':DEPLOY,'input_census_sha256':sha(OUT/'input-census.json'),
            'source_boundary_sha256':sha(OUT/'source-boundary.json'),
            'runner_commit':git('rev-parse','HEAD'),
            'runner_path':ROOT.name+'/retirement_run.py','probe_path':ROOT.name+'/retirement_probe.php',
            'probe_sha256':sha(ROOT/'retirement_probe.php'),'runner_sha256':sha(ROOT/'retirement_run.py')},
        'computed_at':census['captured_at'],
        'claimed_moves':[],
        'method':'Count every changed stage produced by the actual deployed assess implementation versus an exact controlled reversion of only the withdrawn guard, on the frozen complete public proposal census. Non-withdrawn rows have byte-identical execution by the pinned source proof; execute both actual PHP variants for every withdrawn row using its public confirmed effective measurements. Positive controls inject confirmed loss and support into synthetic withdrawn cases, outside the live denominator, and must show non-zero divergence. A no-evidence control must show zero. Do not substitute stable post-deploy snapshots for a causal comparison.',
        'scope':'Live deployment/reassessment guard only. Supplementary active-mode endpoint tests separately check authorisation, protected stages, preserved records, retry, public rendering and later evidence. No activation or release is authorised by this measurement.',
        'supplementary_tests':['tests/ProposalRetirementTest.php','tests/LifecycleWithdrawalPresentationTest.php'],
        'admissibility_gates':['Current exact source, target and deployment must match; all public census records are retained, not just selected row classes.',
            'Probe, census, source-boundary and runner bytes must match their pre-mint public commitments.',
            'The source-boundary proof and both planted non-zero controls must work; a failed instrument is an evidenced abort, never a zero.',
            'The isolated endpoint suite must execute assertions without a protected-class regression; any failure is preserved as an abort with full output and must be investigated before activation.',
            'File the one finite live flip count unchanged, including nonzero; no reruns selected by result.'],
        'planned_sample':{'public_proposals':len(census['records']),'row_classes':census['row_class_counts'],
            'public_withdrawn_cases':len(census['withdrawn_details']),'synthetic_controls_excluded':3,
            'counterfactual_arms':2,'supplementary_test_files':2,'reader_calls':0}}
    save(OUT/'planned-manifest.json',manifest)
    print('Prepared manifest; no test or causal outcome run.')

def run():
    execution=OUT/'execution'
    if execution.exists():raise RuntimeError('Prior execution exists; inspect/reconcile, never rerun')
    m=read(OUT/'planned-manifest.json');a=m['against']
    assert sha(OUT/'input-census.json')==a['input_census_sha256']
    assert sha(OUT/'source-boundary.json')==a['source_boundary_sha256']
    assert sha(ROOT/'retirement_probe.php')==a['probe_sha256'] and sha(ROOT/'retirement_run.py')==a['runner_sha256']
    assert sha(WEB/'src/Service/MeasurementService.php')==read(OUT/'source-boundary.json')['current_measurement_service_sha256']
    assert not git('status','--porcelain','--',ROOT.name), 'Public freeze must be committed'
    c=ainglish_client();c.whoami();c.suggestions(proposal=PID,domain='protocols')
    p=c.proposal(SLUG,authenticated=True)
    assert p['public_id']==PID and p['stage']=='seconded' and not p['measurements']
    assert c.health()['deployment']['commit']==DEPLOY
    colony_client().get_all_comments(p['colony_thread_url'].rstrip('/').split('/')[-1])
    mint={'estimand':'Count unclaimed live stage changes caused specifically by the deployed withdrawn reassessment guard, over the complete frozen public register/open/history population; synthetic sensitivity controls are excluded.',
        'admissibility_gates':m['admissibility_gates'],'planned_sample':m['planned_sample'],'proposal_revision':SLUG}
    save(execution/'preflight.json',c.preflight_attempt(SLUG,m,**mint))
    opened=c.mint_attempt(SLUG,m,**mint);save(execution/'attempt.json',opened)
    attempt=opened['attempt']['attempt_id']
    try:
        for path in m['supplementary_tests']:
            # The named DB is exclusively created for this experiment. Never use
            # a shared ainglish_test database: these tests clear their fixtures.
            result=docker('php','vendor/bin/phpunit',path,db=True)
            save(execution/(Path(path).stem+'.json'),{'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
            result.check_returncode()
        result=docker('php','/evidence/retirement_probe.php','/app','/evidence/retirement/input-census.json')
        save(execution/'probe-process.json',{'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        result.check_returncode();outcome=json.loads(result.stdout)
        save(execution/'causal-result.json',outcome)
        payload={'metric':'unclaimed_verdict_flips','value':outcome['value'],'manifest':m,
            'panel_models':m['models'],'panel_neff':1,'attempt_id':attempt}
        save(execution/'measurement-payload.json',payload)
        receipt=c.measure(SLUG,payload);save(execution/'measurement-receipt.json',receipt)
        print('FILED',outcome['value'],'on',outcome['domain_count'],'public rows; independent confirmation still required.',flush=True)
    except Exception as exc:
        save(execution/'failure.json',{'type':type(exc).__name__,'message':str(exc)})
        state=c.attempt(attempt)
        if state.get('state')=='open':
            evidence={'kind':'ainglish.retirement-regression-failure.v1','failure_type':type(exc).__name__,
                'message':str(exc),'retained_files':{p.name:sha(p) for p in execution.glob('*.json')}}
            save(execution/'abort.json',c.abort_attempt(attempt,'Retirement audit prerequisite or instrument failed; inspect retained output',evidence,failed_gate_kind='harness_error'))
        raise

if __name__=='__main__':
    {'prepare':prepare,'run':run}[sys.argv[1]]()

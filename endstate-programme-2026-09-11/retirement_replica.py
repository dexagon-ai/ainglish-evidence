"""Portable, fail-closed retirement replication. Freeze before any causal test.

Uses the executor's own client factory. Never provisions a database or downloads
dependencies. The original author cannot use this runner to confirm their row.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlparse

TARGET = '06abccd00e91728cda103b2a8b7d84499dc89eaf8f8292384fe87b7d4966c23e'
PID = 'a-b5zwpb706751xmby'
SLUG = 'author-retirement-close-an-unratified-language-version-2'
IMPLEMENTATION = 'dcccabf25a7fcc3c2161ba1e1ba47c50ed1efdb3'
SOURCE_PATH = 'src/Service/MeasurementService.php'
OLD = 'if (!$p->isPublished()) {'
NEW = "if (!$p->isPublished() || $p->stage === 'withdrawn') {"
HERE = Path(__file__).resolve().parent
ESTIMAND = ('Count unclaimed live stage changes caused specifically by the deployed '
            'withdrawn reassessment guard, over the complete frozen public register/open/history '
            'population; synthetic sensitivity controls are excluded.')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def read(path):
    return json.loads(path.read_text())


def factory(spec):
    module, separator, name = spec.partition(':')
    if not separator or not module or not name or '.' in name:
        raise ValueError('Choose your own importable_module:client_factory; never supply a credential')
    return getattr(importlib.import_module(module), name)()


def method(text):
    match = re.search(r'(?ms)^    public function assess\(Proposal \$p\): void\n.*?(?=^    /\*\*)', text)
    if not match:
        raise ValueError('Cannot isolate the exact causal method')
    return match.group()


def git(checkout, *args):
    return subprocess.check_output(['git', '-C', str(checkout), *args], text=True,
                                   stderr=subprocess.PIPE).strip()


def source_boundary(checkout, deployment):
    def show(ref):
        # git() removes only final whitespace, outside this isolated method.
        return git(checkout, 'show', ref + ':' + SOURCE_PATH)
    before, after, current = [method(show(r)) for r in [IMPLEMENTATION+'^1', IMPLEMENTATION, deployment]]
    if before.count(OLD) != 1 or after.count(NEW) != 1 or before.replace(OLD, NEW) != after or current != after:
        raise ValueError('Causal method has drifted; do not reuse this instrument')
    if method((checkout/SOURCE_PATH).read_text()) != current:
        raise ValueError('Working source differs from the deployed causal method')
    if git(checkout, 'rev-parse', 'HEAD') != deployment:
        raise ValueError('Use a checkout of the exact deployed commit, not a pending branch')
    if git(checkout, 'status', '--porcelain', '--', 'src', 'tests', 'config', 'composer.lock'):
        raise ValueError('Source/test payload must be clean before freezing')
    return {'implementation': IMPLEMENTATION, 'parent': git(checkout, 'rev-parse', IMPLEMENTATION+'^1'),
            'current_deployment': deployment, 'current_assess_sha256': hashlib.sha256(current.encode()).hexdigest(),
            'current_source_sha256': sha(checkout/SOURCE_PATH),
            'difference': {'before': OLD, 'after': NEW},
            'non_withdrawn_rows': 'Retained in denominator under exact branch-equivalence proof, not runtime cases'}


def eligibility(client):
    suggestions = client.suggestions(proposal=PID, domain='protocols')
    identity = client.whoami()
    source = client.measurement(TARGET)
    proposal = client.proposal(SLUG, authenticated=True)
    if identity['sub'] == source['submitter']['sub']:
        raise ValueError('The original author cannot independently replicate this result')
    if source.get('is_replication') or source.get('evidence_state') != 'valid' or source.get('retraction', {}).get('retracted'):
        raise ValueError('Source is not a valid effective original')
    offered = [r for r in suggestions['suggestions'] if r.get('replicates_hash') == TARGET
               and r.get('executable_now') is True]
    if len(offered) != 1 or proposal['public_id'] != PID or proposal['stage'] not in ('seconded', 'measured'):
        raise ValueError('Exact independent replication is not currently offered; stop for review')
    return source, proposal


def validate_census(census):
    records = census['records']
    if not records or len({r['public_id'] for r in records}) != len(records):
        raise ValueError('Empty or duplicate census')
    expected = {r['public_id'] for r in records if r['stage'] == 'withdrawn'}
    if expected != set(census['withdrawn_details']):
        raise ValueError('Incomplete withdrawn-case population')
    for key, detail in census['withdrawn_details'].items():
        if detail['stage'] != 'withdrawn' or detail['public_id'] != key:
            raise ValueError('Census/detail changed stage during capture; recapture before mint')
        if detail.get('full_measurement_envelopes') is not True:
            raise ValueError('Full measurement envelopes, not list projections, are required')


def prepare(client, checkout, out, discussion_url):
    source, proposal = eligibility(client)
    if discussion_url != proposal['colony_thread_url']:
        raise ValueError('Acknowledge the current full discussion URL after reading it independently')
    if out.exists():
        raise ValueError('Output already exists; never overwrite an earlier freeze')
    deployment = client.health()['deployment']['commit']
    boundary = source_boundary(checkout, deployment)
    records = [r for p in client.proposal_pages(page_size=200) for r in p['proposals']]
    details = {}
    for row in records:
        if row['stage'] == 'withdrawn':
            detail = client.proposal(row['slug'])
            detail['measurements'] = [client.measurement(m['manifest_hash']) for m in detail['measurements']]
            detail['full_measurement_envelopes'] = True
            details[row['public_id']] = detail
    census = {'captured_at': datetime.now(timezone.utc).isoformat(), 'records': records,
              'domain': 'complete public all-stage proposal sweep, language and protocols',
              'withdrawn_details': details,
              'row_class_counts': dict(Counter(('protocol' if r['kind']=='protocol' else 'language')+'/'+r['stage'] for r in records))}
    validate_census(census)
    manifest = dict(source['manifest'])
    if manifest['metric'] != 'unclaimed_verdict_flips' or manifest['models'] != ['retirement-causal-guard-audit-v1']:
        raise ValueError('Unexpected source estimand/instrument')
    save(out/'input-census.json', census)
    save(out/'source-boundary.json', boundary)
    manifest.update(replicates_hash=TARGET, computed_at=census['captured_at'])
    manifest['against'] = {'repository': 'ai-nglish/ainglish-symfony', 'implementation': IMPLEMENTATION,
        'current_deployment': deployment, 'input_census_sha256': sha(out/'input-census.json'),
        'source_boundary_sha256': sha(out/'source-boundary.json'),
        'runner_sha256': sha(HERE/'retirement_replica.py'), 'probe_sha256': sha(HERE/'retirement_probe.php'),
        'source_measurement': TARGET,
        'supplementary_test_sha256': {p: sha(checkout/p) for p in manifest['supplementary_tests']},
        'composer_lock_sha256': sha(checkout/'composer.lock')}
    manifest['planned_sample'] = dict(manifest['planned_sample'], public_proposals=len(records),
        row_classes=census['row_class_counts'], public_withdrawn_cases=len(details))
    save(out/'manifest.json', manifest)
    save(out/'preparation.json', {'measurement': False, 'outcomes_computed': False,
        'source': TARGET, 'fresh_census': True, 'discussion_reviewed': discussion_url,
        'adaptations': ['Executor-specific fresh live census and full evidence envelopes',
            'Same real PHP counterfactual/control/aggregation contract, parameterized paths',
            'Current deployed method equivalence, not original-only empty-list assertion'],
        'still_required': ['Independent contract review', 'Publish frozen inputs/runner/probe and inspect dependencies',
            'Dedicated disposable local database provisioned by executor', 'Fresh eligibility and mint before all outcomes']})
    return manifest


def safe_database(url):
    parsed = urlparse(url)
    name = parsed.path.lstrip('/')
    if parsed.scheme not in ('mysql', 'mariadb') or parsed.hostname not in ('127.0.0.1', 'localhost', 'db'):
        raise ValueError('Only a local disposable test database is allowed')
    if not re.fullmatch(r'ainglish_retirement_replica_[a-z0-9]{8,32}', name):
        raise ValueError('Database must have the reserved replica prefix and an 8-32 character unique suffix')
    return name


def run(client, checkout, out, php, freeze_url, database_url, accept_database):
    if not freeze_url.startswith('https://'):
        raise ValueError('Publish the exact frozen package at an immutable HTTPS receipt before mint')
    if not accept_database:
        raise ValueError('The endpoint tests clear fixtures; explicit exclusive disposable DB acknowledgement required')
    safe_database(database_url)
    if (out/'execution').exists():
        raise ValueError('A prior execution exists; reconcile it, never rerun automatically')
    source, _ = eligibility(client)
    manifest = read(out/'manifest.json'); pins = manifest['against']
    if manifest.get('replicates_hash') != TARGET:
        raise ValueError('Missing exact replication target')
    for path, digest in [(out/'input-census.json', pins['input_census_sha256']),
                         (out/'source-boundary.json', pins['source_boundary_sha256']),
                         (HERE/'retirement_replica.py', pins['runner_sha256']),
                         (HERE/'retirement_probe.php', pins['probe_sha256']),
                         (checkout/'composer.lock', pins['composer_lock_sha256'])]:
        if sha(path) != digest:
            raise ValueError('A frozen input or instrument changed')
    for path, digest in pins['supplementary_test_sha256'].items():
        if sha(checkout/path) != digest:
            raise ValueError('A supplementary test changed after freeze')
    validate_census(read(out/'input-census.json'))
    boundary = source_boundary(checkout, client.health()['deployment']['commit'])
    if boundary != read(out/'source-boundary.json'):
        raise ValueError('Deployment/source boundary changed since freeze')
    if manifest['method'] != source['manifest']['method'] or manifest['models'] != source['manifest']['models']:
        raise ValueError('Replication method/roster differs from original')
    # Pure preflight is deliberately before execution or causal probes.
    kwargs = dict(estimand=ESTIMAND, admissibility_gates=manifest['admissibility_gates'],
                  planned_sample=manifest['planned_sample'], proposal_revision=SLUG)
    checked = client.preflight_attempt(SLUG, manifest, **kwargs)
    if checked.get('accepted') is not True or checked.get('kind') != 'ainglish.attempt-preflight.v1':
        raise ValueError('Server preflight refused the frozen plan')
    preparation = checked.get('replication_preparation')
    if preparation is not None and (preparation.get('known_obstructions')
            or preparation.get('status') != 'no_known_obstruction'):
        raise ValueError('Server replication preparation reports an obstruction; do not spend to confirm')
    execution = out/'execution'
    save(execution/'preflight.json', checked)
    save(execution/'published-freeze.json', {'url': freeze_url})
    opened = client.mint_attempt(SLUG, manifest, **kwargs)
    save(execution/'attempt.json', opened)
    attempt = opened['attempt']['attempt_id']
    env = dict(os.environ, APP_ENV='test', DATABASE_URL=database_url)
    def invoke(name, argv):
        process = subprocess.run([php, *argv], cwd=checkout, env=env, text=True,
                                 capture_output=True, timeout=600)
        # Local private logs only: scrub the known DB URL in case a library prints it.
        save(execution/(name+'.json'), {'exit_code': process.returncode,
            'stdout': process.stdout.replace(database_url, '[redacted test database]'),
            'stderr': process.stderr.replace(database_url, '[redacted test database]')})
        if process.returncode:
            raise RuntimeError('Retained subprocess failed: '+name)
        return process.stdout
    try:
        for path in manifest['supplementary_tests']:
            invoke(Path(path).stem, ['vendor/bin/phpunit', path])
        outcome = json.loads(invoke('probe-process', [str(HERE/'retirement_probe.php'),
                                     str(checkout), str(out/'input-census.json')]))
        value = outcome['value']
        if type(value) is not int or not 0 <= value <= manifest['planned_sample']['public_proposals']:
            raise ValueError('Not a finite live flip count')
        if outcome['domain_count'] != manifest['planned_sample']['public_proposals']:
            raise ValueError('Outcome omitted census rows')
        save(execution/'causal-result.json', outcome)
        payload = {'metric': manifest['metric'], 'value': value, 'manifest': manifest,
                   'replicates_hash': TARGET, 'panel_models': manifest['models'], 'panel_neff': 1,
                   'attempt_id': attempt}
        save(execution/'measurement-payload.json', payload)
        receipt = client.measure(SLUG, payload)
        save(execution/'measurement-receipt.json', receipt)
        save(execution/'after.json', client.proposal(SLUG, authenticated=True))
        return receipt
    except Exception as error:
        # Keep outcome/log files private until reviewed for accidental dependency logging.
        save(execution/'failure.json', {'type': type(error).__name__, 'message': 'Inspect retained local logs; no automatic rerun'})
        state = client.attempt(attempt)
        if state.get('state', state.get('attempt', {}).get('state')) == 'open':
            save(execution/'abort.json', client.abort_attempt(attempt,
                'Frozen retirement replication prerequisite, instrument or submission failed; retained output requires review',
                {'failure_type': type(error).__name__, 'retained_file_digests': {p.name: sha(p) for p in execution.glob('*.json')}},
                failed_gate_kind='harness_error'))
        raise


def main():
    os.umask(0o077)
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['prepare', 'run'])
    p.add_argument('--client-factory', required=True)
    p.add_argument('--checkout', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--discussion-reviewed')
    p.add_argument('--php', default='php', help='Installed executable or locally reviewed wrapper; no download')
    p.add_argument('--freeze-url')
    p.add_argument('--exclusive-disposable-database', action='store_true')
    a = p.parse_args()
    client = factory(a.client_factory)
    if a.action == 'prepare':
        prepare(client, a.checkout.resolve(), a.out.resolve(), a.discussion_reviewed)
        print('Prepared, not measured. Review and publish this freeze before run.')
    else:
        run(client, a.checkout.resolve(), a.out.resolve(), a.php, a.freeze_url or '',
            os.environ.get('DATABASE_URL', ''), a.exclusive_disposable_database)
        print('Filed the retained result; independently inspect settlement and remaining gates.')


if __name__ == '__main__':
    main()

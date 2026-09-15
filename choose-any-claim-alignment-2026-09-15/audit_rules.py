"""Replay actual pinned upstream rule methods without editing the checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

PIN = '766bc18b4f4a7e807fbfb2da669c3e09d187df34'
ROOT = Path(__file__).resolve().parent

def audit(repo, php):
    digests = {}
    with tempfile.TemporaryDirectory(prefix='choose-rule-audit-') as temporary:
        for name in ('ProtocolMeta', 'MeasurementProtocols', 'MeasurementService', 'EvidenceReadiness', 'ReplicationSettlement'):
            source = subprocess.check_output(['git', '-C', str(repo), 'show',
                                               f'{PIN}:src/Service/{name}.php'])
            digests[name] = hashlib.sha256(source).hexdigest()
            (Path(temporary) / (name + '.php')).write_bytes(source)
        process = subprocess.run([php, str(ROOT / 'current-rule-probe.php'), temporary],
                                 capture_output=True, text=True)
        if process.returncode:
            raise RuntimeError(process.stdout + process.stderr)
        result = json.loads(process.stdout)
    result.update(upstream_commit=PIN, source_sha256=digests)
    assert [r['bounded_prerequisite_stance'] for r in result['cases']] == [
        'unresolved', 'unresolved', 'supports', 'supports']
    assert result['cases'][3]['effective_stance'] == 'opposes'
    assert [r['reproduced_ok'] for r in result['replication_examples']] == [False, False, False, True]
    return result

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--php', default='php')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    result = audit(args.repo, args.php)
    with args.output.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print('Pinned domain-method audit passed; no external write or reader call.')

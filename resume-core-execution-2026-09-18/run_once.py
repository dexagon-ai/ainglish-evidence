"""Same reviewed original runner, new repaired-preparation receipt directory."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEGACY = HERE.parent/'resume-core-original-2026-09-17/run_once.py'
LEGACY_SHA = '7a864f1418f38b7726c20b1545c8f9dc75a9cd3901264603363162939daa6f2d'

def load_runner():
    assert hashlib.sha256(LEGACY.read_bytes()).hexdigest() == LEGACY_SHA
    spec = importlib.util.spec_from_file_location('reviewed_resume_runner', LEGACY)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    runner.HERE = HERE
    prior_checks = runner.checks

    def repaired_checks(a, runspec):
        decision = runner.read('execution-decision.json')
        for name, expected in decision['file_sha256'].items():
            assert Path(name).name == name
            assert hashlib.sha256((HERE/name).read_bytes()).hexdigest() == expected, name
        assert runner.read('cross-bank-audit.json')['passed']
        assert runner.read('approval-conditions.json')['checked_author_notice'] == '556dc5f3-400d-4567-92eb-13a813072875'
        rows = runner.colony_client().get_all_comments(runner.THREAD)
        required = {'77bdb7bb-999e-4732-9bd5-dfe58dd32e9b', '2fbe86ab-ec13-4240-a2b8-54bb4e94f2be'}
        assert required <= {r['id'] for r in rows}, 'Missing repair freeze or acceptance'
        checked = prior_checks(a, runspec)
        checked['repaired_replica_items_sha256'] = 'd2ee5b418a037e1054ccb1691bcf4c721ea2332c51ff2de6ae196bcb267ed940'
        checked['historical_held_preparation_preserved'] = True
        return checked

    runner.checks = repaired_checks
    return runner

if __name__ == '__main__':
    load_runner().main()

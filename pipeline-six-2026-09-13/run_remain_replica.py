"""One official, preregistered execution. No retry, alternate model or self-vote."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess

from ainglish.panel import _planned_panel_manifest, _run_preregistered_panel, ask
from local_colony_auth import ainglish_client, colony_client

HERE = Path(__file__).resolve().parent / 'remain-source-matched'
SOURCE = 'f6ea7793b22c101c1d3ada038db24ec58518e7a145c428e01081e827b2feead1'
PID = 'a-xffrm7wz2wt3xhzf'


def save(name, value):
    with (HERE / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    assert shutil.disk_usage(HERE).free > 20 * 1024 ** 3
    connections = subprocess.check_output(['ss', '-Htn', 'sport = :11434'], text=True)
    assert not connections.strip(), 'Another local inference connection is active; no eviction.'
    c = ainglish_client()
    assert c.whoami()['sub'] == '52b1883a-464e-403c-9059-d57afe91a13c'
    suggestion = c.suggestions(proposal=PID)
    assert any(r.get('replicates_hash') == SOURCE and r.get('confirmation_capable')
               for r in suggestion['suggestions'])
    thread = colony_client().get_comments('9b2e1d5f-a186-45c7-bab8-cfcde8a72240')
    assert thread['has_more'] is False and thread['total'] == 11, 'New discussion requires review before mint.'
    proposal = c.proposal(PID, authenticated=True)
    contract = json.loads((HERE / 'remain-proposal-contract.json').read_text())
    assert {k: proposal[k] for k in contract} == contract
    assert proposal['stage'] == 'measured' and proposal['author_work_notices']['active'] is None
    source = c.measurement(SOURCE)
    assert source['evidence_state'] == 'valid' and source['retraction'] is None
    assert not source['confirmed'] and not source['is_replication']
    spec = json.loads((HERE / 'remain-runspec.json').read_text())
    planned = json.loads((HERE / 'remain-planned-manifest.json').read_text())
    assert _planned_panel_manifest(spec) == planned
    preflight = c.preflight_attempt(spec['slug'], planned, **spec['attempt'])
    assert preflight.get('accepted') is True, preflight
    save('remain-execution-start.json', {'started_at': datetime.now(timezone.utc).isoformat(),
                                       'principal': 'Dexagon', 'source_hash': SOURCE,
                                       'boundary': 'Execution marker, not a measurement or mint receipt.'})
    result = _run_preregistered_panel(spec, spec, ask, c, receipt_dir=str(HERE), receipt_stem='remain-replica')
    if result is None:
        raise SystemExit('Official attempt aborted; retain receipt and do not rerun this design.')
    save('remain-result.json', result)
    after = c.proposal(PID)
    save('remain-public-after.json', {k: after[k] for k in
         ['public_id', 'slug', 'stage', 'evidence_readiness', 'verdict', 'author_work_notices']})
    print('Filed one independent-principal fresh-input result; inspect its actual settlement, not just its value.')

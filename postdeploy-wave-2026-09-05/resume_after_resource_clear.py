"""Resume only the zero-call, pre-mint resource refusal; never retry an experiment."""
import hashlib
import json
import subprocess
import urllib.request
from datetime import datetime, timezone

import analyse
import prepare_readers
import repair_controls
import run_readers_once


def main():
    root = repair_controls.OUT
    previous = json.loads((root / 'mean.careful.exception.json').read_text())
    assert previous['message'] == 'Unrelated inference workload'
    assert previous['attempt_id'] is None and previous['calls_retained'] == 0
    assert not list(root.glob('*.opened.json')) and not list(root.glob('*.calls.jsonl'))
    repair_controls.validate()
    with urllib.request.urlopen('http://127.0.0.1:11434/api/ps', timeout=10) as response:
        assert json.load(response)['models'] == [], 'Wait for unrelated inference to finish'
    destination = root / 'execution-after-resource-clear'
    destination.mkdir()  # Exclusive: a later failure is not an invitation to rerun.
    (destination / 'frozen').mkdir()
    copies = {}
    for stem in repair_controls.ORDER:
        spec_path = root / (stem + '.runspec.json')
        spec = json.loads(spec_path.read_text())
        item_path = root / 'frozen' / (stem + '.items.json')
        published = subprocess.run(
            ['git', 'show', spec['attempt']['planned_sample']['source_commit'] + ':' +
             str(item_path.relative_to(repair_controls.ROOT.parent))],
            cwd=repair_controls.ROOT.parent, check=True, capture_output=True,
        ).stdout
        assert published == item_path.read_bytes()
        for source in [spec_path, item_path]:
            payload = source.read_bytes()
            relative = source.relative_to(root)
            with (destination / relative).open('xb') as output:
                output.write(payload)
            copies[str(relative)] = hashlib.sha256(payload).hexdigest()
    with (destination / 'resource-resume.json').open('x') as output:
        json.dump({
            'at': datetime.now(timezone.utc).isoformat(),
            'reason': 'Earlier refusal happened before mint and before any reader call; unrelated workload has now ended.',
            'prior_refusal': previous,
            'unchanged_frozen_bytes': copies,
            'stop_rule': 'First aborted study stops the campaign; no further redesign or reader retry.',
        }, output, indent=2)
        output.write('\n')
    prepare_readers.ROOT = destination
    run_readers_once.ROOT = destination
    run_readers_once.validate = repair_controls.validate
    run_readers_once.STOP_ON_ABORT = True
    run_readers_once.main()
    analyse.ROOT = destination
    analyse.main()


if __name__ == '__main__':
    main()

"""Execute frozen originals once through the official SDK; retain raw output too."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

from ainglish import panel
from instrument import ROOT, PRIOR, canonical, save
from studies import IDS, ORDER


def validate():
    assert json.loads((ROOT / 'instrument/finished.json').read_text())['state'] == 'validated'
    index = json.loads((ROOT / 'frozen/index.json').read_text())
    for stem in ORDER:
        items = json.loads((ROOT / 'frozen' / f'{stem}.items.json').read_text())
        assert hashlib.sha256(canonical(items)).hexdigest() == index[stem]['items_sha256']
    return True


def main():
    # Reuse the already exercised SDK orchestration, but own a new output directory,
    # new frozen manifests, a strict first-abort stop, and complete raw wire answers.
    sys.path.insert(0, str(PRIOR))
    spec = importlib.util.spec_from_file_location('prior_reader_runner', PRIOR / 'run_readers_once.py')
    runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    runner.ROOT = ROOT; runner.IDS = IDS; runner.ORDER = ORDER; runner.validate = validate
    runner.save = save; runner.STOP_ON_ABORT = True
    original_chat = panel.chat
    with (ROOT / 'raw-reader-outputs.jsonl').open('x') as journal:
        def chat(reader, prompt):
            record = {'at': datetime.now(timezone.utc).isoformat(), 'reader': reader['name'],
                      'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest()}
            try:
                output, truncated = original_chat(reader, prompt)
                record.update(output=output, truncated=truncated)
                return output, truncated
            except BaseException as exc:
                record['error_type'] = type(exc).__name__
                raise
            finally:
                journal.write(json.dumps(record) + '\n'); journal.flush(); os.fsync(journal.fileno())
        with patch.object(panel, 'chat', side_effect=chat):
            runner.main()


if __name__ == '__main__':
    main()

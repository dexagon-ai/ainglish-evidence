"""Freeze or execute target-independent qualification on our isolated cached reader service."""
import argparse
import json
from pathlib import Path
from ainglish import reader_qualification

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write('\n')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['freeze', 'run'])
    args = parser.parse_args()
    for name in ['mistral', 'gemma']:
        target = ROOT / 'qualification' / (name + '.screen.json')
        if args.action == 'freeze':
            spec = json.loads((REPO / 'overnight-2026-09-05/instrument' / ('validation.' + name + '.screen.json')).read_text())
            spec['reader']['base_url'] = 'http://127.0.0.1:11435/v1'
            spec.pop('screen_url', None)
            reader_qualification.validate_screen(spec)
            save(target, spec)
            print('Frozen', name, len(spec['controls']), 'target-independent controls; no inference', flush=True)
        else:
            output = target.with_name(name + '.result.json')
            assert not output.exists(), 'Keep the first qualification; no automatic retry'
            result = reader_qualification.run_screen(json.loads(target.read_text()))
            save(output, result)
            print(name, result['receipt']['result'], flush=True)

if __name__ == '__main__':
    main()

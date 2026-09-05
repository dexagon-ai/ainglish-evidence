"""Repair uppercase comparator identifiers on four never-minted, never-observed plans."""
import json
from pathlib import Path
from ainglish import panel
from prepare import ORDER, save

ROOT = Path(__file__).resolve().parent

def main():
    changes = []
    for name, condition in ORDER:
        if (name, condition) == ('verdict', 'bare'):
            continue  # Already observed: its design and answers must not change.
        stem = name+'.'+condition
        failure = json.loads((ROOT/(stem+'.exception.json')).read_text())
        assert failure['calls_retained'] == 0 and failure['attempt_id'] is None
        assert not any((ROOT/(stem+s)).exists() for s in ['.opened.json', '.intent.json', '.calls.jsonl'])
        spec = json.loads((ROOT/(stem+'.runspec.json')).read_text())
        old = spec['comparator']['kind']; new = old.lower()
        assert old != new and 'English' in old
        assert spec['comparison_identity']['comparator_genre'] == old
        spec['comparator']['kind'] = new
        spec['comparison_identity']['comparator_genre'] = new
        # Only these two labels change; all scientific inputs and all other settings stay fixed.
        original = json.loads((ROOT/(stem+'.runspec.json')).read_text())
        original['comparator']['kind'] = new
        original['comparison_identity']['comparator_genre'] = new
        assert original == spec
        manifest = dict(spec, items=json.loads((ROOT/'frozen'/(stem+'.items.json')).read_text()))
        panel.prepare_reader_instruments(manifest)
        panel._planned_panel_manifest(manifest)  # Mock oracle only; never a model call.
        save(stem+'.preflight-fixed.runspec.json', spec)
        changes.append({'condition': stem, 'old_label': old, 'new_label': new, 'prior_calls': 0,
                        'prior_attempt': None, 'mock_preview_passed': True, 'changed_fields':
                        ['comparator.kind', 'comparison_identity.comparator_genre']})
    save('preflight-repair.json', {'reason': 'SDK requires lowercase versioned comparator identifiers; the initial generator used uppercase English.',
        'scientific_inputs_changed': False, 'analysis_changed': False, 'observed_conditions_repeated': False,
        'changes': changes})
    print('Four zero-observation plans repaired and mock-preflighted; no reader calls.')

if __name__ == '__main__': main()

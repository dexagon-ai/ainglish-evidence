"""Run against the patched pinned packet directory, without tokenization."""
import copy,importlib.util,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('packet',Path(sys.argv[1])/'noundo_rstar.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
p.selftest()
bad=['Deleted the branch, can-undo(reflog; ).',
     'Deleted the branch, can-undo(reflog; oper)ator).',
     'Deleted the branch, can-undo(reflog; ONLY operator).',
     'Deleted the branch, can-undo(reflog; By operator).',
     'Deleted the branch.; now wait, no-undo.',
     'Deleted the branch., no-undo.',
     'Deleted the branch?, can-undo(reflog).',
     'Deleted the branch, can-undo(PARTIAL restore).']
for s in bad:
    try:p.parse_marked(s)
    except ValueError:pass
    else:raise AssertionError(s)
bank=p.synthetic_bank();profile=p.sampling_profile(bank)
assert p.validate_frozen_profile(bank,profile)['structural_validation_only']
invalid=copy.deepcopy(bank)
for row in invalid:
    f=p.parse_marked(row['ainglish'])
    if f.get('holder'):
        f['holder']='oper)ator';row.update(ainglish=p.render_marked(f),english=p.render_rstar(f));break
try:p.validate_bank(invalid)
except ValueError:pass
else:raise AssertionError('invalid full bank accepted')
drift=copy.deepcopy(bank)
for row in drift:
    f=p.parse_marked(row['ainglish'])
    if 'path' in f:
        f['path']='a much longer recovery pathway';row.update(ainglish=p.render_marked(f),english=p.render_rstar(f));break
p.validate_bank(drift) # same marginals, but not the agreed joint population
try:p.validate_frozen_profile(drift,profile)
except ValueError:pass
else:raise AssertionError('population drift accepted')
inverted=copy.deepcopy(bank)
for row in inverted:row['shape']='instruction' if row['shape']=='report' else 'report'
# A structural validator cannot certify arbitrary natural language tense or restoration.
assert p.validate_bank(inverted)['semantic_review_required']
assert 'maximum tokenizer mean' in p.CLAIM and 'roster mean' not in p.CLAIM
print('8 parser negatives, invalid full-bank rejection, joint-population drift refusal, semantic-review boundary and estimator checked; 0 tokenizer/reader calls')

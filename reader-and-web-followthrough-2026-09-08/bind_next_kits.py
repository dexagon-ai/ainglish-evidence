"""Create reviewable exact reader plans, without minting or calling readers."""
import json
from pathlib import Path
from build_readers import freeze

ROOT = Path(__file__).resolve().parent
for name, seed in [('postpone', 2026090887), ('replace', 2026090888)]:
    items = json.loads((ROOT / (name + '-kit') / 'items.json').read_text())
    plan = json.loads((ROOT / (name + '-kit') / 'plan.json').read_text())
    freeze(name + '-careful', name, items,
           ('192 ledger-first authored ' + name + ' scenarios versus full careful English, two fixed cached reader families. ' +
            ('Immediate action, what the instruction asserts, and return-time guarantee, not a test of whether a prior meeting actually approved the matter. This component does not test the +30pp bare-table hypothesis; supplied speaker-variety labels are not real participants.' if name == 'postpone' else
             'Leaving/entering roles, hypothetical post-completion occupant, and excluded inferences, across eight domains, four clause forces and both nearby reference orders. Both arms explicitly state the absence of supplied deletion, exchange, compatibility and authority facts, so excluded-inference performance is conditional on that safeguard; it is not unaided cold inference.') +
            ' Authored template variants are not independent natural-use scenarios or human validation; this is additional original coverage, not an independent replication.'),
           'claim_test', {'kind': name + '-careful-english-v1', 'description': 'Exactly shared scenario record and contextual force; marker versus complete careful-English instruction. No hidden-intention accuracy baseline.'},
           seed, ['Full-coverage cost original ' + plan['cost_original'] + ' remains valid and independently confirmed within its <=0 allowance before comprehension execution',
                  'A real independent reviewer must accept the exact scenario ledger, visible arms, golds and scope; bind review to this items digest',
                  plan['analysis'], 'Keep every source result and all planned exclusions; this packet does not complete the separately listed robustness or descriptive ambiguity components'])

    fixtures = json.loads((ROOT / (name + '-kit') / 'validity-fixtures.json').read_text())
    scope = ('This question is about applying the consider-now/postpone procedural fork. Only unpinned procedural uses are in scope; furniture, data/database tables and an already pinned ruleset are not.' if name == 'postpone' else
             'The registered replacement relation requires both named old/new labels, two distinct uniquely resolved nonempty references, and one identified slot. Do not guess missing, equal, unresolved or ambiguous roles.')
    diagnostic = []
    for f in fixtures:
        diagnostic.append({'id': name + '-' + f['id'], 'english': scope + ' Candidate text: ' + f['text'],
                           'ainglish': scope + ' Candidate text: ' + f['text'],
                           'question': 'Does this candidate satisfy the stated applicability or validity requirement?',
                           'options': ['Yes: apply the relation as written.', 'No: do not apply it; preserve the stated scope or ask for clarification.'],
                           'answer': 'No: do not apply it; preserve the stated scope or ask for clarification.',
                           'settlement_stratum': name + '-invalid', 'diagnostic_class': f.get('defect', 'carve-out'), 'diagnostic_only': True})
    # A reject-everything reader must not pass a validity diagnostic: pair each
    # prescribed invalid fixture with an explicit valid applicability control.
    for i in range(len(fixtures)):
        text = ('In an unpinned meeting, consider-now(matter K-' + str(i) + ').' if name == 'postpone' else
                f'In the sole slot S-{i}, replace(old=O-{i}, new=N-{i}); both labels resolve uniquely to different objects.')
        diagnostic.append({'id': name + '-valid-control-' + str(i), 'english': scope + ' Candidate text: ' + text,
                           'ainglish': scope + ' Candidate text: ' + text,
                           'question': 'Does this candidate satisfy the stated applicability or validity requirement?',
                           'options': ['No: do not apply it; preserve the stated scope or ask for clarification.', 'Yes: apply the relation as written.'],
                           'answer': 'Yes: apply the relation as written.', 'settlement_stratum': name + '-valid',
                           'diagnostic_class': 'sufficient-control', 'diagnostic_only': True})
    freeze(name + '-validity', name, diagnostic,
           f'{name}: 24 prescribed invalid/carve-out fixtures plus 24 valid applicability controls; identical candidate text and scope in both arms. This is absolute rule-following diagnostic coverage, not a causal language-benefit contrast, not an independent replication and not the main scalar. Two fixed cached readers; repeated defect templates are not independent natural-use samples.',
           'diagnostic', {'kind': 'identical-scope-and-candidate-control-v1', 'description': 'Both arms identical by design; inspect absolute false acceptance and false rejection separately, not arm delta as a benefit.'},
           seed + 10, ['Complete the named cost and exact semantic-review gates before this dependent programme',
                       'Report invalid acceptance and valid rejection by defect and reader separately; a reject-all model is not successful',
                       'Do not combine this identical-arm scope diagnostic with the primary careful-English comprehension score'])

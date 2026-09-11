"""Recheck three held remote study packages. No authentication or inference.

Uses existing public answer-bearing packets; these are NOT fresh replication
inputs. The output is a preparation handoff, never an executable runspec.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from collections import Counter
from ainglish.experiment_audit import audit_items
from ainglish.panel import _validate_learnability_v2

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PACKETS = REPO / 'completion-paths-2026-09-10/reader-packets'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def source(relative):
    return json.loads(subprocess.check_output(['git', '-C', str(REPO), 'show',
        '041943d:completion-followthrough-2026-09-09/' + relative], text=True))


def build(states):
    rent = load(PACKETS/'rent-learning/items.json')
    controls = [r for r in rent if r.get('calibration')]
    designs = [
        ('rent', 'learnability', rent, 'rent-learning',
         '64 application targets; byte-identical marked arms, the official harness adds the exact entry only to the entry arm. Not the separate 96-item CAD matrix.'),
        ('resume', 'comprehension_accuracy_delta', source('resume-v2/careful-items.json') + controls,
         'resume-learning', '64 core plus 32 separate boundary cases under full canonical careful English. New remote original, not a replication of the old Falcon/OLMo instrument and not a learning result.'),
        ('sanction', 'comprehension_accuracy_delta', load(PACKETS/'sanction-careful/items.json') + controls,
         'sanction-careful', '64 careful-English/force component targets. Not the separately promised bare-English advantage, practical-verb comparison or complete robustness/fidelity programme.'),
    ]
    out = []
    for name, metric, items, prior, scope in designs:
        current = states[name]
        frozen = load(PACKETS/prior/'proposal-snapshot.json')
        fields = ['public_id', 'slug', 'form', 'english_mapping', 'predicted_measurement', 'evidence_contract']
        changes = [k for k in fields if current[k] != frozen[k]]
        targets = [r for r in items if not r.get('calibration')]
        audit = audit_items(items)
        if not audit['ok']:
            raise ValueError((name, audit))
        if metric == 'learnability':
            plan = load(PACKETS/prior/'review-plan.json')
            if not _validate_learnability_v2({'slug':current['slug'], 'form':current['form'],
                    'construct':current['form'], 'entry':plan['entry']}, targets, controls):
                raise ValueError('Learning entry or identical-arm contract changed')
        item_budget = len(targets) * (2 if metric == 'learnability' else 1)
        out.append({
            'public_id': current['public_id'], 'slug': current['slug'], 'metric': metric,
            'status': 'hold_changed_proposal' if changes else 'prepared_not_run',
            'changed_proposal_fields': changes,
            'scope': scope, 'items_sha256': digest(items), 'target_count':len(targets),
            'control_count':len(controls),
            'per_form_targets':dict(Counter(r.get('strata',{}).get('form','undeclared') for r in targets)),
            'items':items, 'structural_audit':audit,
            'full_semantic_certification':False,
            'live_work':current['evidence_readiness'],
            'current_proposal_projection':{k:current[k] for k in fields},
            'reader_instruments':[], 'reader_qualifications':[], 'accepted_executors':[],
            'scientific_attempt_id':None, 'reader_calls_made':0,
            'call_budget_per_reader': {'targets':item_budget,'calibration':2*len(controls),
                'total':item_budget+2*len(controls),
                'excludes':'Separate reader qualification; price and duration need the actual provider/settings. No automatic retries.'},
            'reader_scope':{
                'existing_broad_design_min_lineages':2,
                'one_lineage_option': 'not_allowed_by_declared_sanction_plan' if name=='sanction' else 'separate_prospective_scoped_original_for_review',
                'boundary':'No existing manifest or two-lineage commitment is silently changed. A single-reader study cannot claim broad portability, weight training or completion of a two-lineage requirement.'},
            'stop_before_spend':[
                'Read the live proposal and complete discussion as your own identity. Any changed definition, contract, author reset or competing campaign requires fresh review.',
                'Choose the exact study scope and roster openly before any target exposure; no inherited or invented reader access.',
                'Validate the entire question/option meaning and canonical English, not just structural checks or agreement with the saved key.',
                'Check your exact authenticated offered metric/role/target and unresolved prerequisite decisions. This public handoff grants no personal eligibility.',
                'Qualify exact target-independent reader/settings bindings before exposure. A chat runtime with tools/memory is not a stateless reader.',
                'Freeze full official runspec, every answer-bearing item, entry where relevant, seed, strata, analysis, budget and abort rules; preflight and mint before scientific calls.',
                'Retain faults and all adverse/null results; an independent confirmation uses fresh complete inputs and the preserved original contract, not these published rows again.',
            ],
        })
    return {'kind':'ainglish.remote-review-handoffs.v1','executable':False,
            'measurement':False,'new_models':False,'packages':out}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--states',type=Path,default=HERE/'reader-proposal-snapshots.json')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    result=build(load(a.states))
    with a.output.open('x') as f:
        json.dump(result,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
    for row in result['packages']:
        print(row['public_id'],row['metric'],row['status'],row['target_count'],row['call_budget_per_reader']['total'])

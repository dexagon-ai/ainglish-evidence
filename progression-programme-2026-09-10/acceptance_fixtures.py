"""Executable prospective review fixtures, NOT today's policy or a measurement.

The 5 pp margin and 90% floor belong to invented cases, not project defaults.
Run directly for the reference oracle; --candidate module:callable checks an
independently implemented prospective interpreter against the same required flags.
"""
import argparse
import copy
import importlib
import json

BASE = dict(margin=5, accuracy_floor=.9, interval=[-1, 2], accuracy=.96,
            required_form_lowers=[-1, -1], confirmed=True, confirmed_loss=False,
            uncertainty_valid=True, cost_promised=True, cost_confirmed=True,
            bare_promised=False, bare_confirmed=False, extra_constraints_met=True,
            exposure_matches=True, prospective=True, unresolved_old_carrier=False,
            semantic_judgment_only=False)

CASES = [
    ('A', {}, 'candidate_preservation_and_promises_complete'),
    ('B', dict(interval=[-8, 4]), 'preservation_not_established'),
    ('C', dict(interval=[-3, -1], confirmed_loss=True), 'confirmed_loss_veto'),
    ('D', dict(interval=[-9, -6], confirmed_loss=True), 'preservation_not_established'),
    ('E', dict(accuracy=.5), 'absolute_floor_unmet'),
    ('F', dict(interval=[0, 0], accuracy=1, uncertainty_valid=False), 'uncertainty_unresolved'),
    ('G', dict(required_form_lowers=[-1, -8]), 'required_form_unmet'),
    ('H', dict(cost_confirmed=False), 'separate_cost_unmet'),
    ('I', dict(bare_promised=True, bare_confirmed=True, interval=[-9, -6]), 'preservation_not_established'),
    ('J', dict(bare_promised=True), 'separate_bare_gain_unmet'),
    ('K', dict(confirmed=False), 'independent_confirmation_unmet'),
    ('L', dict(uncertainty_valid=False), 'uncertainty_unresolved'),
    ('M', dict(unresolved_old_carrier=True), 'old_carrier_not_erased'),
    ('N', dict(exposure_matches=False), 'exposure_mismatch'),
    ('O', dict(prospective=False), 'requires_prospective_successor'),
    ('P', dict(prospective=False, confirmed_loss=True), 'confirmed_loss_veto'),
    ('Q', dict(extra_constraints_met=False), 'extra_constraint_unmet'),
    ('R', dict(semantic_judgment_only=True, confirmed=False), 'judgment_is_not_a_measurement'),
]


def interpret(c):
    flags = []
    checks = [
        (c['confirmed_loss'], 'confirmed_loss_veto'),
        (c['interval'][0] < -c['margin'], 'preservation_not_established'),
        (c['accuracy'] < c['accuracy_floor'], 'absolute_floor_unmet'),
        (any(x < -c['margin'] for x in c['required_form_lowers']), 'required_form_unmet'),
        (not c['uncertainty_valid'], 'uncertainty_unresolved'),
        (not c['confirmed'], 'independent_confirmation_unmet'),
        (c['cost_promised'] and not c['cost_confirmed'], 'separate_cost_unmet'),
        (c['bare_promised'] and not c['bare_confirmed'], 'separate_bare_gain_unmet'),
        (not c['extra_constraints_met'], 'extra_constraint_unmet'),
        (not c['exposure_matches'], 'exposure_mismatch'),
        (not c['prospective'], 'requires_prospective_successor'),
        (c['unresolved_old_carrier'], 'old_carrier_not_erased'),
        (c['semantic_judgment_only'], 'judgment_is_not_a_measurement'),
    ]
    for failed, name in checks:
        if failed:
            flags.append(name)
    return flags or ['candidate_preservation_and_promises_complete']


def check(candidate=interpret):
    results = []
    for name, change, required in CASES:
        c = copy.deepcopy(BASE | change)
        actual = candidate(c)
        assert required in actual, (name, required, actual)
        if name != 'A':
            assert 'candidate_preservation_and_promises_complete' not in actual, name
        results.append({'case': name, 'required': required, 'actual': actual})
    # Case-specific margins, no global 5 pp fallback; adverse or missing cost same hold.
    assert 'preservation_not_established' in candidate(BASE | {'margin': 3, 'interval': [-4, 2]})
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', help='Prospective pure interpreter module:callable; never a live write endpoint')
    args = parser.parse_args()
    candidate = interpret
    if args.candidate:
        module, name = args.candidate.split(':', 1)
        candidate = getattr(importlib.import_module(module), name)
    print(json.dumps({'kind': 'prospective-acceptance-fixtures', 'measurement': False,
                      'current_rule_activated': False, 'cases': check(candidate)}, indent=2))

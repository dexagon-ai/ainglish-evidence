"""Illustrative proposal-spec witnesses, NOT tests of deployed implementation."""
from copy import deepcopy
import unittest

IDENTITY = 'attested-strata-v1'


def prerequisite(row, keyed):
    if not keyed:
        return 'supports' if row['point'] >= -5 else 'opposes'
    if row.get('identity') != IDENTITY or not row.get('attested'):
        return 'unresolved'
    bounds = row.get('bounds', [])
    if not bounds:
        return 'unresolved'
    if any(valid and hi < -5 for lo, hi, valid in bounds):
        return 'opposes'
    return 'supports' if all(valid and lo >= -5 for lo, hi, valid in bounds) else 'unresolved'


def mint_admissible(keyed, identity):
    return not keyed or identity == IDENTITY


class ContractScopeWitnesses(unittest.TestCase):
    def test_f8c_f8d_missing_identity_never_point_satisfies_new_contract(self):
        for bounds in ([(-2, 1, True), (-3, 2, True), (-4, 1, True)],
                       [(-20, 18, True)]):
            row = {'point': -1, 'bounds': bounds, 'attested': True,
                   'generic_stance': 'neutral', 'settlement_receipt': {'reproduced_ok': True}}
            old = deepcopy(row)
            self.assertEqual(prerequisite(row, True), 'unresolved')
            self.assertEqual(prerequisite(row, False), 'supports')
            self.assertEqual(row, old)

    def test_f8e_missing_or_wrong_identity_rejects_future_mint(self):
        for identity in (None, '', 'different-method'):
            self.assertFalse(mint_admissible(True, identity))
            self.assertTrue(mint_admissible(False, identity))
        self.assertTrue(mint_admissible(True, IDENTITY))

    def test_identity_without_attestation_is_not_sufficient(self):
        self.assertEqual(prerequisite({'point': 1, 'identity': IDENTITY}, True), 'unresolved')
        self.assertEqual(prerequisite({'point': 1, 'identity': IDENTITY, 'attested': True}, True),
                         'unresolved')

    def test_non_degenerate_opposition_precedes_another_held_form(self):
        row = {'point': -2, 'identity': IDENTITY, 'attested': True,
               'bounds': [(-3, 1, False), (0, 0, False), (-7, -6, True)]}
        self.assertEqual(prerequisite(row, True), 'opposes')


if __name__ == '__main__':
    unittest.main()

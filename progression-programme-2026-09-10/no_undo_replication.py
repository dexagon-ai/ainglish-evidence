"""One prospectively frozen CPU-only replication; prepare and run are separate.

Uses an executor-owned authenticated SDK factory, no model downloads, no source
result matching/tuning. This run cannot establish comprehension or future training gains.
"""
import argparse
import copy
import hashlib
import importlib
import json
from pathlib import Path
from ainglish import token_measurement
from ainglish.client import manifest_commitment

SLUG = 'action-no-undo-action-can-undo-how-4'
PID = 'a-mv841prke9x9e5cm'
TARGET = '6a5e62a8e0a56127c91089f68451d525eed5957e067e91a58319919735a6c35c'
ROOT = Path(__file__).with_name('no-undo-token-replication')

# Fictional action statements, not reports of real destructive operations. Each
# can-undo path is stipulated to restore precisely the pre-action state, with no loss.
NO_UNDO = [
    'The amber fixture was sealed', 'Allocate the final raffle ticket',
    'The sealed ballot was opened', 'Submit the binding tender',
    'The beacon nonce was spent', 'Disclose the puzzle solution',
    'The spare fuses were melted', 'Issue the final arbitration award',
    'The witness sample was dissolved', 'Redeem the ceramic voucher',
    'The last timing pulse was emitted', 'Transfer the numbered bond',
    'The courier pouch was unsealed', 'Announce the embargoed result',
    'The final challenge was answered', 'Cast the numbered ceramic tile',
]
# Eight reports/eight instructions; path-only, time, holder and cost conditions
# appear without removing facts from either arm. The compact English variants are
# selected before any counting; no longer clausal comparator is substituted later.
CAN_UNDO = [
    ('The orange row was renamed', 'rename journal', None, None, None),
    ('Lower the mixer gain', 'gain preset', None, None, None),
    ('The diagram layer was hidden', 'layer switch', None, None, None),
    ('Reorder the index cards', 'order record', None, None, None),
    ('The atlas palette was changed', 'palette checkpoint', None, '8h', None),
    ('Hide the gallery panel', 'visibility toggle', None, '5d', None),
    ('The rover heading was adjusted', 'heading checkpoint', None, '20m', None),
    ('Move the copper slider', 'position log', None, '40m', None),
    ('The sensor profile was exchanged', 'profile archive', 'technician', None, None),
    ('Rename the marble workspace', 'name ledger', 'owner', None, None),
    ('The piano preset was replaced', 'preset backup', 'performer', None, None),
    ('Change the classroom layout', 'layout record', 'caretaker', None, None),
    ('The brass dial was recalibrated', 'calibration journal', 'maintainer', '3h', None),
    ('Move the violet partition', 'partition snapshot', 'custodian', '9d', None),
    ('The lantern offset was changed', 'offset restore', None, None, '6 credits'),
    ('Swap the ribbon layout', 'layout restore', 'designer', '2d', '7 credits'),
]


def pairs():
    out = []
    for i, action in enumerate(NO_UNDO):
        suffix = 'irreversibly' if i % 2 == 0 else 'irrevocably'
        out.append({'stratum': 'no-undo', 'english': f'{action} {suffix}.', 'ainglish': f'{action}, no-undo.'})
    for action, path, holder, window, cost in CAN_UNDO:
        slots = [path] + ([holder+'-only'] if holder else []) + ([window] if window else []) + ([cost] if cost else [])
        english = f'{action}; reversible via {path}'
        if holder:
            english += f' by {holder} only'
        if window:
            english += f' within {window}'
        if cost:
            english += f'; cost {cost}'
        out.append({'stratum': 'can-undo', 'english': english+'.', 'ainglish': f'{action}, can-undo({"; ".join(slots)}).'})
    return out


def save(name, value):
    with (ROOT/name).open('x') as f:
        json.dump(value, f, indent=2)


def eligible(client):
    suggestions = client.suggestions(proposal=PID)
    source = client.measurement(TARGET)
    current = client.proposal(SLUG, authenticated=True)
    assert current['public_id'] == PID and current['stage'] in ('seconded', 'measured')
    assert client.whoami()['sub'] != source['submitter']['sub']
    assert any(s.get('replicates_hash') == TARGET and s.get('executable_now') is True for s in suggestions['suggestions'])
    assert source['confirmed'] is False, 'Another participant already completed confirmation; re-plan, do not duplicate'
    return source, current


def main(mode, factory):
    module, name = factory.split(':', 1)
    client = getattr(importlib.import_module(module), name)()
    source, proposal = eligible(client)
    limits = client.protocols()['measurement_submission']['manifest'].get('token_delta_limits')
    if mode == 'prepare':
        ROOT.mkdir(exist_ok=False)
        original = source['manifest']
        sampled = pairs()
        assert len(sampled) == 32
        assert all((x['english'], x['ainglish']) not in [(y['english'], y['ainglish']) for y in original['test_set']] for x in sampled)
        assert all(x[side] not in [y[s] for y in original['test_set'] for s in ['english','ainglish']] for x in sampled for side in ['english','ainglish'])
        manifest = {k: copy.deepcopy(original[k]) for k in ['metric','construct','models','settlement_strata','estimand_contract']}
        manifest.update(test_set=sampled, replicates_hash=TARGET)
        plan = token_measurement.prepare({'manifest': manifest, 'replication_target_manifest': original}, token_limits=limits, expected_replicates_hash=TARGET)
        assert plan['manifest']['estimand_contract'] == original['estimand_contract']
        assert plan['comparison_identity_status']['state'] == 'matched'
        checked = client.preflight_attempt(SLUG, plan['manifest'], **plan['mint'])
        assert checked['accepted'] is True
        save('source.json', source); save('proposal.json', proposal); save('plan.json', plan); save('preflight.json', checked)
        save('freeze.json', {'measurement': False, 'target': TARGET, 'manifest_commitment': plan['manifest_commitment'],
             'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'pair_overlap': 0, 'either_arm_exact_reuse': 0, 'target_outcomes_computed': False,
             'boundary': 'Exact source contract retained, including its legacy word loss. Every fictional case stipulates full pre-action restoration or no restoration; no loss slot is introduced. Cost only, not comprehension. No result-dependent comparator selection.'})
        print('prepared', plan['manifest_commitment'], '32 fresh pairs; no tokenizer calls')
        return
    plan = json.loads((ROOT/'plan.json').read_text())
    frozen = json.loads((ROOT/'freeze.json').read_text())
    old = json.loads((ROOT/'proposal.json').read_text())
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == frozen['runner_sha256']
    assert manifest_commitment(plan['manifest']) == frozen['manifest_commitment']
    assert plan['manifest']['estimand_contract'] == source['manifest']['estimand_contract']
    for key in ['english_mapping','predicted_measurement','evidence_contract']:
        assert proposal[key] == old[key], 'Proposal changed after freeze'
    assert not (ROOT/'mint.json').exists(), 'Do not automatically rerun a spent/uncertain attempt'
    checked = client.preflight_attempt(SLUG, plan['manifest'], **plan['mint'])
    assert checked['accepted'] is True
    minted = client.mint_attempt(SLUG, plan['manifest'], **plan['mint'])
    save('mint.json', minted)
    result = token_measurement.run_prepared(plan, minted['attempt']['attempt_id'], token_limits=limits, expected_replicates_hash=TARGET)
    save('result.json', result)
    token_measurement.verify_payload(result['payload'])
    filed = client.measure(SLUG, result['payload']); save('filing.json', filed)
    after = client.measurement(plan['manifest_commitment']); save('after.json', after)
    save('after-proposal.json', client.proposal(SLUG, authenticated=True))
    client.suggestions(proposal=PID)
    print(json.dumps({k:after.get(k) for k in ['manifest_hash','value','value_lo','value_hi','settlement_eligible','reproduced_ok','stratum_results']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare','run'])
    parser.add_argument('--client-factory', required=True)
    args = parser.parse_args(); main(args.mode, args.client_factory)

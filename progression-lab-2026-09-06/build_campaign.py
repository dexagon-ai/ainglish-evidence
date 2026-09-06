"""Freeze new inputs without loading a tokenizer or calling a reader."""
import hashlib
import json
from pathlib import Path
from ainglish import estimand, token_measurement
from ainglish.experiment_audit import audit_items
from snapshot import ROOT, save

SOURCE = '40702354347269f4230a1e2964522d8da3081fc7a188229204a00b833dba0d0e'


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def main():
    pairs = []
    domains = [('library', 'copy', 'ISBN'), ('filesystem', 'file', 'checksum'),
               ('finance', 'account', 'balance'), ('deployment', 'worker', 'image_digest'),
               ('warehouse', 'package', 'mass'), ('publishing', 'document', 'edition'),
               ('laboratory', 'sample', 'concentration'), ('calendar', 'booking', 'start_time')]
    for domain, noun, key in domains:
        for variant in range(2):
            x, y = noun + '-north-' + str(variant), noun + '-south-' + str(variant)
            context = f'In the {domain} identity system, at the stated comparison time, '
            pairs.append({'english': context + f'{x} and {y} refer to one entity.',
                          'ainglish': context + f'{x} same-instance-as({y}).', 'stratum': 'identity'})
            pairs.append({'english': context + f'{x} and {y} have equal {key} values.',
                          'ainglish': context + f'{x} value-equal-to({y}, by={key}).', 'stratum': 'value'})
    manifest = {'metric': 'token_delta', 'models': ['cl100k_base', 'o200k_base', 'p50k_base'],
        'test_set': pairs, 'settlement_strata': [{'id': 'identity', 'weight': 1}, {'id': 'value', 'weight': 1}],
        'estimand_contract': estimand.declaration(unit_span='complete statement',
            contrast='registered identity or named-value statement versus concise complete careful English',
            population='32 complete pairs over eight declared identity systems, equal relation weights, two identifier variants',
            reducer='least_favourable', aggregation_rule='equal pair mean then maximum tokenizer mean; retain each relation separately')}
    save('frozen/instance-token.prepared.json', token_measurement.prepare({'manifest': manifest}))

    # Same consequence task, five answer labels, three equally weighted strata;
    # every complete source input replaced. This does not test all proposal claims.
    facts = [
        ('Museum tickets carry a visit date', 'A museum ticket has no visit date'),
        ('Parcels have a tracking number', 'A parcel has no tracking number'),
        ('Laboratory reports name their units', 'A laboratory report omits its units'),
        ('Published maps include a scale', 'A published map omits its scale'),
        ('Inventory transfers retain the origin', 'An inventory transfer loses its origin'),
        ('Festival badges name a venue', 'A festival badge names no venue'),
        ('Survey responses include a consent record', 'A survey response lacks a consent record'),
        ('Train reservations contain a seat reference', 'A train reservation has no seat reference'),
        ('Exhibition loans record a return date', 'An exhibition loan has no return date'),
        ('Repair orders identify a device', 'A repair order identifies no device'),
        ('School trips list an emergency contact', 'A school trip lists no emergency contact'),
        ('Equipment bookings identify a room', 'An equipment booking identifies no room'),
    ]
    items = []
    for stratum, marker, gold in [('b', 'by-construction', 'A'), ('r', 'by-rule', 'B'), ('i', 'in-practice', 'C')]:
        for index, (claim, exception) in enumerate(facts):
            intent = stratum in ('r', 'i') and index in (1, 5, 9)
            prefix = 'Chosen deliberately. ' if intent else ''
            english = {
                'b': claim + '; the mechanism makes any exception require a change.',
                'r': 'A standing rule requires that ' + claim[0].lower() + claim[1:] + '; exceptions are possible and a responsible owner must fix one.',
                'i': 'In every observation so far, ' + claim[0].lower() + claim[1:] + '; nothing prevents an exception.',
            }[stratum]
            position = len(items) % 5
            options = [x for x in 'ABCDE' if x != gold]
            options.insert(position, gold)
            items.append({'id': f'fresh-{stratum}-{index+1:02}', 'english': prefix + english,
                'ainglish': prefix + claim + ' ' + marker + '.',
                'question': exception + ', system same. Then? A=false B=breach C=new D=valid E=?',
                'options': options, 'answer': gold, 'settlement_stratum': stratum,
                'strata': {'i': int(intent)}})
    for index in range(6):
        answer = 'ABC'[index % 3]
        items.append({'id': f'fresh-control-{index}', 'calibration': True,
            'english': f'Retrieval control {index}: the outcome code is not stated.',
            'ainglish': f'Retrieval control {index}: the correct outcome code is {answer}.',
            'question': 'Which outcome code is correct?', 'options': list('EABCD'), 'answer': answer})
    original = json.loads((ROOT / 'sources' / (SOURCE + '.json')).read_text())
    source_items = original['manifest']['items']
    source_pairs = {(r['english'], r['ainglish']) for r in source_items if not r.get('calibration')}
    assert not source_pairs & {(r['english'], r['ainglish']) for r in items if not r.get('calibration')}
    audit = audit_items(items, require_balanced=True)
    assert audit['ok'], audit
    save('frozen/construction.items.json', items)
    save('frozen/construction.input-audit.json', audit)
    old = json.loads((ROOT.parent / 'usefulness-2026-09-06/probability/probability.numeric.runspec.json').read_text())
    proposal = json.loads((ROOT/'snapshot/construction.proposal.json').read_text())
    spec = {k: old[k] for k in ['panel', 'reader_qualifications', 'admissibility'] if k in old}
    spec.update(slug=proposal['slug'], metric='comprehension_accuracy_delta', seed=2026090581,
        replicates_hash=SOURCE, comparator=original['manifest']['comparator'],
        items_sha256=hashlib.sha256(canonical(items)).hexdigest(),
        settlement_strata=original['manifest']['settlement_strata'],
        calibration_min_gap=0.5, planted_arm='ainglish',
        panel_neff=2,
        attempt={'estimand': 'Fresh-input replication of 40702354: equal-weight b/r/i consequence classification versus complete careful English. Different cached reader roster, exact source strata; no added estimand contract.',
                 'admissibility_gates': ['Source remains active and I remain eligible; source strata and comparator unchanged.', 'Frozen item keys follow the published mapping; all complete pairs disjoint from source.', 'Both qualified cached readers complete the fixed run under declared calibration and cell-yield gates; no retries.'],
                 'planned_sample': {'real_items': 36, 'calibration_items': 6, 'readers': 2,
                                    'mapping_sha256': hashlib.sha256(proposal['english_mapping'].encode()).hexdigest()}})
    save('frozen/construction.runspec.template.json', spec)
    save('frozen/DESIGN.json', {'governance_evidence': True, 'new_tokenizer_or_reader_calls': 0,
        'construction_scope': 'Replicates one consequence-classification task, not all possible-exception, bare-copula, intent-trap or adoption claims. Three regimes and the original five-option scoring retained. Separate reader roster declared, not identical-model reproduction.',
        'instance_scope': '32 complete statements, eight domain labels and two identifier variations per relation. Lexical variation does not create 32 independent grammatical structures. Neither token cost nor a second establishes comprehension.',
        'source_hash': SOURCE, 'no_new_models': True, 'target_retries': 0})
    print('Frozen 32 token pairs and36+6 replication items; no inference or encoding.')


if __name__ == '__main__': main()

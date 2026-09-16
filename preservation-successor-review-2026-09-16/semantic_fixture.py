"""Small, unrun design-review witnesses; not target measurement items or a large bank."""
import json

FORMS = {'they-one': 'that one person or entity',
         'they-many': 'those two or more people or entities'}
WORLDS = [
    {
        'id': 'dispatch-channel',
        'context': 'The dispatch rule depends on the number of referent entities, not their internal members. A message with one recipient entity is handled privately; a message with several recipient entities requires a joint coordination record. The notice does not identify its recipients.',
        'predicate': 'will receive the dispatch request.',
        'question': 'Which action is warranted under the dispatch rule?',
        'choices': {'k7': 'Open an individual delivery ticket.', 'm4': 'Open a shared routing ticket.',
                    'r9': 'Ask the sender to clarify the recipient number.'},
        'one_key': 'k7', 'many_key': 'm4', 'bare_key': 'r9',
    },
    {
        'id': 'acknowledgment-stop',
        'context': 'In this workflow a sole recipient entity permits closure on one signed acknowledgment. Where there are multiple recipient entities, a single acknowledgment never permits closure. An entity may itself represent several people. The recipient identity is not supplied.',
        'predicate': 'will acknowledge this delivery.',
        'question': 'Only one valid acknowledgment has arrived. What does the workflow permit?',
        'choices': {'s2': 'Mark the delivery complete.', 'v8': 'Keep the delivery pending.',
                    'q6': 'Clarify the number of recipient entities first.'},
        'one_key': 's2', 'many_key': 'v8', 'bare_key': 'q6',
    },
    {
        'id': 'credential-route',
        'context': 'The credential policy grants a single addressed entity an individual access instrument. A notice addressing several entities instead enters the coordinated authorization process. The number of people represented by any entity is irrelevant; identity remains unspecified.',
        'predicate': 'will access the archive.',
        'question': 'Which processing route follows from the notice?',
        'choices': {'p3': 'Issue the personal-route credential.', 'h5': 'Start a joint access request.',
                    'b8': 'Request the missing recipient-number information.'},
        'one_key': 'p3', 'many_key': 'h5', 'bare_key': 'b8',
    },
]


def main():
    fixtures = []
    for world in WORLDS:
        for form, expansion in FORMS.items():
            gold = world['one_key'] if form == 'they-one' else world['many_key']
            context = world['context']
            suffix = ' ' + world['predicate']
            row = {'id': world['id'] + '/' + form, 'form': form,
                   'marked': context + ' ' + form + suffix,
                   'careful': context + ' ' + expansion + suffix,
                   'bare': context + ' they' + suffix,
                   'question': world['question'], 'choices': world['choices'],
                   'gold_by_arm': {'marked': gold, 'careful': gold, 'bare': world['bare_key']},
                   'status': 'unrun_review_fixture_not_sdk_panel_item'}
            assert row['marked'].replace(form, expansion) == row['careful']
            assert row['gold_by_arm']['marked'] == row['gold_by_arm']['careful']
            assert row['gold_by_arm']['bare'] != row['gold_by_arm']['marked']
            assert gold in row['choices']
            fixtures.append(row)
    ontology = [
        {'referent_entities': 1, 'represented_people': 9, 'form': 'they-one',
         'warranted_people_count': 'unknown_from_marker_alone'},
        {'referent_entities': 2, 'represented_people': 0, 'form': 'they-many',
         'warranted_people_count': 'unknown_from_marker_alone'},
    ]
    for case in ontology:
        assert (case['referent_entities'] == 1) == (case['form'] == 'they-one')
    nonclaims = []
    for form in FORMS:
        for category in ('gender', 'known_identity', 'unanimity', 'all_members', 'collective_action'):
            nonclaims.append({'form': form, 'category': category,
                              'from_number_marker_alone': 'not_entailed',
                              'explicit_shared_context_positive_control_required': True})
    print(json.dumps({'kind': 'unrun-semantic-review-fixtures-v1', 'model_calls': 0,
                      'checks': 'passed', 'examples': fixtures, 'ontology_checks': ontology,
                      'nonclaim_coverage_requirements': nonclaims,
                      'limitation': 'These are elementary review witnesses, not independent-world counts, a complete instrument, or evidence of reader performance.'}, indent=2))


if __name__ == '__main__':
    main()

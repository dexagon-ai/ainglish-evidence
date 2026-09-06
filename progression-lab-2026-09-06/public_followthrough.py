"""Export public proposal facts without personalised task suggestions or private threads."""
import hashlib
import json
from snapshot import ROOT, save


def main():
    source = (ROOT / 'FOLLOWTHROUGH.json').read_bytes()
    data = json.loads(source)
    keys = ['label', 'public_id', 'slug', 'stage', 'publication_status',
            'mapping_sha256', 'evidence_contract', 'evidence_readiness',
            'measurements', 'colony_thread_url', 'ratified_at']
    result = {'kind': 'ainglish.public-campaign-followthrough.v1', 'at': data['at'],
        'source_snapshot_sha256': hashlib.sha256(source).hexdigest(),
        'records': [{k: row[k] for k in keys} for row in data['records']],
        'boundary': 'Eight campaign proposals plus one preparatory candidate. Dated proposal facts, not a claim that a submitted measurement, an open ballot, or a prepared handoff completed an evidence gate. No personalised suggestions, private messages or discussion-author profiles are included.'}
    save('FOLLOWTHROUGH-PUBLIC.json', result)
    print('Published-field export:', len(result['records']), 'records')


if __name__ == '__main__':
    main()

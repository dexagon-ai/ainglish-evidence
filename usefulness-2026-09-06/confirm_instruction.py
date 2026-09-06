"""Confirm the corrected item-specific evidence annotation after source review."""
import json
from pathlib import Path
from ainglish import panel
from ainglish_moderation import ModerationClient
from local_colony_auth import ainglish_client, load_api_key, totp_now

ROOT=Path(__file__).resolve().parent
APPROVAL='33ead8c9-738e-4772-96b9-d4d700b3cb14'
TARGET='8a16cda8-0386-4b98-8ae0-4f4b41a6423f'
SOURCE='https://raw.githubusercontent.com/reticuli-labs/panel-artifacts/4f617353cf2f771432cd04d143e97e4db7e958db/thisonce-appl-2026-08-31/items.json'


def main():
    destination=ROOT/'instruction-annotation.json'
    assert not destination.exists(), 'Read and reconcile existing action; do not repeat it'
    items,sha=panel.fetch_items(SOURCE,'7463a0a4fca412475403acad2ab14c191b6199ddc31cbdae20f3b9374f813c40')
    affected=[r for r in items if r.get('settlement_stratum')=='dx:project-scope' and 'from-now-on' in r['ainglish']]
    assert len(affected)==10 and all(r['answer']=='no' for r in affected)
    qualified=[r for r in affected if 'here' in r['ainglish']]
    assert [r['id'] for r in qualified]==['ta-dx-project-scope-115']
    c=ainglish_client();c.suggestions()
    p=c.proposal('this-once-from-now-on-does-this-instruction-apply-to-this-ta',authenticated=True)
    assert 'all later comparable work' in p['english_mapping']
    m=ModerationClient(colony_api_key=load_api_key(),totp=totp_now,use_env=False)
    before=m.approval(APPROVAL)['approval']
    assert before['status']=='pending' and before['target']['id']==TARGET
    assert before['requested_by_sub']=='040b6f79-a867-46d4-8069-fd6143bd9e20'
    decision=before['evidence_decision']
    assert decision['state']=='record_only' and 'NINE' in decision['public_explanation'] and '115' in decision['public_explanation']
    # Exact source arms and the entire current mapping were manually inspected
    # before this confirmation. This is not an automated semantic classifier.
    receipt=m.confirm_approval(APPROVAL,idempotency_key='dexagon-instruction-nine-keys-20260906')
    after=m.approval(APPROVAL)['approval']
    row=c.measurement('85a36ba6b6deb7982e7ffd8627b343f3a08b099116d8ae9a0827cb1cc87748f6')
    report={'source_url':SOURCE,'items_sha256':sha,'manual_review':'Nine unrestricted comparable-work keys conflict with mapping; the explicit here scope in item115 remains no.',
            'affected_ids':[r['id'] for r in affected if r['id']!='ta-dx-project-scope-115'],
            'excluded_id':'ta-dx-project-scope-115','approval_id':APPROVAL,'target_attempt_id':TARGET,
            'receipt':receipt,'status':after['status'],'measurement_readback':row,
            'retention':'No cells, answers or source bytes changed; record_only is not deletion or rescore.'}
    with destination.open('x') as handle:json.dump(report,handle,indent=2,ensure_ascii=False);handle.write('\n')
    print(json.dumps({'approval_id':APPROVAL,'status':after['status'],'measurement_keys':list(row)}))


if __name__=='__main__':main()

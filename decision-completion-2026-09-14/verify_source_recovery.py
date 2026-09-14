"""Verify a recovered public bank without editing a manifest or calling readers."""
from datetime import datetime, timezone
import json
from pathlib import Path
from ainglish.client import AinglishClient
from ainglish.panel import fetch_items
from ainglish.experiment_audit import audit_replication_items

ROOT = Path(__file__).resolve().parent
SOURCE = '6402298c595e40c70709bfb1aa4c16a24aed9f0effd939fad17b336a91eae05c'
PIN = '00b095dcdead7a457ef254879b16063a0109c38228f246f1a40c22117d03f1ff'
URL = 'https://raw.githubusercontent.com/reticuli-labs/panel-artifacts/01f16411ac0b63bb8c66ca83f699e5fdcae27674/repeat-restore-comp-2026-08-31/items.json'


def main():
    original = AinglishClient(use_env=False).measurement(SOURCE)
    assert original['manifest']['items_sha256'] == PIN
    items, actual = fetch_items(URL, PIN)
    same = audit_replication_items(items, items)
    assert same['complete_pairs']['fresh_fraction'] == 0
    report = {'checked_at': datetime.now(timezone.utc).isoformat(),
        'source_measurement': SOURCE, 'manifest_items_url': original['manifest']['items_url'],
        'recovered_url': URL, 'parsed_items_sha256': actual, 'rows': len(items),
        'manifest_item_counts': original['manifest']['item_counts'],
        'same_input_diagnostic': same,
        'boundary': 'Exact bank recovered for inspection. Same-input overlap diagnostic only: no fresh replication, reader call, manifest change, confirmation or source-quality certification.'}
    (ROOT / 'source-recovery.json').write_text(json.dumps(report, indent=2) + '\n')
    print('RECOVERED', len(items), actual, 'same_input_fresh_fraction', same['complete_pairs']['fresh_fraction'])


if __name__ == '__main__':
    main()

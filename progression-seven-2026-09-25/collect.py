"""Recover public audit evidence, with bounded downloads. No scientific calls/writes."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

from ainglish.client import AinglishClient

ROOT = Path(__file__).resolve().parent
HASHES = ['e47e7f73745b8d74c253ec83c5ac14657e34dcc612346c169ce90e6e079b8f72',
          '5e0897021cfec1f5b8941d388ab03fc837e0d763f7cf625e8e9c8e3254360050']
IDS = ['a-4y6nergvf2fc2wmt', 'a-ppyzdf5qk6z67aty', 'a-twt7mcv776hnrz2f',
       'a-ef4rsdm2ksnkdz2r', 'a-mbxazvtshv2excx5', 'a-gsp0xkxk1sq5pgn5',
       'a-hz2zrrjkjfjvjgdb', 'a-mv841prke9x9e5cm', 'a-hvrcz8j6qcp8amvr']


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def write(path, x):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(x, indent=2, ensure_ascii=False) + '\n')


def acquire():
    a = AinglishClient(use_env=False)
    dest = ROOT / 'overslip'
    if (dest/'source.json').exists():
        raise RuntimeError('Public evidence already captured: verify rather than replace history')
    for label, h in zip(('source', 'replica'), HASHES):
        m = a.measurement(h)
        write(dest/(label+'.json'), m)
        url = m['manifest']['items_url']
        with urlopen(Request(url, headers={'User-Agent':'Dexagon-evidence-audit'}), timeout=40) as r:
            blob = r.read(2*1024*1024+1)
        assert len(blob) <= 2*1024*1024
        (dest/(label+'-carrier.json')).write_bytes(blob)
        print(label, len(blob), hashlib.sha256(blob).hexdigest(), flush=True)
    snapshot = {'captured_at': datetime.now(timezone.utc).isoformat(), 'proposals': []}
    for ident in IDS:
        p = a.proposal(ident)
        snapshot['proposals'].append({k:p.get(k) for k in (
            'public_id','slug','title','kind','stage','form','english_mapping','predicted_measurement',
            'evidence_contract','ratification','ballot_closure','colony_thread_url','author_work_notices')})
    write(ROOT/'live-before.json', snapshot)


if __name__ == '__main__':
    acquire()

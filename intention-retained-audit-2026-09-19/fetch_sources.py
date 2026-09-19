"""Mirror only three already-public JSON artifacts, with pinned hashes and size limits."""
import hashlib
import json
from urllib.request import urlopen
from audit import ROOT, INDEX_SHA


def fetch(url, sha, size=None):
    assert url.startswith('https://paste.c-net.org/')
    with urlopen(url, timeout=30) as response:
        raw = response.read(200001)
    assert len(raw) < 200001 and hashlib.sha256(raw).hexdigest() == sha
    assert size is None or len(raw) == size
    return raw


if __name__ == '__main__':
    raw = fetch('https://paste.c-net.org/uo5f2897676w', INDEX_SHA)
    index = json.loads(raw)
    (ROOT / 'source-index.json').write_bytes(raw)
    for name in ('scientific_cells', 'calibration_cells'):
        ref = index['retained_artifacts'][name]
        (ROOT / (name + '.json')).write_bytes(fetch(ref['url'], ref['sha256'], ref['bytes']))
    print('Mirrored three hash-verified public JSON artifacts; no runner fetched or executed.')

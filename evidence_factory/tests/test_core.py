from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from evidence_factory.core import CampaignError, CampaignIndex, content_sha256


class CampaignIndexTests(unittest.TestCase):
    def make_index(self, root: Path) -> Path:
        spec = {"slug": "example", "metric": "comprehension_accuracy_delta"}
        spec_path = root / "runspec.json"
        encoded = (json.dumps(spec, indent=2) + "\n").encode()
        spec_path.write_bytes(encoded)
        payload = {
            "kind": "ainglish.campaign-index.v1",
            "campaigns": {
                "example": {
                    "runspec": "runspec.json",
                    "runspec_sha256": hashlib.sha256(encoded).hexdigest(),
                    "receipt_stem": "example",
                    "gpu_index": 0,
                }
            },
        }
        payload["content_sha256"] = content_sha256(payload)
        path = root / "index.json"
        path.write_text(json.dumps(payload, indent=2) + "\n")
        return path

    def test_loads_digest_pinned_index(self):
        with tempfile.TemporaryDirectory() as temporary:
            index = CampaignIndex.load(self.make_index(Path(temporary)))
            self.assertEqual(index.entries[0].name, "example")
            self.assertEqual(index.entries[0].gpu_index, 0)

    def test_refuses_index_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.make_index(Path(temporary))
            payload = json.loads(path.read_text())
            payload["campaigns"]["example"]["gpu_index"] = 1
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(CampaignError, "content drift"):
                CampaignIndex.load(path)

    def test_refuses_runspec_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.make_index(root)
            (root / "runspec.json").write_text("{}\n")
            with self.assertRaisesRegex(CampaignError, "runspec drift"):
                CampaignIndex.load(path)

    def test_refuses_path_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.make_index(root)
            payload = json.loads(path.read_text())
            payload["campaigns"]["example"]["runspec"] = "../runspec.json"
            unsealed = dict(payload)
            del unsealed["content_sha256"]
            payload["content_sha256"] = content_sha256(unsealed)
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(CampaignError, "escapes"):
                CampaignIndex.load(path)


if __name__ == "__main__":
    unittest.main()

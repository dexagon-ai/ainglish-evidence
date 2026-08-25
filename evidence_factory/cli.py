"""Zero-cost validation CLI for a frozen campaign index."""

from __future__ import annotations

import argparse
import json

from .core import CampaignError, CampaignIndex, gpu_snapshots


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("index")
    parser.add_argument("--show-gpus", action="store_true")
    args = parser.parse_args()
    try:
        index = CampaignIndex.load(args.index)
        payload = {
            "status": "ok",
            "kind": index.kind,
            "content_sha256": index.content_digest,
            "campaigns": [
                {
                    "name": row.name,
                    "runspec": str(row.spec_path),
                    "runspec_sha256": row.spec_sha256,
                    "receipt_stem": row.receipt_stem,
                    "gpu_index": row.gpu_index,
                }
                for row in index.entries
            ],
        }
        if args.show_gpus:
            payload["gpus"] = [row.__dict__ for row in gpu_snapshots()]
        print(json.dumps(payload, indent=2))
    except CampaignError as exc:
        raise SystemExit(f"REFUSING: {exc}") from None


if __name__ == "__main__":
    main()

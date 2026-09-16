"""Prepare numeric-only operating-characteristic inputs, using the actual SDK PRF.

No language prompts, answer keys, reader calls, API writes, or target bank are made.
Binary matrices are temporary reproducible build artifacts, not publication data.
"""
from array import array
import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import struct
import sys

from ainglish import panel

SEEDS = (16092601, 16092602)
FORMS = ("numeric-form-0", "numeric-form-1")
READERS = ("synthetic-reader-0", "synthetic-reader-1")
DRAWS = 2000


def prepare(n, run, directory):
    seed = SEEDS[run]
    items = [[f"numeric-only-f{form}-i{i:05d}" for i in range(n)] for form in range(2)]
    arms = bytes(int(panel.arm_for(seed, reader, ident) == "ainglish")
                 for form in range(2) for ident in items[form] for reader in READERS)
    path = directory / f"matrix-n{n}-run{run}.bin"
    with path.open("wb") as handle:
        handle.write(struct.pack("<8sIIII", b"AINGOC1\0", n, DRAWS, 2, 2))
        handle.write(arms)
        for form in range(2):
            for draw in range(DRAWS):
                weights = array("H", [0]) * n
                for position in range(n):
                    index = panel._attested_draw_index(seed, draw, position, n,
                                                       stratum=FORMS[form])
                    weights[index] += 1
                assert sum(weights) == n
                if sys.byteorder != "little":
                    weights.byteswap()
                handle.write(weights.tobytes())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"n_worlds_per_form": n, "run": run, "seed": seed, "draws": DRAWS,
            "sha256": digest, "bytes": path.stat().st_size,
            "arm_counts_by_form_reader": [
                [{"english": sum(arms[(f*n+i)*2+r] == 0 for i in range(n)),
                  "ainglish": sum(arms[(f*n+i)*2+r] == 1 for i in range(n))}
                 for r in range(2)] for f in range(2)]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sizes", nargs="+", type=int, default=[300, 600, 1200])
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    assert panel.INTERVAL_BOOTSTRAP_DRAWS == DRAWS
    assert panel.INTERVAL_PROVENANCE_MAX_CELLS == 5000
    receipts = []
    for n in args.sizes:
        if not 4 <= n <= 1250:
            raise ValueError("two forms times two readers must fit 5,000 cells")
        for run in range(2):
            receipt = prepare(n, run, args.output)
            receipts.append(receipt)
            print(json.dumps(receipt), flush=True)
    (args.output / "matrix-receipts.json").write_text(json.dumps({
        "kind": "numeric-bootstrap-design-inputs-v1", "sdk_version": version("ainglish"),
        "model_calls": 0, "forms": FORMS, "readers": READERS, "matrices": receipts,
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()

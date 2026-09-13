"""Run the three predeclared comparisons, with all attempts minted before exposure.

The official panel's mint callback consumes a genuine pre-opened SDK receipt;
it does not create a second attempt. No scoring or reader behavior is replaced.
"""
import json
from pathlib import Path
import shutil

from ainglish.client import manifest_commitment
from ainglish.panel import (
    _attempt_settings, _planned_panel_manifest, _run_preregistered_panel,
    admissibility_gate_statement, ask, calibration_gate_statement,
    prepare_reader_instruments,
)
from local_colony_auth import ainglish_client

HERE = Path(__file__).resolve().parent


def save(name, data):
    with (HERE / name).open("x") as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write("\n")


class AlreadyMinted:
    def __init__(self, client, descriptor, opened):
        self.client, self.descriptor, self.opened = client, descriptor, opened
        self.used = False

    def __getattr__(self, name):
        return getattr(self.client, name)

    def mint_attempt(self, slug, manifest, **settings):
        assert not self.used, "One execution per pre-opened attempt"
        assert slug == self.descriptor["slug"]
        assert manifest_commitment(manifest) == self.descriptor["manifest_commitment"]
        assert settings == self.descriptor["settings"], "Attempt settings changed after mint"
        actual = self.client.attempt(self.opened["attempt"]["attempt_id"])
        row = actual.get("attempt", actual)
        assert row["state"] == "open", row["state"]
        self.used = True
        return self.opened


def main():
    assert shutil.disk_usage(HERE).free > 20 * 1024 ** 3
    assert not (HERE / "only-focus-batch-attempts.json").exists(), "No automatic re-entry or rerun"
    client = ainglish_client()
    frozen = json.loads((HERE / "only-focus-proposal-contract.json").read_text())

    def fresh():
        p = client.proposal(frozen["public_id"], authenticated=True)
        assert {k: p[k] for k in frozen} == frozen, "Proposal content changed"
        assert p["stage"] in ("seconded", "measured"), p["stage"]
        assert p["author_work_notices"]["active"] is None
        return p

    first = fresh()
    work = next(w for w in first["evidence_readiness"]["work_items"]
                if w["metric"] == "comprehension_accuracy_delta")
    assert work["state"] == "submit_original", work
    prepared = []
    # Validate every exact manifest before opening any obligation.
    for contrast in ("careful", "placement", "bare"):
        name = "only-focus-" + contrast
        spec = json.loads((HERE / (name + "-runspec.json")).read_text())
        prepare_reader_instruments(spec)
        planned = _planned_panel_manifest(spec)
        declared = json.loads((HERE / (name + "-planned-manifest.json")).read_text())
        assert planned == declared
        gates = [calibration_gate_statement(spec), admissibility_gate_statement(spec)]
        settings = _attempt_settings(spec["attempt"], gates)
        prepared.append((name, spec, planned, settings))
    receipts = []
    for name, spec, planned, settings in prepared:
        fresh()
        opened = client.mint_attempt(spec["slug"], planned, **settings)
        descriptor = {"slug": spec["slug"], "manifest_commitment": manifest_commitment(planned),
                      "settings": settings}
        receipt = {"name": name, "descriptor": descriptor, "opened": opened}
        save(name + "-mint.json", receipt)
        receipts.append(receipt)
        print("PRE-EXPOSURE MINT", name, opened["attempt"]["attempt_id"], flush=True)
    save("only-focus-batch-attempts.json", receipts)
    for (name, spec, planned, settings), receipt in zip(prepared, receipts):
        fresh()
        adapter = AlreadyMinted(client, receipt["descriptor"], receipt["opened"])
        result = _run_preregistered_panel(spec, spec, ask, adapter,
                                         receipt_dir=str(HERE), receipt_stem=name)
        # The official runner files/aborts its exact result. Preserve fresh public
        # readback; any subsequent study fault is not permission to hide this row.
        save(name + "-after-attempt.json", client.attempt(receipt["opened"]["attempt"]["attempt_id"]))
        if result is None:
            raise SystemExit("Study stopped honestly; inspect and close any not-yet-run attempts before resuming")
        save(name + "-result.json", result)
        save(name + "-after-proposal.json", client.proposal(frozen["public_id"], authenticated=True))
        print("COMPARISON FINISHED", name, flush=True)


if __name__ == "__main__":
    main()

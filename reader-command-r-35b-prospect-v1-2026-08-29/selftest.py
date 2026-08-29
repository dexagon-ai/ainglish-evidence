#!/usr/bin/env python3
"""Mutation-test the fail-closed Command R host preflight without any network or model call."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("command_r_run_once", ROOT / "run_once.py")
runner = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(runner)


def checked(name: str) -> dict:
    return runner.module.checked(ROOT / name)


def main() -> None:
    plan = checked("development-command-r-plan.json")
    candidate = plan["candidate"]
    runner.module.gpu_rows = lambda: [
        {"index": 0, "name": "GPU", "free_mib": 20000, "utilization": 0},
        {"index": 1, "name": "GPU", "free_mib": 20000, "utilization": 0},
    ]
    state = {"resident": [], "digest": candidate["source_manifest_sha256"]}
    runner.module.get = lambda _endpoint, path: (
        {"version": "0.32.7"} if path == "/api/version"
        else {"models": state["resident"]} if path == "/api/ps"
        else {"models": [{"name": candidate["source_model"], "digest": state["digest"]}]}
    )
    observed = {
        "capabilities": candidate["capabilities"],
        "details": candidate["details"],
        "template": "x" * candidate["template_length_chars"],
    }
    # Bind the synthetic template to the frozen digest without weakening production validation.
    original_sha = runner.hashlib.sha256

    class FakeHash:
        def __init__(self, value: bytes):
            self.value = value

        def hexdigest(self) -> str:
            if self.value == observed["template"].encode():
                return candidate["template_sha256"]
            return original_sha(self.value).hexdigest()

    runner.hashlib.sha256 = FakeHash
    runner.module.post = lambda _endpoint, path, _payload: observed if path == "/api/show" else {}
    packet, receipt = runner.validate(plan)
    assert len(packet["items"]) == 24 and receipt["development_result_sha256"] is None

    def refuses(mutator) -> None:
        value = copy.deepcopy(plan)
        mutator(value)
        try:
            runner.validate(value)
        except SystemExit:
            return
        raise AssertionError("preflight accepted an adversarial mutation")

    refuses(lambda value: value["candidate"].update(source_manifest_sha256="0" * 64))
    refuses(lambda value: value["candidate"].update(capabilities=["completion"]))
    refuses(lambda value: value["candidate"]["details"].update(parameter_size="32.4B"))
    refuses(lambda value: value["candidate"].update(template_length_chars=2865))
    state["resident"] = [{"name": "unexpected"}]
    refuses(lambda _value: None)
    state["resident"] = []

    holdout = checked("holdout-command-r-plan.json")
    try:
        runner.validate(holdout)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("holdout activated without the sealed development result")
    runner.hashlib.sha256 = original_sha
    print(json.dumps({
        "status": "passed",
        "happy_path": 1,
        "rejected_mutants": 5,
        "holdout_without_development": "refused",
        "network_calls": 0,
        "model_calls": 0,
    }, indent=2))


if __name__ == "__main__":
    main()

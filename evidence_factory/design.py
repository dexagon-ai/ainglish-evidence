"""Build and validate a fail-closed reader-evidence design envelope."""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .core import canonical_json, content_sha256


_ROLES = {
    "claim_carrier",
    "bare_diagnostic",
    "learnability_diagnostic",
    "recertification",
}
_CLAIM_COMPARATORS = {
    "complete-careful-english-v1",
    "shortest-adequate-careful-control-v1",
}
_PANEL_METRICS = {
    "comprehension_accuracy_delta",
    "interpretation_entropy_delta",
    "robustness_delta",
    "tag_fidelity",
}
_REQUIRED_GATES = {
    "mint_before_reader_spend": True,
    "calibration_both_arms": True,
    "retain_all_admissible_outcomes": True,
    "no_scientific_cell_retry": True,
    "complete_pair_identity": True,
}


class EvidenceDesignError(RuntimeError):
    """A zero-reader refusal caused by an incomplete or drifting design."""


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceDesignError(f"cannot read JSON artifact {path}: {exc}") from exc


def _relative_file(root: Path, relative: Any, label: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise EvidenceDesignError(f"{label} must be a non-empty relative path")
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise EvidenceDesignError(f"{label} escapes the design directory") from exc
    if not resolved.is_file():
        raise EvidenceDesignError(f"{label} does not exist: {resolved}")
    return resolved


def _item_counts(path: Path) -> tuple[int, int]:
    rows = _read_json(path)
    if not isinstance(rows, list) or not rows:
        raise EvidenceDesignError(f"items file must be a non-empty JSON list: {path}")
    identifiers: set[str] = set()
    calibration = 0
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise EvidenceDesignError(f"{path.name}[{index}] must be an object")
        item_id = row.get("id")
        if not isinstance(item_id, str) or not item_id:
            raise EvidenceDesignError(f"{path.name}[{index}].id must be non-empty")
        if item_id in identifiers:
            raise EvidenceDesignError(f"{path.name} repeats item id {item_id!r}")
        identifiers.add(item_id)
        calibration += row.get("calibration") is True
    return len(rows) - calibration, calibration


@dataclass(frozen=True)
class EvidenceDesign:
    path: Path
    payload: Mapping[str, Any]
    content_digest: str

    @classmethod
    def load(cls, path: str | Path) -> "EvidenceDesign":
        design_path = Path(path).resolve()
        payload = _read_json(design_path)
        if not isinstance(payload, dict):
            raise EvidenceDesignError("evidence design must be a JSON object")
        if payload.get("kind") != "ainglish.reader-evidence-design.v1":
            raise EvidenceDesignError("kind must be ainglish.reader-evidence-design.v1")
        expected = payload.get("content_sha256")
        if not isinstance(expected, str) or len(expected) != 64:
            raise EvidenceDesignError("content_sha256 must be a lowercase SHA-256 digest")
        unsealed = dict(payload)
        del unsealed["content_sha256"]
        actual = content_sha256(unsealed)
        if actual != expected:
            raise EvidenceDesignError(
                f"evidence design drift: expected {expected}, computed {actual}"
            )

        slug = payload.get("slug")
        revision = payload.get("proposal_revision")
        population = payload.get("population")
        if not isinstance(slug, str) or not slug:
            raise EvidenceDesignError("slug must be non-empty")
        if not isinstance(revision, str) or not revision:
            raise EvidenceDesignError("proposal_revision must be non-empty")
        if not isinstance(population, str) or not population.strip():
            raise EvidenceDesignError("population must state the frozen estimand population")

        forms = payload.get("forms")
        if (
            not isinstance(forms, list)
            or not forms
            or any(not isinstance(form, str) or not form for form in forms)
            or len(set(forms)) != len(forms)
        ):
            raise EvidenceDesignError("forms must be a non-empty unique string list")

        gates = payload.get("quality_gates")
        if not isinstance(gates, dict):
            raise EvidenceDesignError("quality_gates must be an object")
        for name, required in _REQUIRED_GATES.items():
            if gates.get(name) is not required:
                raise EvidenceDesignError(f"quality_gates.{name} must be true")
        lineages = gates.get("qualified_reader_lineages_min")
        if isinstance(lineages, bool) or not isinstance(lineages, int) or lineages < 2:
            raise EvidenceDesignError(
                "quality_gates.qualified_reader_lineages_min must be an integer >= 2"
            )

        campaigns = payload.get("campaigns")
        if not isinstance(campaigns, dict) or not campaigns:
            raise EvidenceDesignError("campaigns must be a non-empty object")
        claims_by_form = {form: 0 for form in forms}
        bare_by_form = {form: 0 for form in forms}
        seen_item_digests: dict[str, str] = {}
        for name, campaign in campaigns.items():
            if not isinstance(name, str) or not name or not isinstance(campaign, dict):
                raise EvidenceDesignError("campaign names and values must be non-empty objects")
            role = campaign.get("role")
            form = campaign.get("form")
            metric = campaign.get("metric")
            if role not in _ROLES:
                raise EvidenceDesignError(f"{name}.role must be one of {sorted(_ROLES)}")
            if form not in forms:
                raise EvidenceDesignError(f"{name}.form is not declared in forms")
            if metric not in _PANEL_METRICS:
                raise EvidenceDesignError(f"{name}.metric is not a supported panel metric")
            comparator = campaign.get("comparator")
            if not isinstance(comparator, dict) or not isinstance(comparator.get("kind"), str):
                raise EvidenceDesignError(f"{name}.comparator.kind must be declared")
            comparator_kind = comparator["kind"]
            if role in ("claim_carrier", "recertification"):
                claims_by_form[form] += 1
                if comparator_kind not in _CLAIM_COMPARATORS:
                    raise EvidenceDesignError(
                        f"{name}: a claim carrier must use a complete careful-English comparator"
                    )
            elif role == "bare_diagnostic":
                bare_by_form[form] += 1
                if comparator_kind != "balanced-bare-english-v1":
                    raise EvidenceDesignError(
                        f"{name}: a bare diagnostic must use balanced-bare-english-v1"
                    )

            items_path = _relative_file(design_path.parent, campaign.get("items"), f"{name}.items")
            expected_items = campaign.get("items_sha256")
            actual_items = hashlib.sha256(items_path.read_bytes()).hexdigest()
            if expected_items != actual_items:
                raise EvidenceDesignError(
                    f"{name}: item drift: expected {expected_items}, computed {actual_items}"
                )
            prior = seen_item_digests.get(actual_items)
            if prior is not None:
                raise EvidenceDesignError(
                    f"{name} reuses the complete item file from {prior}; diagnostics and carriers need separate frozen inputs"
                )
            seen_item_digests[actual_items] = name
            real, calibration = _item_counts(items_path)
            planned = campaign.get("planned_sample")
            if not isinstance(planned, dict):
                raise EvidenceDesignError(f"{name}.planned_sample must be an object")
            if planned.get("real_items") != real or planned.get("calibration_items") != calibration:
                raise EvidenceDesignError(
                    f"{name}.planned_sample does not match its frozen item file ({real} real, {calibration} calibration)"
                )
            if real < 16 or calibration < 4:
                raise EvidenceDesignError(
                    f"{name} needs at least 16 scientific and 4 calibration items"
                )

        for form in forms:
            if claims_by_form[form] != 1:
                raise EvidenceDesignError(
                    f"form {form!r} needs exactly one careful-English claim carrier; found {claims_by_form[form]}"
                )
            if bare_by_form[form] > 1:
                raise EvidenceDesignError(
                    f"form {form!r} has more than one bare-English diagnostic"
                )
        return cls(design_path, payload, expected)


def freeze_design(draft_path: str | Path, output_path: str | Path) -> EvidenceDesign:
    """Digest-pin every item file, seal a draft, write it, and validate the result."""

    draft = Path(draft_path).resolve()
    output = Path(output_path).resolve()
    payload = _read_json(draft)
    if not isinstance(payload, dict):
        raise EvidenceDesignError("draft must be a JSON object")
    if "content_sha256" in payload:
        raise EvidenceDesignError("draft already carries content_sha256; freeze only unsealed drafts")
    campaigns = payload.get("campaigns")
    if not isinstance(campaigns, dict):
        raise EvidenceDesignError("draft campaigns must be an object")
    for name, campaign in campaigns.items():
        if not isinstance(campaign, dict):
            raise EvidenceDesignError(f"{name} must be an object")
        items_path = _relative_file(draft.parent, campaign.get("items"), f"{name}.items")
        campaign["items_sha256"] = hashlib.sha256(items_path.read_bytes()).hexdigest()
        real, calibration = _item_counts(items_path)
        planned = campaign.setdefault("planned_sample", {})
        if not isinstance(planned, dict):
            raise EvidenceDesignError(f"{name}.planned_sample must be an object")
        planned.setdefault("real_items", real)
        planned.setdefault("calibration_items", calibration)
    payload["content_sha256"] = content_sha256(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return EvidenceDesign.load(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("draft")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        frozen = freeze_design(args.draft, args.output)
    except EvidenceDesignError as exc:
        raise SystemExit(f"REFUSING: {exc}") from None
    print(json.dumps({
        "status": "passed",
        "output": str(frozen.path),
        "content_sha256": frozen.content_digest,
    }, indent=2))


if __name__ == "__main__":
    main()

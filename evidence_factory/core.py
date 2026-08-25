"""Fail-closed orchestration around the official Ainglish panel harness."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Callable, Iterable, Mapping, Sequence
import urllib.request


_HEX_64 = re.compile(r"[0-9a-f]{64}")
_RECEIPT_SUFFIXES = (
    ".abort.json",
    ".calibration.cells.json",
    ".cells.json",
    ".measurement.json",
)


class CampaignError(RuntimeError):
    """A zero-cost refusal raised before attempt mint or reader spend."""


def canonical_json(value: Any) -> bytes:
    """Return the UTF-8 canonical JSON representation used for content pins."""

    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")


def content_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CampaignError(f"cannot read JSON artifact {path}: {exc}") from exc


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _HEX_64.fullmatch(value):
        raise CampaignError(f"{label} must be a lowercase SHA-256 digest")
    return value


@dataclass(frozen=True)
class CampaignEntry:
    name: str
    spec_path: Path
    spec_sha256: str
    receipt_stem: str
    gpu_index: int | None


@dataclass(frozen=True)
class CampaignIndex:
    """A digest-pinned collection of campaign run specifications."""

    path: Path
    kind: str
    entries: tuple[CampaignEntry, ...]
    content_digest: str

    @classmethod
    def load(cls, path: str | Path) -> "CampaignIndex":
        index_path = Path(path).resolve()
        payload = _read_json(index_path)
        if not isinstance(payload, dict):
            raise CampaignError("campaign index must be a JSON object")
        kind = payload.get("kind")
        if not isinstance(kind, str) or not kind.startswith("ainglish."):
            raise CampaignError("campaign index kind must be an ainglish.* identifier")
        expected = _require_sha256(payload.get("content_sha256"), "content_sha256")
        unsealed = dict(payload)
        del unsealed["content_sha256"]
        actual = content_sha256(unsealed)
        if actual != expected:
            raise CampaignError(
                f"campaign index content drift: expected {expected}, computed {actual}"
            )
        raw_campaigns = payload.get("campaigns")
        if not isinstance(raw_campaigns, dict) or not raw_campaigns:
            raise CampaignError("campaign index needs a non-empty campaigns object")
        entries: list[CampaignEntry] = []
        seen_stems: set[str] = set()
        for name, meta in sorted(raw_campaigns.items()):
            if not isinstance(name, str) or not name or not isinstance(meta, dict):
                raise CampaignError("campaign names and metadata must be non-empty objects")
            relative = meta.get("runspec")
            if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
                raise CampaignError(f"{name}: runspec must be a relative path")
            spec_path = (index_path.parent / relative).resolve()
            try:
                spec_path.relative_to(index_path.parent)
            except ValueError as exc:
                raise CampaignError(f"{name}: runspec escapes the campaign directory") from exc
            spec_digest = _require_sha256(meta.get("runspec_sha256"), f"{name}.runspec_sha256")
            try:
                actual_spec = hashlib.sha256(spec_path.read_bytes()).hexdigest()
            except OSError as exc:
                raise CampaignError(f"{name}: cannot read {spec_path}: {exc}") from exc
            if actual_spec != spec_digest:
                raise CampaignError(
                    f"{name}: runspec drift: expected {spec_digest}, computed {actual_spec}"
                )
            stem = meta.get("receipt_stem", name)
            if not isinstance(stem, str) or not re.fullmatch(r"[A-Za-z0-9._-]+", stem):
                raise CampaignError(f"{name}: invalid receipt_stem")
            if stem in seen_stems:
                raise CampaignError(f"duplicate receipt_stem {stem!r}")
            seen_stems.add(stem)
            gpu_index = meta.get("gpu_index")
            if gpu_index is not None and (isinstance(gpu_index, bool) or not isinstance(gpu_index, int) or gpu_index < 0):
                raise CampaignError(f"{name}: gpu_index must be a non-negative integer")
            entries.append(CampaignEntry(name, spec_path, spec_digest, stem, gpu_index))
        return cls(index_path, kind, tuple(entries), expected)


@dataclass(frozen=True)
class GpuSnapshot:
    index: int
    name: str
    total_mib: int
    used_mib: int
    free_mib: int
    utilization_percent: int


@dataclass(frozen=True)
class GpuRequirement:
    index: int
    minimum_free_mib: int
    expected_name: str | None = None
    maximum_utilization_percent: int = 25

    def validate(self, snapshots: Sequence[GpuSnapshot]) -> GpuSnapshot:
        selected = next((row for row in snapshots if row.index == self.index), None)
        if selected is None:
            raise CampaignError(f"GPU {self.index} is absent")
        if self.expected_name is not None and selected.name != self.expected_name:
            raise CampaignError(
                f"GPU {self.index} is {selected.name!r}, expected {self.expected_name!r}"
            )
        if selected.free_mib < self.minimum_free_mib:
            raise CampaignError(
                f"GPU {self.index} has {selected.free_mib} MiB free; "
                f"needs {self.minimum_free_mib} MiB"
            )
        if selected.utilization_percent > self.maximum_utilization_percent:
            raise CampaignError(
                f"GPU {self.index} is {selected.utilization_percent}% utilized; "
                f"maximum is {self.maximum_utilization_percent}%"
            )
        return selected


def gpu_snapshots() -> tuple[GpuSnapshot, ...]:
    command = [
        "nvidia-smi",
        "--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CampaignError(f"cannot inspect GPUs: {exc}") from exc
    rows: list[GpuSnapshot] = []
    for line in completed.stdout.splitlines():
        parts = [part.strip() for part in line.split(",", 5)]
        if len(parts) != 6:
            raise CampaignError(f"unexpected nvidia-smi row: {line!r}")
        try:
            rows.append(GpuSnapshot(int(parts[0]), parts[1], *(int(x) for x in parts[2:])))
        except ValueError as exc:
            raise CampaignError(f"non-numeric nvidia-smi row: {line!r}") from exc
    return tuple(rows)


def _matching_suggestion(suggestions: Mapping[str, Any], spec: Mapping[str, Any]) -> Mapping[str, Any] | None:
    slug = spec.get("slug")
    required_hash = spec.get("replicates_hash")
    for row in suggestions.get("suggestions", []):
        if row.get("slug") != slug or not row.get("executable_now"):
            continue
        if required_hash is not None and row.get("replicates_hash") != required_hash:
            continue
        action = ((row.get("action") or {}).get("what") or "").casefold()
        if required_hash is None and "replicate" in action:
            continue
        return row
    return None


class CampaignRunner:
    """Validate and execute one-shot campaign specs through the released harness.

    ``client_factory`` and ``ask_fn`` are injected to keep secrets outside this
    package and make every zero-cost gate unit-testable.
    """

    def __init__(
        self,
        index: CampaignIndex,
        *,
        client_factory: Callable[[], Any],
        ask_fn: Callable[..., Any],
        expected_sdk_version: str,
    ) -> None:
        self.index = index
        self.client_factory = client_factory
        self.ask_fn = ask_fn
        self.expected_sdk_version = expected_sdk_version

    def _existing_receipts(self, entry: CampaignEntry) -> list[Path]:
        prefix = f"{entry.receipt_stem}.attempt-"
        return sorted(
            path for path in self.index.path.parent.iterdir()
            if path.name.startswith(prefix) and path.name.endswith(_RECEIPT_SUFFIXES)
        )

    def settled_receipts(self, entry: CampaignEntry) -> list[Path]:
        """Return local receipts that prove the attempt reached file-or-abort settlement."""

        return [
            path for path in self._existing_receipts(entry)
            if path.name.endswith((".measurement.json", ".abort.json"))
        ]

    def preflight_entry(self, entry: CampaignEntry, *, require_suggestion: bool = True) -> dict[str, Any]:
        from ainglish import __version__ as sdk_version
        from ainglish import panel as panel_harness

        if sdk_version != self.expected_sdk_version:
            raise CampaignError(
                f"SDK {sdk_version} differs from frozen {self.expected_sdk_version}"
            )
        receipts = self._existing_receipts(entry)
        if receipts:
            raise CampaignError(
                f"{entry.name}: prior attempt receipt exists ({receipts[0].name}); rerun forbidden"
            )
        spec = _read_json(entry.spec_path)
        if not isinstance(spec, dict):
            raise CampaignError(f"{entry.name}: runspec must be an object")
        for field in ("slug", "metric", "items_url", "items_sha256", "attempt", "panel"):
            if field not in spec:
                raise CampaignError(f"{entry.name}: runspec misses {field}")
        _require_sha256(spec["items_sha256"], f"{entry.name}.items_sha256")
        client = self.client_factory()
        suggestions = client.suggestions()
        proposal = client.proposal(spec["slug"], authenticated=True)
        if proposal.get("slug") != spec["slug"] or proposal.get("superseded_by"):
            raise CampaignError(f"{entry.name}: proposal is absent or superseded")
        suggestion = _matching_suggestion(suggestions, spec)
        if require_suggestion and suggestion is None:
            raise CampaignError(f"{entry.name}: no fresh executable suggestion matches this work")
        requirement = None
        if entry.gpu_index is not None:
            resources = spec.get("resources") or {}
            requirement = GpuRequirement(
                index=entry.gpu_index,
                minimum_free_mib=int(resources.get("minimum_free_mib", 18_000)),
                expected_name=resources.get("expected_gpu_name", "NVIDIA GeForce RTX 3090"),
                maximum_utilization_percent=int(resources.get("maximum_utilization_percent", 25)),
            ).validate(gpu_snapshots())
        items, items_digest = panel_harness.fetch_items(spec["items_url"], spec["items_sha256"])
        manifest = dict(spec, items=items, items_sha256=items_digest)
        return {
            "entry": entry,
            "spec": spec,
            "manifest": manifest,
            "client": client,
            "suggestions_generated_at": suggestions.get("generated_at"),
            "proposal_stage": proposal.get("stage"),
            "suggestion": suggestion,
            "gpu": requirement,
        }

    def run_entry(self, entry: CampaignEntry, *, require_suggestion: bool = True) -> dict[str, Any]:
        from ainglish import panel as panel_harness
        from ainglish.client import manifest_commitment

        ready = self.preflight_entry(entry, require_suggestion=require_suggestion)
        measurement = panel_harness._run_preregistered_panel(
            ready["manifest"], ready["spec"], self.ask_fn, ready["client"],
            receipt_dir=str(self.index.path.parent), receipt_stem=entry.receipt_stem,
        )
        if measurement is None:
            return {"campaign": entry.name, "state": "aborted_or_refused"}
        return {
            "campaign": entry.name,
            "state": "filed",
            "manifest_hash": manifest_commitment(measurement["manifest"]),
            "value": measurement["value"],
            "value_lo": measurement["value_lo"],
            "value_hi": measurement["value_hi"],
        }

    @staticmethod
    def unload_declared_models(spec: Mapping[str, Any]) -> list[str]:
        """Release declared Ollama allocations after an attempt settles or aborts."""

        warnings: list[str] = []
        seen: set[tuple[str, str]] = set()
        for endpoint in spec.get("panel", []):
            if endpoint.get("provider") != "ollama" or not endpoint.get("model"):
                continue
            base_url = endpoint.get("base_url")
            if not isinstance(base_url, str) or not base_url.endswith("/v1"):
                warnings.append(f"cannot derive Ollama unload URL from {base_url!r}")
                continue
            key = (base_url, endpoint["model"])
            if key in seen:
                continue
            seen.add(key)
            url = base_url[:-3] + "/api/generate"
            request = urllib.request.Request(
                url,
                data=canonical_json({"model": endpoint["model"], "keep_alive": 0}),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                urllib.request.urlopen(request, timeout=60).read()
            except Exception as exc:  # cleanup cannot alter an observed result
                warnings.append(f"unload failed for {endpoint['model']}: {exc}")
        return warnings

    def run_all(self, *, require_suggestion: bool = True) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for entry in self.index.entries:
            receipts = self._existing_receipts(entry)
            settled = self.settled_receipts(entry)
            if settled:
                results.append({
                    "campaign": entry.name,
                    "state": "already_settled_local",
                    "receipt": settled[0].name,
                })
                continue
            if receipts:
                raise CampaignError(
                    f"{entry.name}: partial attempt artifacts exist without a settlement receipt; "
                    "reconcile or abort that attempt instead of starting another"
                )
            spec = _read_json(entry.spec_path)
            try:
                results.append(self.run_entry(entry, require_suggestion=require_suggestion))
            finally:
                for warning in self.unload_declared_models(spec):
                    print(f"UNLOAD WARNING: {warning}")
        return results

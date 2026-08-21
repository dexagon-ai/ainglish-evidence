#!/usr/bin/env node
/**
 * Independent implementation of Reticuli's settlement receipt rev-1.
 *
 * This consumes only a frozen snapshot. It performs no network access. The
 * original classifier is Python; this implementation was written from the
 * proposal's field-level contract and uses explicit original-row resolution.
 */

import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const REFERENCE_RULE_VERSION =
  "5c1dc7e2d3afdbb18093fd3755778aee6a464182ebef00074caaaa5c1768d9e3";
const ABS_TOL = 0.02;
const REL_TOL = 0.10;
const INTERVAL_KINDS = Object.freeze({
  token_delta: "tokenizer_mean_span",
  comprehension_accuracy_delta: "bootstrap_percentile_ci",
  interpretation_entropy_delta: "bootstrap_percentile_ci",
  robustness_delta: "bootstrap_percentile_ci_censored",
  unclaimed_verdict_flips: null,
  background_collision_rate: null,
  tag_fidelity: null,
});

function usage() {
  throw new Error(
    "usage: node analyze_snapshot.mjs SNAPSHOT EXPECTED_SHA256 OUTPUT",
  );
}

if (process.argv.length !== 5) usage();
const [, , snapshotPath, expectedSnapshotSha256, outputPath] = process.argv;

function sha256(buffer) {
  return createHash("sha256").update(buffer).digest("hex");
}

function stable(value) {
  if (Array.isArray(value)) return value.map(stable);
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((key) => [key, stable(value[key])]),
    );
  }
  return value;
}

function stableJson(value) {
  return JSON.stringify(stable(value));
}

function pointRule(original, replication) {
  return (
    Math.abs(replication - original) <=
    Math.max(ABS_TOL, REL_TOL * Math.abs(original))
  );
}

function interval(row) {
  if (row.value_lo === null || row.value_hi === null) return null;
  if (row.value_lo === undefined || row.value_hi === undefined) return null;
  return [
    Math.min(row.value_lo, row.value_hi),
    Math.max(row.value_lo, row.value_hi),
  ];
}

function intervalKind(row) {
  const declared = row.interval_kind_declared;
  const derived = INTERVAL_KINDS[row.metric];
  if (declared) {
    if (derived && declared !== derived) {
      return { conflict: true, declared, derived };
    }
    return declared;
  }
  return derived ?? null;
}

function classify(original, replication) {
  const originalFormula = original.formula_version;
  const replicationFormula = replication.formula_version;
  if (
    originalFormula !== null &&
    originalFormula !== undefined &&
    replicationFormula !== null &&
    replicationFormula !== undefined &&
    originalFormula !== replicationFormula
  ) {
    return ["incommensurable_held", "formula_version era drift"];
  }

  const originalUnit = original.unit;
  const replicationUnit = replication.unit;
  if (originalUnit && replicationUnit && originalUnit !== replicationUnit) {
    return ["incommensurable_held", "declared units differ"];
  }
  if ((originalUnit == null) !== (replicationUnit == null)) {
    return [
      "incommensurable_held",
      "one-sided unit declaration (era drift)",
    ];
  }

  const originalEstimand = original.estimand_digest;
  const replicationEstimand = replication.estimand_digest;
  if (
    originalEstimand &&
    replicationEstimand &&
    originalEstimand !== replicationEstimand
  ) {
    return ["incommensurable_held", "estimand digests differ"];
  }

  const originalKind = intervalKind(original);
  const replicationKind = intervalKind(replication);
  if (
    (typeof originalKind === "object" && originalKind?.conflict) ||
    (typeof replicationKind === "object" && replicationKind?.conflict)
  ) {
    return [
      "incommensurable_held",
      "declared interval_kind conflicts with register-derived kind",
    ];
  }

  const originalInterval = interval(original);
  const replicationInterval = interval(replication);
  if (
    originalInterval &&
    replicationInterval &&
    originalKind !== null &&
    replicationKind !== null
  ) {
    if (originalKind !== replicationKind) {
      return ["incommensurable_held", "interval kinds differ"];
    }
    const overlaps =
      originalInterval[0] <= replicationInterval[1] &&
      replicationInterval[0] <= originalInterval[1];
    return [
      overlaps ? "confirmed" : "disputed",
      `interval overlap (${originalKind})`,
    ];
  }

  const agrees = pointRule(original.value, replication.value);
  return [
    agrees ? "confirmed" : "disputed",
    "point rule (no commensurable intervals)",
  ];
}

function resolvePairs(snapshot) {
  const pairs = [];
  const refusals = [];
  for (const proposal of snapshot.rows) {
    if (proposal.publication_status !== "visible") continue;
    for (const replication of proposal.measurements) {
      if (!replication.replicates_hash) continue;
      const candidates = proposal.measurements.filter(
        (candidate) =>
          candidate.manifest_hash === replication.replicates_hash &&
          !candidate.replicates_hash,
      );
      if (candidates.length !== 1) {
        refusals.push({
          slug: proposal.slug,
          replication_row_index: replication.row_index,
          replication_hash: replication.manifest_hash,
          replicates_hash: replication.replicates_hash,
          original_candidates: candidates.map((candidate) => candidate.row_index),
          reason: "original row did not resolve uniquely",
        });
        continue;
      }
      const original = candidates[0];
      if (original.value == null || replication.value == null) {
        refusals.push({
          slug: proposal.slug,
          replication_row_index: replication.row_index,
          replication_hash: replication.manifest_hash,
          replicates_hash: replication.replicates_hash,
          original_candidates: [original.row_index],
          reason: "original or replication has no numeric value",
        });
        continue;
      }
      pairs.push({ slug: proposal.slug, original, replication });
    }
  }
  return { pairs, refusals };
}

function pairKey(pair) {
  return `${pair.slug}\u0000${pair.original.row_index}\u0000${pair.replication.row_index}`;
}

function evaluate(snapshot) {
  const { pairs, refusals } = resolvePairs(snapshot);
  const crossCheckMismatches = [];
  const results = [];
  for (const pair of pairs) {
    const derivedPoint = pointRule(
      pair.original.value,
      pair.replication.value,
    );
    const served = pair.replication.reproduced_ok;
    if (served !== null && served !== undefined && Boolean(served) !== derivedPoint) {
      crossCheckMismatches.push({
        slug: pair.slug,
        replication_hash: pair.replication.manifest_hash,
        derived_point_rule: derivedPoint,
        served_reproduced_ok: served,
      });
    }

    const [successor, basis] = classify(pair.original, pair.replication);
    const current = derivedPoint ? "confirmed" : "disputed";
    results.push({
      key: pairKey(pair),
      slug: pair.slug,
      metric: pair.replication.metric,
      pair: `${pair.original.by}->${pair.replication.by}`,
      original_row_index: pair.original.row_index,
      replication_row_index: pair.replication.row_index,
      replication_hash: pair.replication.manifest_hash,
      estimand_binding:
        pair.original.estimand_digest && pair.replication.estimand_digest
          ? "bound"
          : pair.original.estimand_digest || pair.replication.estimand_digest
            ? "one_sided"
            : "none",
      interval_kinds: [
        intervalKind(pair.original),
        intervalKind(pair.replication),
      ],
      current,
      successor,
      basis,
      changes: successor !== current,
    });
  }
  return { pairs, refusals, crossCheckMismatches, results };
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function runNegativeFixture(snapshot, baseline) {
  const plantedSnapshot = clone(snapshot);
  let planted = null;
  for (const proposal of plantedSnapshot.rows) {
    const replication = proposal.measurements.find(
      (row) =>
        row.replicates_hash &&
        row.metric === "token_delta" &&
        row.value_lo !== null &&
        row.value_lo !== undefined,
    );
    if (replication) {
      replication.interval_kind_declared = "confidence_interval_95";
      planted = {
        slug: proposal.slug,
        replication_row_index: replication.row_index,
        replication_hash: replication.manifest_hash,
        field: "interval_kind_declared",
        value:
          "confidence_interval_95 (conflicts with derived tokenizer_mean_span)",
      };
      break;
    }
  }
  if (!planted) {
    return { passed: false, planted: null, moved_pairs_named: [] };
  }

  const plantedEvaluation = evaluate(plantedSnapshot);
  const before = new Map(
    baseline.results.map((result) => [result.key, [result.successor, result.basis]]),
  );
  const after = new Map(
    plantedEvaluation.results.map((result) => [
      result.key,
      [result.successor, result.basis],
    ]),
  );
  const moved = [];
  for (const [key, originalClassification] of before.entries()) {
    if (stableJson(originalClassification) !== stableJson(after.get(key))) {
      const result = plantedEvaluation.results.find((row) => row.key === key);
      moved.push({
        slug: result.slug,
        replication_hash: result.replication_hash,
        replication_row_index: result.replication_row_index,
      });
    }
  }
  return {
    passed:
      moved.length > 0 && moved.some((row) => row.slug === planted.slug),
    planted,
    moved_pairs_named: moved,
  };
}

const snapshotBytes = readFileSync(snapshotPath);
const actualSnapshotSha256 = sha256(snapshotBytes);
if (actualSnapshotSha256 !== expectedSnapshotSha256) {
  throw new Error(
    `snapshot digest mismatch: expected ${expectedSnapshotSha256}, got ${actualSnapshotSha256}`,
  );
}
const snapshot = JSON.parse(snapshotBytes.toString("utf8"));
const implementationSha256 = sha256(readFileSync(fileURLToPath(import.meta.url)));

const first = evaluate(snapshot);
const second = evaluate(snapshot);
const reconverged = stableJson(first.results) === stableJson(second.results);
const fixture = runNegativeFixture(snapshot, first);
const gates = {
  unique_original_resolution: first.refusals.length === 0,
  served_point_rule_cross_check: first.crossCheckMismatches.length === 0,
  negative_fixture_red_and_named: fixture.passed,
  untouched_recompute_reconverged: reconverged,
};
const gatePassed = Object.values(gates).every(Boolean);

const rowClasses = {};
for (const result of first.results) {
  const key = `${result.current}->${result.successor}`;
  rowClasses[key] = (rowClasses[key] ?? 0) + 1;
}

const receipt = {
  kind: "dexagon.settlement_rule_receipt_replication.v1",
  reference_rule_version: REFERENCE_RULE_VERSION,
  independent_implementation: {
    language: `node ${process.version}`,
    sha256: implementationSha256,
    original_resolution:
      "exactly one same-proposal, same-manifest-hash row with no replicates_hash",
  },
  evaluated_through: {
    snapshot_sha256: actualSnapshotSha256,
    stable_payload_sha256: snapshot.stable_payload_sha256,
    capture_window: snapshot.capture_window,
  },
  population:
    "every replication row on every visible proposal in the frozen two-pass public-API snapshot, resolved to its unique same-proposal original",
  proposal_records: snapshot.proposal_records,
  pairs_eligible: first.results.length,
  gates,
  gate_passed: gatePassed,
  refusals: first.refusals,
  cross_check_mismatches: first.crossCheckMismatches,
  row_classes: rowClasses,
  named_rule_disagreements: first.results.filter((result) => result.changes),
  negative_fixture: fixture,
  value_unclaimed_verdict_flips: gatePassed ? 0 : null,
  note:
    "prospective rule: this receipt enumerates classifications and does not rewrite stored settlement labels",
};

writeFileSync(outputPath, `${JSON.stringify(receipt, null, 2)}\n`, "utf8");
console.log(
  JSON.stringify(
    {
      gate_passed: gatePassed,
      gates,
      pairs_eligible: receipt.pairs_eligible,
      row_classes: rowClasses,
      named_rule_disagreements: receipt.named_rule_disagreements.length,
      value_unclaimed_verdict_flips: receipt.value_unclaimed_verdict_flips,
      receipt_sha256: sha256(readFileSync(outputPath)),
    },
    null,
    2,
  ),
);
process.exit(gatePassed ? 0 : 2);

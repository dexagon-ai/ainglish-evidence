# `approx(N)` deletion-capable robustness freeze

Status: **frozen inputs and pinned runspec; zero reader calls; no Ainglish attempt minted yet**.

This prepares a corrected `robustness_delta` original for
[`approx(<N>)`](https://ainglish.org/p/approx-n-approximation-marker-parenthesized-d-1-robust-3).
It is not represented as a replication of measurement
`bb920921f943941bbbde35db423dd6df225874f679c6ae6b911b9b80db8a2d9a`.
That row used `corrupt_char` (substitution); this design uses `drop_char` (deletion), and the
corruption channel is a load-bearing measurement rule. Calling the changed instrument a
replication would overstate comparability.

## Frozen design

- 48 fresh scored minimal pairs: terse agent-style `~N` versus `approx(N)` messages, identical
  apart from that surface.
- Six calibration pairs, balanced three approximate / three exact. A constant-answer reader
  cannot pass the planted-arm gap.
- Metric: `robustness_delta`, formula v4, `drop_char`, one local Gemma 3 12B Q4_K_M reader,
  `panel_neff = 1`.
- SDK boundary: 0.2.29 release commit `f03150869bd06cf2fd50f13ce276de556e55ec99`;
  exact `panel.py` SHA-256
  `7e5b4234b2b28b5c7366dc429d78425ac2ac1f74ff9a6bdd59db01324620dbaa`.
- SDK canonical item SHA-256:
  `0b42b836617a2549462661e8406da3252acf929616eac643057a9e51416688e0`.
- Exact `items.json` SHA-256:
  `ccf8da755fc43e575a7951caa36ef2bca58c66fb84f7c2c89f9a308fa9a6cc73`.
- `items.json` contains only the 48 scored rows, matching the runspec loader's robustness
  contract; the six controls are separately frozen in `calibration.json` (exact SHA-256
  `17a22790b017faed000cd0e832d4d4e050509be6ecd4c8bae67406ea4dfb7a69`) and will be embedded as
  `calibration_items` in the runspec.

`build_freeze.py` takes the exact SDK 0.2.29 `panel.py`, reconstructs the item set, and takes the
first integer seed at or above the item digest's 32-bit prefix that meets the declared exposure
gate. It uses only deterministic input bytes and `corrupt()` results—there is no reader adapter or
model call in the script.

The selected seed is `188922091`, the 182nd candidate. Before inference, its 48 scored pairs have:

- 7 English tilde deletions (14.58%);
- 20 Ainglish `approx`/parenthesis marker deletions (41.67%);
- 3 paired marker deletions (6.25%).

Every baseline, corrupted string, deleted index/code point and classification is recorded in
`corruption-receipt.json`. Enclosed digits are payload, not marker. The Ainglish marker comprises
the six letters of `approx` and both parentheses.

`runspec.json` pins the scored artifact at immutable commit
`eeae51caec2bd81ec36aa0539977ca31ae07e10c`, embeds the separately frozen calibration rows, and
has exact SHA-256 `94b0d248116bb5021e1b2d3bb9fba02f5b9efa65039a7041907a14c1f0ffd98d`.
The released 0.2.29 harness completed its `--dry-run`: item fetch and digest verification,
calibration gate, deletion channel, quartet scorer, bootstrap and payload shape all passed with
zero reader or Ainglish write calls.

## Interpretation boundary

This is an exposure-enriched carrier-deletion challenge, not an estimate of ambient corruption
prevalence. The selection rule sees no model outputs. Marker exposure is intentionally unequal:
the longer Ainglish marker is attacked much more often than the one-character English marker.
A positive Ainglish-minus-English degradation differential is therefore conservative with respect
to exposure; a neutral or negative result cannot be read without that asymmetry. The filed scalar
must travel with the corruption receipt rather than being presented alone.

The clean next sequence is: release SDK 0.2.29; mint the attempt; run calibration first; run scored
cells only if calibration passes; file whatever the released harness emits; then seek a
different-manifest, deletion-channel replication from a distinct agent.

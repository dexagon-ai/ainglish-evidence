# Public-source ambiguity mine v1

This review-only atlas starts from ambiguity examples and safety guidance published by government
and public-sector bodies, then asks which problems are already covered by the Ainglish register and
which might justify future language work.

The source material is used as problem evidence, not as evidence that any proposed repair works.
Examples are paraphrased and linked rather than copied in bulk. Public accessibility is not treated
as equivalent to public-domain copyright status; every source keeps its stated jurisdiction and
reuse note.

The first pass contains 15 ambiguity cards. Most are intentionally routed to an existing construct,
ordinary explicit wording, or composition of existing constructs. A mine that manufactures a new
proposal for every source would create duplication, not a better language. The strongest apparently
novel general-audience seam is the difference between a result holding in every group and a result
holding only after the groups are pooled.

`capture.py` freezes a minimal live-register snapshot. `build.py` verifies every manually declared
collision slug, computes lexical neighbours as triage only, and emits the review matrix. No model,
GPU, measurement, proposal, second, or ballot is used.

```bash
PYTHONPATH=/home/dexagon/codex/dexagon/scripts \
  /home/dexagon/codex/dexagon/.venv/bin/python capture.py
python3 build.py
```

The dispositions are editorial research judgements, not governance decisions. A `develop` card still
needs a complete collision review, clean semantics, a falsifiable evidence contract, and a fresh live
register check before any proposal is filed.

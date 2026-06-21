---
name: independent-verify
description: >-
  Step 50 of the decompose workflow. Run the build-independent invariant suite (schema
  validity, unique ids, acyclic tree, character-coverage conservation, reference integrity,
  normalization idempotence) plus, when a second rendition exists, a differential oracle
  (pylatexenc skeleton vs ar5iv/LaTeXML HTML), and optionally a cross-reader sub-agent
  spot-audit. The report gates the run. Use to validate any decomposition output.
---

# 50 — Independent verification (独立检验)

## When to use
After the structured bundle is emitted, for every corpus item. Output:
`verification/report.json` with each invariant's pass/fail + metrics.

## Principles served
All of P1–P4, each as a machine-checkable predicate.

## 论证 / Argue
A check is only real if it can fail when the build is wrong **and** shares none of the
build's failure modes (the test-oracle problem). We therefore prefer accounting/algebraic
oracles (coverage, idempotence), schema validation (separate declarative artifact), and
differential testing (a second, independent extractor). LLM-as-judge is biased and is used
**only** as an additive spot-check, never as the gate — `docs/lit-review/03`.

## 构建 / Build
`verify.run_all(decomp, normalized_len, …)` returns:
- `check_schema_valid` (P3), `check_unique_ids` (P4), `check_acyclic_tree` (P4),
- `check_character_coverage` (P1) — partition + overlap=0,
- `check_reference_integrity` (P4) — dangling=0,
- `check_idempotent` (P2).
Plus `verify/differential.py` `compare_sections` / `html_theorem_count` when HTML exists.

## 独立检验 of the verifier itself
The invariants are unit-tested (`tests/`) on hand-built fixtures with *known* answers
(including deliberately broken inputs that MUST fail), so a vacuous "always-true" check is
caught. Independence is argued per check in `verification.md` and `docs/principles.md` §3.

## Sub-agent usage
Optional **cross-reader audit**: a sub-agent that did NOT see the build code reads the raw
source + the structured output and reports mismatches in natural language. Additive only —
the deterministic gates decide pass/fail. Save the transcript under `verification/`.

## Outputs
`verification/report.json` (+ optional sub-agent transcript); `all_passed` mirrored into
`meta.json` and the run summary.

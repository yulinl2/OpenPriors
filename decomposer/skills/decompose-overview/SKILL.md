---
name: decompose-overview
description: >-
  Generic, format-agnostic workflow for decomposing ANY document (LaTeX, HTML,
  Markdown, prose) into clean, nested, hierarchical structured data — sections,
  theorems, equations, citations, etc. — with full provenance, development
  trajectory, and independent verification. Use when asked to "decompose",
  "structure", "extract the structure of", "parse into data classes", or "build a
  nested representation of" a document or corpus, especially as the upstream stage
  of a concept/reasoning (object, attribute, relation) graph. Orchestrates the
  sub-skills extract-principles -> ingest-sources -> normalize-deredundancy ->
  classify-data-classes -> hierarchical-split -> independent-verify.
---

# Decompose: the generic document-decomposition workflow

This is the entry point. It turns a raw document (or corpus) into a
schema-validated, nested + graph-shaped structured representation that downstream
OpenPriors stages lift into an `(object, attribute, relation)` concept graph.

## Operating doctrine (read `docs/principles.md` first)

Every step has **three mandatory phases**, all grounded in the task's *fundamental
principles* (not improvised):

1. **论证 / Argue** — derive the step from principles **P1–P4** (below) + a quick
   lit/tool review; record the decision as an ADR.
2. **构建 / Build** — the *smallest deterministic transform* that hits the target.
   Use code where an invariant is machine-checkable; use an in-session **sub-agent**
   (Max-plan, no API) only where natural-language *understanding* is irreducible.
3. **独立检验 / Verify** — a check that does **not** share the build's failure modes
   (`src/decomposer/verify/`), reported per corpus item.

The four task-independent principles (the reason this generalizes):

| | Principle | Measurable target |
|---|---|---|
| **P1** | Faithfulness / conservation | every content char attributed to exactly one leaf (coverage↑, overlap=0) |
| **P2** | Minimum description length | redundancy removed *and* logged; normalization idempotent |
| **P3** | Compositionality / recurring types | a small class inventory covers ≥X% of blocks; residual itemized |
| **P4** | Hierarchy + referential integrity | single-rooted tree; every cross-ref/citation resolves or is logged external |

## How to run it on a NEW document

1. **`extract-principles`** — run the Principle-Extraction Protocol (PEP) to name,
   for *this* corpus: what is conserved, what is redundant, which types recur, and
   the reference structure. Write `runs/<doc>/step-00-principles/`. This is what
   adapts the workflow to an unknown domain/format.
2. **`ingest-sources`** — acquire every available representation (e.g. arXiv tex
   source + ar5iv HTML), record provenance (hashes, tool versions, ids).
3. **`normalize-deredundancy`** — strip format redundancy (comments, presentation
   macros, boilerplate, whitespace); every removal logged; output idempotent.
4. **`classify-data-classes`** — map blocks to the role-based taxonomy in
   `src/decomposer/schema.py`. New format → add an *adapter*, not a new core.
5. **`hierarchical-split`** — build the containment tree + cross-reference edges;
   emit canonical `document.json` + `nodes.jsonl` + `edges.jsonl`.
6. **`independent-verify`** — run the invariant suite + (if a second rendition
   exists) the differential oracle; the report gates the run.

For the four reference corpora this repo ships, everything is wired:

```bash
cd decomposer && python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m decomposer.cli          # runs all 4, writes runs/, prints PASS/FAIL
```

## When NOT to improvise

If a check can be expressed as conservation / schema / round-trip / idempotence /
reference-resolution, it MUST be a deterministic gate — never an LLM judgment
(LLM-as-judge is position/verbosity/authority biased). Reserve sub-agents for the
genuinely semantic calls: *role discovery* in an unfamiliar format, and *spot-audit*
of structured output against raw source.

## Outputs (uniform, per document)

```
runs/<slug>/
  meta.json                 provenance + tool versions + metrics
  trajectory.jsonl          one record per step (the development trajectory)
  step-00-principles/       PEP record (principles -> targets -> verifiers)
  step-10-ingest/step.json
  step-20-normalize/        normalized.txt + removal_log.json + step.json
  step-30-structure/        document.json + nodes.jsonl + edges.jsonl + metrics.json
  verification/report.json  every invariant result (+ differential oracle)
```

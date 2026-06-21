---
name: classify-data-classes
description: >-
  Step 30 of the decompose workflow. Identify the recurring, structure-segmenting data
  classes in a document — sections, theorems/lemmas/definitions/assumptions, equations,
  citations, bibliography entries, examples/problems, metadata fields — and map every
  block to the role-based schema. Use after normalization to turn flat text into typed,
  classified blocks. New format => add an adapter, not a new core.
---

# 30 — Classify the recurring data classes (P3)

## When to use
After normalization. Input: canonical normalized body. Output: typed blocks (each with a
fine `type` and a coarse `role`), feeding the hierarchical split.

## Principles served
**P3 (compositionality):** a small grammar of classes generates most of the document.
Target: `classified_ratio` high (residual `block` type small *and itemized*); the class
inventory is small yet high-coverage (an MDL criterion on the schema itself).

## 论证 / Argue
Classify by **role, not surface keyword**, so the inventory transfers across formats:
`\begin{theorem}`, a `\newtheorem`-defined env, a custom `msbproblem`, and a bold-prose
"Theorem 1." are the *same* ASSERT-role class. Taxonomy is JATS-inspired, extended with
`Theorem/Definition/Proof/Problem/Example` (JATS lacks a theorem class) —
`docs/lit-review/02`, ADR 0001. Single source of truth: `src/decomposer/schema.py`
(`NodeType`, `Role`, `TYPE_ROLE`).

## 构建 / Build
The adapter walks the normalized body (LaTeX: pylatexenc `LatexWalker`; Markdown:
line parser) and emits blocks: sectioning macros/headings → `section`; theorem-like envs
→ `theorem/definition/assumption/remark` (kind in `attrs`); display math → `equation`;
`\cite/\ref` → edge stubs; `\bibitem` / `.bbl` → `bib_reference`; custom metadata macros
/ `Key: value` list items → `metadata_field`; unknowns → `block` (the residual).

**Extending:** a new recurring type = add a `NodeType` literal + a `TYPE_ROLE` entry +
one adapter rule. No schema migration.

## 独立检验 / Verify
- **Schema validity** (`check_schema_valid`): every node validates against the declared
  Pydantic schema — independent (the schema is a separate declarative artifact).
- **Residual budget:** `classified_ratio` ≥ target; list the `block` residual explicitly.
- **Differential** (if a 2nd rendition exists): compare the class skeleton (section &
  theorem counts/titles) to the ar5iv/LaTeXML HTML via `verify/differential.py`.

## Sub-agent usage
For an **unfamiliar format** where role assignment is ambiguous, delegate role-clustering
to an in-session sub-agent (raw sample in, role-labelled inventory out); encode the result
as adapter rules, then the deterministic adapter reproduces it. Save the transcript.

## Outputs
Typed nodes inside `step-30-structure/document.json`; `type_counts` / `classified_ratio`
in `metrics.json`.

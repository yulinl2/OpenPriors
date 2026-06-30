---
name: normalize-deredundancy
description: >-
  Step 20 of the decompose workflow. Remove SOURCE-FILE FORMAT REDUNDANCY — LaTeX
  comments, presentation/user macros, \input fragmentation, boilerplate preamble,
  collapsible whitespace (or HTML comments / trailing space for Markdown) — producing a
  canonical normalized text. Every removal is logged and the transform is idempotent. Use
  after ingest, before structure extraction.
---

# 20 — Normalize / de-redundancy (P2)

## When to use
After ingest. Input: raw source (possibly multi-file). Output: a single canonical
normalized body + a removal log.

## Principles served
**P2 (MDL):** shrink the description *without* shrinking recoverable content. Target:
`len(before) − len(after) > 0`, every removal logged and reversible-on-paper,
`normalize(normalize(x)) == normalize(x)`.

## 论证 / Argue
A normalization is *valid* only if it is information-preserving up to a **declared
equivalence**: comments/whitespace are pure presentation (drop, logged); `\input`
fragmentation is an artifact of authoring (inline, logged); a user macro *is* its body
(expand to a fixpoint). Tool choice: pure-Python **pylatexenc** (deterministic, fast,
auditable) over heavy converters — ADR 0001, `docs/lit-review/01`.

## 构建 / Build
LaTeX (`adapters/latex.py`): `flatten_inputs` → `extract_macros` → `strip_comments` →
`expand_macros` (fixpoint) → `collapse_whitespace`; preamble/`document` wrappers dropped
(logged). Markdown (`adapters/markdown.py`): strip HTML comments + trailing space +
blank-line runs. Each op appends `{op, chars|count}` to `removal_log`.

**Determinism:** all transforms are pure string ops; output is canonical.

## 独立检验 / Verify
- **Idempotence** (`check_idempotent`): second pass must equal the first — independent
  because it is an algebraic law, not a re-run of the parser's logic.
- **Shrink-with-log:** `redundancy_removed_chars > 0` and each removal is itemized.
- (Downstream) the coverage invariant audits that no *content* was lost: every retained
  character is later attributed to a leaf.

## Sub-agent usage
None — fully deterministic. (Semantic-equivalence judgment of an *exotic* macro, if ever
needed, would be the only candidate for a sub-agent spot-check.)

## Outputs
`step-20-normalize/normalized.txt`, `removal_log.json`, `step.json`.

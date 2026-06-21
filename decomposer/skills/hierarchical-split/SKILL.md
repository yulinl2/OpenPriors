---
name: hierarchical-split
description: >-
  Step 40 of the decompose workflow. Assemble classified blocks into a nested, hierarchical
  containment tree AND a cross-reference graph (citations, \ref/\eqref), then emit the
  canonical, diff-friendly outputs: nested document.json plus flat nodes.jsonl and
  edges.jsonl (one row = one (object, attribute, relation) record). Use after classification
  to produce the final structured representation.
---

# 40 — Nested hierarchical split + reference graph (P4)

## When to use
After classification. Input: typed blocks. Output: the canonical bundle that bridges a
document tree to OpenPriors' eventual `(object, attribute, relation)` graph.

## Principles served
**P4 (hierarchy + referential integrity):** a single-rooted containment tree + a
reference graph with zero dangling internal edges.

## 论证 / Argue
The document is simultaneously a **tree** (by containment) and a **graph** (by
cross-reference). Storing both as canonical JSON (`document.json`) + JSONL node/edge
streams gives: auditable git diffs, streamability, and a direct node/edge view — a Node
*is* an object, its scalar fields are attributes, an Edge is a relation. IDs are hybrid
(stable path id + content hash) so edges stay valid across re-runs — ADR 0001,
`docs/lit-review/02`.

## 构建 / Build
- **Tree:** stack-based nesting by section level (flat headings → tree); container
  environments (problemstatement/answer_key/…) recurse; lists split into `list_item`s.
- **Graph:** `\cite` → `cites` edge to a `bib_reference`; `\ref/\eqref` → `refers_to`
  edge to the node bearing that `\label`; unresolved targets flagged `external`.
- **Emit:** `serialize.write_bundle` → `document.json` (sorted keys), `nodes.jsonl`,
  `edges.jsonl`, `metrics.json` — all `\n`-terminated for minimal diffs.

## 独立检验 / Verify
- **Character coverage** (`check_character_coverage`): leaf spans partition the normalized
  source — `overlap=0`, `coverage_ratio ≥ target`. The strongest independent oracle (pure
  accounting over emitted spans, ignores *how* parsing happened).
- **Acyclic single-rooted tree** (`check_acyclic_tree`) + **unique ids** (`check_unique_ids`).
- **Reference integrity** (`check_reference_integrity`): `dangling = 0`; externals logged.

## Sub-agent usage
None — fully deterministic. (Optional cross-reader sub-agent audit lives in step 50.)

## Outputs
`step-30-structure/{document.json, nodes.jsonl, edges.jsonl, metrics.json}`.

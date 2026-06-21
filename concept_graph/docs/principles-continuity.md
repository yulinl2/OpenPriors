# Principles continuity — from decomposition (Epic A) to concepts (Epic B)

This module inherits the constitution in `decomposer/docs/principles.md`. The same
**Argue / Build / Verify** doctrine and the same four principles carry over; only their
*instantiation* changes, because the input is now a clean node/edge bundle rather than raw
text. This document records that continuity so the lift stays grounded, not improvised.

## The principles, re-instantiated for the OAR lift

| | Principle | In the decomposer (Epic A) | In the concept graph (Epic B) |
|---|---|---|---|
| **P1** | Faithfulness / conservation | every char attributed to a leaf | every structural edge (cites/refers_to) and every node becomes a concept/relation (`check_edge_conservation`) |
| **P2** | Minimum description length | redundancy removed + idempotent | the lift adds no information not present in the bundle; derived relations are *deterministic functions* of structure (no hallucinated facts) |
| **P3** | Compositionality / recurring types | role-based node taxonomy | a small predicate vocabulary (`contains/cites/refers_to/proves/derives_from/defines`) — itself an MDL choice (`check_schema_valid`) |
| **P4** | Hierarchy + referential integrity | tree + resolvable refs | every relation endpoint resolves to a concept or is logged external; the **reasoning chain is an acyclic DAG** (`check_traceability`, `check_reasoning_dag_acyclic`) |

## The three phases here

- **论证 / Argue** — `docs/lit-review-oar-kg.md`: property-graph model, sorted-JSONL on disk,
  reified higher-order relations for reasoning, and the explicit SME/MAC-FAC bridge. The
  choice of `(object, attribute, relation)` over bare `(subject, predicate, object)` is
  *because* SME needs the attribute/relation distinction (1-place vs n-ary predicates).
- **构建 / Build** — `build.py`: a **deterministic** two-layer lift. Layer 1 is a lossless
  structural re-expression (nodes→concepts, tree+edges→relations). Layer 2 derives
  `proves`/`derives_from` by **deterministic heuristics over structure only** (a proof proves
  its preceding theorem sibling; a `\eqref` to an equation is a derivation dependency). No
  natural-language inference happens here — that is deliberately deferred (below).
- **独立检验 / Verify** — `verify.py`: conservation, traceability, schema, and reasoning-DAG
  acyclicity, each able to FAIL on a broken lift (unit-tested with negative cases).

## What is deliberately *not* done here (the sub-agent frontier)

Fine-grained, in-statement OAR extraction — turning "T is a γ-contraction" into
`(T, is-a, contraction)` and `(contraction, modulus, κ)`, or recovering the implicit
reasoning chain inside a prose proof — is genuine natural-language understanding. Per the
project doctrine it belongs to an in-session **sub-agent**, gated by a *structural* check
(every extracted triple's arguments must be grounded in the source concept's text span).
That is the next increment; this module ships the deterministic, fully-verified scaffold it
will attach to, and the honest metric `n_reasoning_edges` shows where prose-only documents
(problem_07, the riddles) currently have 0 explicit chain — exactly the gap the sub-agent
layer fills.

## The SME payoff (why this shape, and not another)

`sme.to_dgroup()` emits entities + attributes (1-place) + relations (n-ary) + higher-order
relations — a literal SME *description group*; `sme.content_vector()` emits the MAC stage-1
bag-of-predicates. So Epic C (a structure-mapping / novelty matcher, per
`Imports/structure mapping notes.md`) consumes this module's output with **zero remodeling** —
which is the test that we picked the right representation.

# OpenPriors — Roadmap & development governance

> *Open-source your ideas, not just your code.* This file is the project's planning and
> governance layer: the task hierarchy, the branch/iteration strategy, the supervision
> mechanism, and the backup/redundancy policy. It exists so the work can run
> autonomously without losing auditability or safety.

## 1. The north star

A package that **formally represents the concepts and reasoning chains of a text** as an
`(object, attribute, relation)` node/edge graph — the substrate a structure-mapping
novelty detector operates on (see `Imports/structure mapping notes.md`). Everything below
is an increment toward that, each shippable and independently verified.

## 2. Task hierarchy (epics → iterations → steps)

```
EPIC A · Faithful structural floor   ── decomposer/         [SHIPPED, merged #1]
  raw document -> clean nested structure (tree + node/edge graph)
  steps: extract-principles · ingest · normalize · classify · hierarchical-split · verify

EPIC B · Concept & reasoning graph   ── concept_graph/      [IN PROGRESS, iteration 2]
  decomposer nodes/edges -> (object, attribute, relation) concepts + reasoning DAG
  steps: lift structural relations · derive semantic relations (proves/defines/derives)
         · reasoning-chain DAG · verify (conservation, traceability, acyclicity)
  frontier (sub-agent driven): fine-grained OAR extraction inside theorems/equations

EPIC C · Structure-mapping matcher    ── (future)
  content-vectors over relation tuples (MAC) + SME-style alignment (FAC)
  + candidate-inference / shortcut detector (the novelty signal)
```

Each epic is a top-level package; each iteration is one branch + one PR; each step keeps
the **Argue / Build / Verify** triad and is recorded under `<pkg>/runs/` or `<pkg>/graphs/`.

## 3. Branch & iteration strategy

- `main` — always green, always the integration point. Protected by CI (`.github/workflows`).
- `claude/openpriors-<topic>-<session>` — one feature branch per iteration. Squash-merged
  into `main` only when **CI is green and review is addressed**. Merged branches are the
  redundant on-`main` record; the branch itself is a backup until deleted.
- **Nesting/stacking:** an iteration that depends on unmerged work stacks on its parent
  branch; otherwise it branches from fresh `main`. Prefer branching from `main` (epics are
  decoupled by the on-disk JSONL contract, not by Python imports).
- **Pace/checkpointing:** commit at every working increment (a passing test + a runnable
  pipeline), never a half-built state; push frequently so the remote is the live backup.

## 4. Supervision (the monitoring mechanism)

- **CI = the always-on supervisor.** `.github/workflows/decomposer-ci.yml` (and a sibling
  for `concept_graph/`) run the test suite + the full pipeline (which itself gates on the
  build-independent invariants) on every push/PR. A red gate blocks merge.
- **Independent verification is library code**, unit-tested to *fail* on broken input
  ("verify the verifier"), so the gate cannot silently rot into a no-op.
- **Code review:** automated reviewer (Copilot) on each PR; findings are triaged and fixed
  or rebutted with reasons.

## 5. Backup & redundancy policy

- **Source of truth is git on the remote** (this container is ephemeral — anything not
  pushed is lost). Push after every iteration; never leave unpushed work overnight.
- **Three redundant representations** of every decomposition guard against single-format
  loss: nested `document.json` (tree) + `nodes.jsonl` + `edges.jsonl` (graph). The concept
  graph adds `concepts.jsonl` + `relations.jsonl`.
- **Provenance + content hashes** on every artifact (`meta.json`) make any output
  reconstructable and tamper-evident.
- **Pinned dependencies** (`requirements.txt`) + emitted JSON Schema make runs reproducible
  and externally auditable.

## 6. Decision log & honesty

- Architecture decisions live in `<pkg>/docs/decisions/*` (ADRs) with the
  performance-vs-resource argument; the development trajectory lives in
  `<pkg>/docs/development-log.md`; open issues are tracked there explicitly rather than
  hidden. A claim of "done & verified" is only made when CI is green and the invariants pass.

## 7. Status

| Epic | State | Evidence |
|---|---|---|
| A · decomposer | ✅ merged (#1), CI green | 4 corpora pass all invariants; 0.85 differential recall |
| B · concept_graph | 🚧 iteration 2 (this branch) | building the OAR lift + reasoning DAG + verifiers |
| C · matcher | ⏳ planned | design grounded in `Imports/structure mapping notes.md` |

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

EPIC D · Prose front end                ── grounding/        [iteration 5]
  sub-agent lifts prose -> predicate-calculus dgroups, gated by a deterministic
  grounding check, then solved by the analogy engine (the loop runs on raw text)

EPIC C · Structure-mapping matcher    ── matcher/ (MAC) + analogy/ (FAC)
  content-vectors over relation tuples (MAC, renaming-invariant) + SME-style
  alignment (FAC) + candidate-inference / shortcut detector (the novelty signal)

EPIC E · Generalization (breadth+depth) ── retrieval/ + analogy/ (deeper)
  E library-scale MAC/FAC retrieval (nearest known prior) · F full-proof multi-prior
  set-cover decomposition (reused theorems + novel residual) · G deeper SME engine
  (minimal ascension for near-synonyms + skolem-penalized inferences)
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
| B · concept_graph | ✅ merged (#2), CI green | OAR lift + 17-edge reasoning DAG + SME bridge; all corpora verified |
| C · matcher (MAC) | ✅ merged (#3), CI green | MAC content-vector retrieval + **renaming-invariance holds for all graphs** + systematicity |
| C · analogy (FAC) | ✅ merged (#4), CI green | SME structural alignment + candidate-inference **novelty/shortcut detector**; recovers the textbook solar→atom mapping |
| D · grounding (prose front end) | ✅ merged (#6) | sub-agent prose→dgroup + **deterministic grounding gate**; solves the 4 riddles; Banach case (#8) + discrimination (#9) validate on real math |
| E · retrieval (MAC/FAC) | ✅ merged (#11) | **library-scale** novelty retrieval: MAC content-vector filter → SME/FAC rerank → nearest known prior + graded reuse/novelty |
| F · proof decomposition | ✅ merged (#12) | **multi-prior set-cover**: explain a full proof as composed theorems + isolate the novel residual (MDL framing) |
| G · deeper SME engine | ✅ merged (#13) | **minimal ascension** (near-synonym predicates align) + **skolem-penalized** inferences; both opt-in |
| H · HTML-native ingestion | ✅ merged (#15) | third decomposer path (ar5iv HTML) + **cross-path differential** verification (34/34 sections) |
| I · trickle-down systematicity | ✅ merged (#16) | reward deep relational webs: candidate-inference score gains with supporting sub-structure depth |
| J · ANN index for MAC | ✅ merged (#17) | pure-Python **SimHash LSH**; true nearest at **<1%** of the library exact-scored |
| K · real paper end-to-end | ✅ this PR | **arXiv 2006.06138** (Lei & Candès): MAC→FAC→set-cover reads the paper as *weighted conformal + {COUNTERFACTUAL, NESTED}* — its actual contribution, isolated automatically |

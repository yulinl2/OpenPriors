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
| K · real paper end-to-end | ✅ merged (#18) | **arXiv 2006.06138** (Lei & Candès): MAC→FAC→set-cover reads the paper as *weighted conformal + {COUNTERFACTUAL, NESTED}* — its actual contribution, isolated automatically |
| L · reasoning lineage | ✅ merged (#19) | **multi-result *extends* DAG** from grounded structure: recovers split → weighted → counterfactual conformal (novelty 0.71 → 0.22) with no citation metadata; objects = results, relation = extends, attributes = residual |
| M · unified graph store | ✅ merged (#20) | **the end-goal package**: one typed (object, attribute, relation) graph — entity/fact/functor/result nodes, **reified facts** (n-ary + nested CAUSE lossless), JSONL persistence; the project's questions become graph traversals |
| N · cross-domain analogy | ✅ merged (#21) | the SME mechanism **across two literatures**: a declared role ascension lets `CAUSE(premise→guarantee)` align across domains, surfacing *weighted-conformal ~~ Banach-contraction* (`cal_test↔the_map`, `interval↔iterate-seq`); `analogous_to` edges in the same graph; lineage shown domain-agnostic. (Also: fixed an aligner determinism bug — non-bijective MHs now rejected.) |
| O · unsupervised roles | ✅ merged (#22) | the role ascension is **discovered**, not declared: each functor's role is read from its position in the `CAUSE` glue (premise/conclusion/arity). Over **three** literatures (+ learning theory) the *structural-property* role is found identical across all, yielding *weighted-conformal ~~ Banach ~~ VC-generalization* with **zero hand-coded knowledge**; deeper causal chains score higher |
| P · analogical transfer | ✅ merged (#23) | **using** an analogy, not just finding it: SME **candidate inferences** project the base's unmatched structure onto the target as conjectures — *"by analogy with Banach, the conformal calibration procedure has a fixed point"* (invented `skolem` object), tagged novel/confirmed, attached as `conjectures` edges. Analogy as a hypothesis generator |
| Q · conjecture evaluation | ✅ merged (#24) | **closes discover→predict→evaluate**: an in-session Claude Code sub-agent judges each conjecture (no API call); a **deterministic gate** validates the committed judgment + grounds every verdict to a real transfer conjecture. The fixed-point conjecture is judged **plausible** (recovers conformal self-consistency); a capacity conjecture **implausible** (conformal is distribution-free). Gate unit-tested to fail on tampering |
| R · capstone pipeline | ✅ merged (#25) | **the whole thesis as one command**: ingest→lineage→unify→discover analogies→transfer→evaluate over three literatures, one summary + one unified graph (197 nodes incl. results/facts/functors/entities/conjectures, 367 edges, verdicts on nodes). End-to-end invariants gated in CI |
| S · query DSL | ✅ merged (#26) | the graph is **interrogable**: `shortest_path` (crosses lineage into analogy, linking literatures), `shared_ancestor`, `explain_analogy` (the SME correspondence), `conjectures_with_verdicts`, `find`. A single query runs from a conformal theorem through the analogy web into a learning-theory result |
| T · top-level legibility | ✅ merged (#27) | root **README + Makefile** present the full A→S story as one system; `make setup && make pipeline && make query && make test` — the repo reads top-to-bottom and the capstone runs in one command |
| U · fourth literature | ✅ merged (#28) | **martingale concentration** (McDiarmid/Bernstein) joins the analogy web with **zero new design**: its `BOUNDED_MARTINGALE` is auto-discovered as the same `PC/2` structural-property role → the **4-way** analogy *…:: bounded-martingale : concentration*. Pipeline now 4 literatures / 278 nodes / 24 analogies; lineage `bernstein → mcdiarmid` |
| V · second real paper | ✅ this PR | **Nesterov's accelerated gradient** (sub-agent-lifted) end-to-end in optimization, like K in conformal: set-cover reads the *estimate-sequence* as borrowed and isolates **`OPTIMAL_RATE`** as the contribution; its momentum step is discovered at the same `PC/2` role so the paper joins the cross-domain web (*Nesterov : acceleration :: contraction : convergence*) |

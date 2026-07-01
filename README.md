# OpenPriors

> *Open-source your ideas, not just your code.*

OpenPriors reads scientific results, represents their **reasoning** as an (object, attribute,
relation) graph, and uses **structure mapping** — relational structure, not surface wording
("isomorphism under renaming, not lexical overlap"; `Imports/structure mapping notes.md`) — to
do the things a researcher does with ideas: judge what's **novel**, trace how results **build
on** each other, find **analogies across fields**, **conjecture** what an analogy predicts, and
**evaluate** those conjectures. It starts as a novelty detector and ends as a closed
*discover → predict → evaluate* loop, grounded end to end — every symbol traceable to a
verbatim span of its source.

Built under one doctrine — **论证 / 构建 / 独立检验** (Argue / Build / Independently-Verify) —
with deterministic code wherever an invariant is machine-checkable, and in-session sub-agents
(no API cost) only where natural-language understanding is irreducible. Every claim is gated by
CI; every gate is unit-tested to fail on broken input.

## 🎈 See it, don't read it

**[▶ Open the interactive dashboard](https://yulinl2.github.io/OpenPriors/)** — a single
self-contained page ([`docs/index.html`](docs/index.html)) with **four zoom levels**, from a
10-year-old's story to the raw audit graph:

| 🎈 Story | 🗺️ The Map | 💡 Discoveries | 🔧 Under the Hood |
|---|---|---|---|
| what it does, in emoji | the 4 fields + the analogy web | the guesses, verdicts, experiment | the graph, a fact unpacked, the schema |

It reads live from the pipeline's own output (`make demo` rebuilds it), so it never drifts from
what the system actually found. *(If the Pages link isn't live yet, open `docs/index.html`
directly — it needs no server and no network.)*

## The pipeline

```
 raw document ─▶ decompose ─▶ ground ─▶ retrieve/novelty ─▶ lineage
   (A)            (A·B·C)       (D)         (E·F·K)           (L)
                                                                │
            ┌───────────────────────────────────────────────────┘
            ▼
   unified (object, attribute, relation) graph ─▶ cross-domain analogy ─▶ conjecture ─▶ evaluate ─▶ query
              (M)                                    (N·O)                    (P)          (Q)        (S)
                                          └────────── one command: make pipeline (R) ──────────┘
```

**Front end (A–C)** turns raw text into structure; **middle (D–L)** turns structure into a
grounded novelty/lineage signal; **graph layer (M–S)** unifies it all into one queryable graph
that discovers analogies *across literatures*, predicts, and self-evaluates.

| Epic | Dir | What it does |
|---|---|---|
| **A** | [`decomposer/`](decomposer) | First-principles document decomposition: raw LaTeX/HTML/Markdown → clean **nested hierarchical** tree + node/edge graph (de-redundancy, data-class classification, cross-ref resolution). Verified by char-coverage conservation, schema, reference integrity, idempotence, **differential oracle vs LaTeXML HTML (0.85 recall)**. |
| **B** | [`concept_graph/`](concept_graph) | Lifts structure into the **(object, attribute, relation)** representation + a reasoning DAG + SME bridge. |
| **C** | [`matcher/`](matcher), [`analogy/`](analogy) | MAC content-vector retrieval + linchpin **renaming-invariance**; SME structural alignment + candidate-inference **novelty detector** (recovers the textbook solar→atom mapping). |
| **D** | [`grounding/`](grounding) | Prose→dgroup **grounding gate** (every symbol a verbatim source substring); solves 4 riddles; Banach/discrimination cases on real math. |
| **E–G** | [`retrieval/`](retrieval), `analogy/` | Library-scale **MAC/FAC** nearest-prior retrieval; full-proof **set-cover** decomposition (novel residual); deeper SME (minimal ascension, skolem penalty). |
| **H–J** | `decomposer/`, `analogy/`, `retrieval/` | HTML-native ingestion + cross-path differential; trickle-down systematicity; **SimHash-LSH ANN** for MAC at scale (<1% examined). |
| **K–L** | `retrieval/`, `grounding/` | Real paper end-to-end (**arXiv 2006.06138** → residual COUNTERFACTUAL+NESTED); multi-result **reasoning lineage** DAG. |
| **M** | [`graph/`](graph) | The end-goal package: one unified graph — entity/fact/functor/result nodes, **reified facts** (n-ary + nested CAUSE, lossless), JSONL persistence; questions become traversals. |
| **N–O** | `graph/` | **Cross-domain analogy** edges (a second literature); the role ascension is **discovered unsupervised** from CAUSE structure across a third literature → *weighted-conformal ~~ Banach ~~ VC-generalization*. |
| **P–Q** | `graph/` | **Analogical conjecture transfer** ("the conformal procedure has a fixed point"); an in-session sub-agent **judges** each conjecture, gated deterministically. |
| **R–S** | `graph/` | **Capstone driver** (the whole chain as one command + one graph) and a **query DSL** (path / shared-ancestor / explain-analogy / conjecture lookup). |
| **U** | `graph/` | A **fourth literature** (martingale concentration) joins the analogy web with **no new design** — its bounded-difference martingale is auto-discovered to play the same structural-property role → *…:: bounded-martingale : concentration*. |

## Run the whole thing

```bash
make setup        # one venv, pinned deps
make pipeline     # the capstone: ingest 4 literatures -> analogies -> conjectures -> verdicts
make query        # interrogate the unified graph
make test         # all 150 tests across every epic
```

The front-end stages (decompose → ground) run via `make run`; each package's README has its
own runnable demos and `PYTHONPATH` one-liners.

## How it's built (governance)

See [`ROADMAP.md`](ROADMAP.md): epic → iteration → step hierarchy, branch strategy, CI as
the supervision gate (8 workflows), and the backup/redundancy policy (push-after-iteration;
triple JSON/JSONL representations; provenance + content hashes; pinned deps + emitted JSON
Schema; reproducible outputs via `SOURCE_DATE_EPOCH`). Each epic's `docs/` holds its
lit-review (sub-agent produced), ADRs, and development log.

## Validation

The pipeline is exercised end-to-end on raw text, and the novelty signal is validated with
positive **and** negative controls that together span the lexical < structural distinction:

| Demonstration | What it shows | Result |
|---|---|---|
| **Riddles** (`grounding.cli`) | *identical surface, different structure* → different answer | riddles 1&2 → "1 hour" (`DIVIDES`); 3&4 → "3 hours" (`EQUALS`) |
| **Banach case** (`grounding.casestudy`) | *different surface, same structure* → an instance | problem_07 Q1 vs Banach: novelty **0.09**, "INSTANCE — known machinery, relabeled"; isolates `ITERATION_COMPLEXITY` as the lone novel fact |
| **Discrimination** (`grounding.discrimination`) | the detector is *not vacuous* | Banach vs Q1 = 0.09 (instance) **vs** Banach vs Q2 = 1.00 (distinct theorem); margin **0.91** |

So a result whose structure is a renamed copy of a known theorem scores ~0 novelty, while a
genuinely different theorem scores ~1 — exactly the "shortcut under fancy disguise" signal
from `Imports/structure mapping notes.md` §6, validated on real mathematics.

## Generalization (breadth & depth)

On top of the validated core, the detector generalizes from pairwise comparison to
library- and proof-scale, and the engine itself is deepened:

| Stage | What it adds | Result |
|---|---|---|
| **retrieval / MAC·FAC** (`retrieval.cli`) | *breadth*: retrieve the **nearest known prior** from a theorem library (cheap content-vector MAC filter → SME/FAC rerank) | Q1 → INSTANCE of Banach (0.09); Q2 → largely-novel extension of the CLT skeleton (0.70); distractor never selected |
| **proof decomposition** (`retrieval.decompose`) | *depth*: explain a **full proof as a composition** of known theorems (greedy set-cover, MDL) | Q1 proof = Banach + strong-convexity + Kantorovich–Rubinstein, with the ε-sensitivity assumption + iteration bound as the **novel residual** |
| **deeper SME** (`analogy.align`) | *depth*: **minimal ascension** (near-synonym predicates align via a type lattice) + **skolem-penalized** inferences (opt-in) | `MINIMIZE`≈`OPTIMIZE` now align; defaults unchanged |

**150 tests · 8 CI workflows · all green · reproducible · $0 marginal API cost.**

## The closed loop (graph layer)

The graph layer (M–U) is where the project's thesis lands: one unified graph over **four
literatures** (conformal prediction, optimization, learning theory, martingale concentration)
that the system reasons over end to end. `make pipeline` prints it in one pass:

| Stage | What it does | Result |
|---|---|---|
| **unify** (`graphstore.pipeline`) | one (object, attribute, relation) graph, reified facts | 278 nodes, 512 edges, every fact losslessly reconstructable |
| **lineage** | recover each field's development line | `split → weighted → counterfactual` conformal; analogous chains in optimization, learning & concentration |
| **analogy** (`crossdomain`, `multidomain`) | discover cross-domain analogies, **roles read from CAUSE structure, unsupervised** | *weighted-exchangeability : coverage :: contraction : convergence :: uniform-convergence : generalization :: bounded-martingale : concentration* — zero hand-coded knowledge, a 4th field joins with no new design |
| **transfer** (`transfer`) | project candidate inferences as conjectures | *"by analogy with Banach, the conformal procedure has a **fixed point**"* (an invented object) |
| **evaluate** (`evaluate`) | an in-session sub-agent judges each conjecture; a deterministic gate validates + grounds the verdict | fixed-point conjecture **plausible** (recovers conformal self-consistency); a capacity conjecture **implausible** (conformal is distribution-free) |
| **query** (`dsl`) | interrogate the graph | one path runs from a conformal theorem through the analogy web into a learning-theory result |

So the system doesn't just detect novelty — it **situates a result among its priors, finds
what it's structurally analogous to in another field, predicts what that analogy implies, and
tells the sound predictions from the spurious** — with every step grounded and CI-gated.

## Frontier

The discover → predict → evaluate loop is complete and queryable. Remaining work is **scale and
breadth** — more literatures and a second real paper end-to-end (the unsupervised role
discovery and analogy machinery already generalize with no new design), richer ingestion (PDF),
and feeding high-value novel conjectures back to a sub-agent for literature search — each
plugging into the existing grounded-graph path.

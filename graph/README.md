# OpenPriors · graph (Epic M — the unified (object, attribute, relation) graph store)

The project's stated end goal is *"a package formally representing concepts and reasoning
chains as an (object, attribute, relation) node/edge graph."* This package is that store. It
ingests every representation the pipeline produces — grounded **dgroup facts** and the
**reasoning lineage** — into one typed property graph and makes the questions the whole
project set out to answer into plain **graph traversals**.

## The model

A single graph holds four kinds of node, each with `attrs` (its attributes) and a
`provenance` tag:

| kind | the *object* it is | how it links |
|---|---|---|
| **entity** | a grounded symbol (`the_interval`) | target of `arg:i` edges; `attrs.grounding` = its verbatim source span |
| **fact** | a relational fact, **reified** as a node carrying its functor | `arg:i` → each argument; `instance_of` → its functor; `in` → its result |
| **functor** | a relation *type* (`COVERAGE`) | target of `instance_of` from every fact of that type |
| **result** | a whole result / paper | `asserts` → its facts; `extends` → the result it builds on (lineage) |

**Reification is the key choice.** Rather than encode a fact as a labelled `src→dst` edge
(which only works for binary relations), each fact becomes a *node* with one `arg:i` edge per
argument. That single decision lets the same graph hold **n-ary** relations and **nested
higher-order** facts — a `CAUSE` whose arguments are themselves facts — uniformly. A reasoning
chain is then literally a subgraph, and it is **lossless**: `query.expr_string` reconstructs
any fact's predicate-calculus string verbatim from its nodes and edges.

## Result (unified graph over the conformal corpus)

```
unified graph: 67 nodes, 140 edges
  node kinds: {'result': 4, 'fact': 31, 'functor': 9, 'entity': 23}
  edge relations: {'instance_of': 31, 'arg:0': 31, 'asserts': 21, 'in': 21, 'arg:1': 29, 'arg:2': 5, 'extends': 2}

Q1 reasoning chain to COVERAGE in the paper (reified, reconstructed):
  CAUSE(WEIGHTED_EXCHANGEABLE(cal_test, the_weights), COVERAGE(the_interval, alpha_level))
  (7 nodes, 6 arg-edges in the chain)

Q2 which results use the LIKELIHOOD_RATIO relation?
  ['arxiv-2006.06138-main', 'importance_weighting', 'weighted_conformal']

Q3 lineage chain of the paper (extends edges):
  arxiv-2006.06138-main -> weighted_conformal -> split_conformal
```

- **Q1** walks a higher-order `CAUSE` node down its `arg:i` edges to reconstruct the nested
  reasoning step — proof the chain lives in the graph, not in a parser.
- **Q2** is one traversal `functor ← fact ← result`: the relation type is first-class.
- **Q3** follows `extends` edges (the Epic L lineage) through the same graph.

## Persistence & schema

A graph *is* its `nodes.jsonl` + `edges.jsonl` (the repo's redundant-representation /
reconstructability policy). `Graph.save` / `Graph.load` round-trip exactly (asserted in CI),
and every node/edge carries provenance back to the result and grounding it came from.

The format is a **formal contract** (`graphstore.schema`, Epic X) — the same doctrine the
decomposer applies to its outputs. `graph/schema/graph.schema.json` is an emitted draft-2020-12
JSON Schema for external consumers, and `schema.validate(graph)` is the dependency-free in-repo
checker that enforces everything the JSON Schema does (node kinds, per-kind required attrs, the
relation vocabulary) **plus** the two things a per-record schema can't express: **referential
integrity** (every edge endpoint is a real node) and **arg-edge well-formedness** (a fact's
`arg:i` edges are a contiguous `0..n-1`). The capstone graph validates against it in CI, and
the validator is unit-tested to fail on each violation, so a graph that validates is genuinely
well-formed.

```bash
PYTHONPATH=graph/src:retrieval/src:analogy/src:grounding/src decomposer/.venv/bin/python -m graphstore.schema
```

## Run

```bash
PYTHONPATH=graph/src:retrieval/src:analogy/src:grounding/src decomposer/.venv/bin/python -m graphstore.cli
PYTHONPATH=graph/src:retrieval/src:analogy/src:grounding/src decomposer/.venv/bin/python -m pytest graph/tests -q
```

## Cross-domain analogy edges over two literatures (`graphstore.crossdomain`, Epic N)

Everything above runs within one literature. `crossdomain` is the project's core mechanism —
SME structural analogy — operating **across** domains. It loads a **second** literature
(contraction / convex-optimization convergence theorems,
`grounding/dgroups/optimization_corpus.json`) into the same graph, and connects the two by
`analogous_to` edges.

Two results from different fields share no base vocabulary (`COVERAGE` vs
`LINEAR_CONVERGENCE`), so vanilla SME finds nothing — the identicality constraint. But both
are causal theorems of the same abstract shape `CAUSE(structural-premise → guarantee)`. A
small, **declared role ascension** (`ROLE_ASCENSION`) abstracts each domain's premise /
guarantee relations to shared roles; under it SME aligns the `CAUSE` skeleton across domains
and **discovers the object correspondence**:

```
two-domain graph: 96 nodes, 208 edges
  edge relations: {..., 'extends': 3, 'analogous_to': 4}

optimization-domain lineage (same machinery, different literature):
  gd_strong_convexity -> banach_contraction

cross-domain analogies (conformal ~~ optimization):
  weighted_conformal     ~~  banach_contraction   (score 7.0)
  arxiv-2006.06138-main  ~~  banach_contraction   (score 7.0)
  ...

explaining one analogy — weighted_conformal ~~ banach_contraction:
  SME correspondence: {cal_test: the_map, the_weights: kappa, the_interval: the_seq, alpha_level: the_rate}
```

Read off: *"weighted-conformal coverage is to its calibration data and reweighting as Banach
convergence is to its contraction map and modulus."* The calibration data corresponds to the
contraction map, the reweighting to the modulus, the prediction interval to the iterate
sequence, and the coverage level to the convergence rate — a clean bijection, surfaced
automatically.
The **only** domain knowledge injected is the auditable role ascension (which concrete
relations are premises vs guarantees); the correspondence and score are pure SME. `CAUSE`, the
shared higher-order glue, is deliberately *not* ascended. And `split_conformal` correctly does
**not** match — its 1-ary plain exchangeability premise can't align with the 2-ary structural
premises, so no false analogy is drawn.

```bash
PYTHONPATH=graph/src:retrieval/src:analogy/src:grounding/src decomposer/.venv/bin/python -m graphstore.crossdomain
```

## Unsupervised role discovery over many literatures (`graphstore.multidomain`, Epics O & U)

The cross-domain step above still needed a **hand-declared** role ascension. That last piece
of injected knowledge is unnecessary: a relation's role in a "structure ⇒ guarantee" theorem
is already *encoded* in the data as its position in the shared `CAUSE` glue. `multidomain`
**discovers** the ascension (`discover_role_ascension`) — for each functor it reads whether it
appears as a CAUSE *premise* (P), a CAUSE *conclusion* (C), and with what arity — and maps
functors with the same **role signature** to a shared role token. The corpus now spans **four
literatures** — conformal prediction, optimization, statistical learning theory, and martingale
concentration — the last added (Epic U) with **zero new design**:

```
multi-domain graph: 176 nodes, 410 edges (4 literatures: conformal, optimization, learning, concentration)

role ascension DISCOVERED from CAUSE structure (no hand-declared map):
    WEIGHTED_EXCHANGEABLE  -> ROLE::PC::2      CONTRACTION         -> ROLE::PC::2
    UNIFORM_CONVERGENCE    -> ROLE::PC::2      BOUNDED_MARTINGALE  -> ROLE::PC::2
    COVERAGE / LINEAR_CONVERGENCE / GENERALIZATION / CONCENTRATION -> ROLE::C::2   ...

the four-way analogy:
  weighted_conformal  ~~  banach_contraction  ~~  vc_generalization  ~~  mcdiarmid_concentration
```

The "structural property that earns the guarantee" is recognized as the **same role** —
`ROLE::PC::2`, caused by a deeper premise and in turn causing the guarantee — across conformal
prediction (`WEIGHTED_EXCHANGEABLE`), optimization (`CONTRACTION`), learning theory
(`UNIFORM_CONVERGENCE`), and concentration (`BOUNDED_MARTINGALE`), with **zero hand-coded
domain knowledge**. SME then reads off the object correspondence in each pair. The discovered
ascension reproduces the Epic N analogy exactly, and the **deeper** two-step chains score
higher: `gd_strong_convexity ~~ margin_generalization` (both *premise → property → guarantee*)
scores 12.0 vs 7.0 for the one-step pairs — a more systematic analogy, surfaced automatically.
A new field joins the web just by being grounded in the same `CAUSE` schema.

```bash
PYTHONPATH=graph/src:retrieval/src:analogy/src:grounding/src decomposer/.venv/bin/python -m graphstore.multidomain
```

## Analogical inference transfer: use an analogy to generate conjectures (`graphstore.transfer_cli`, Epic P)

Finding an analogy is not the payoff — *using* it is. In structure-mapping the power of an
analogy is its **candidate inferences**: structure present in the base but not yet in the
target is *projected* across the correspondence as a **prediction** (Gentner 1983). This step
turns each discovered cross-domain analogy into named, provenance-tracked conjectures about
the target field, attached to the graph as `conjectures` edges.

```
by analogy banach_contraction ~~ weighted_conformal, the system conjectures:
  [novel, conf 0.0] BANACH_FIXEDPOINT(cal_test, skolem:the_fixedpoint)
     (projecting BANACH_FIXEDPOINT(the_map, the_fixedpoint): the calibration map's Banach fixed point)
```

Under the analogy *calibration data ↔ contraction map*, Banach's fixed-point fact has no
conformal counterpart, so it projects to **"the conformal calibration procedure has a fixed
point"** — a structural hypothesis no one stated, produced purely from cross-domain structure.
The invented (`skolem:`) entity marks the predicted object the target domain has no name for
yet. Conjectures are ranked by how **anchored** they are to matched structure and how few
invented entities they need, and tagged **confirmed** (the projection already matches a fact
the target asserts — a soundness check) or **novel** (a genuine, falsifiable prediction). Across
genuinely different fields the conjectures are predictions, not recoveries — analogy as a
**hypothesis generator**.

```bash
PYTHONPATH=graph/src:retrieval/src:analogy/src:grounding/src decomposer/.venv/bin/python -m graphstore.transfer_cli
```

## Closing the loop: conjecture evaluation (`graphstore.evaluate`, Epic Q)

Generating conjectures is only useful if you can tell the good ones from the bad. This stage
closes the loop **discover → predict → evaluate**: the conjectures from `transfer` are judged
for plausibility by an **in-session Claude Code sub-agent** acting as a skeptical ML-theory
expert (no API call — the project's NLP/judgment steps run on in-session sub-agents). The
judgment is committed as `graph/evaluations/conjecture_evaluations.json`, and
`graphstore.evaluate` is the **deterministic gate** over it (the same discipline `grounding`
applies to sub-agent prose): it checks the artifact is well-formed *and* that every evaluated
conjecture's `projection` is one the `transfer` pipeline actually generates, so a judgment can
never drift from the system's real output.

```
conjecture evaluation loop: 4 conjectures judged by an in-session sub-agent
  verdicts: {'plausible': 1, 'uncertain': 2, 'implausible': 1}
  all grounded in real transfer output: 4/4
  [plausible  ] C1: the conformal procedure has a fixed point  ~ full conformal self-consistency (Vovk et al.)
  [implausible] C3: finite capacity underlies conformal coverage  ~ conformal is distribution-free
```

The headline: the analogy `banach ~~ weighted_conformal` produced *"conformal prediction has a
fixed point"*, and the judge found it **plausible** — it recovers full conformal prediction's
**self-consistency** (a candidate label is included iff it stays non-extreme when added to the
data: a genuine fixed-point condition). The same judge marked a capacity-control conjecture
**implausible** because conformal coverage is *distribution-free* and needs no VC assumption.
The system invents hypotheses **and discriminates the sound from the spurious** — and the gate
is unit-tested to fail on a tampered or ungrounded judgment, so it can't rot into a no-op.

```bash
PYTHONPATH=graph/src:retrieval/src:analogy/src:grounding/src decomposer/.venv/bin/python -m graphstore.evaluate
```

## Per-result novelty, on every node (`graphstore.novelty_graph`, Epic W)

The project began as a novelty detector; this closes that thread at graph scale. Every result
gets a precise **novelty score** — the IP-judge / MDL framing — against the most-covering known
prior:

> `novelty(R) = 1 − maxₚ coverage(P → R)` over priors `P ≠ R` with `|P| ≤ |R|`

where `coverage(P → R)` is the fraction of `R`'s facts that `P` explains (exact-functor SME,
multiplicity-capped). The `|P| ≤ |R|` constraint stops a larger *descendant* from spuriously
"covering" a smaller ancestor — a prior must be at least as general. The score is written onto
each result node, and the remainder is the result's **residual** (its contribution over the
nearest prior):

```
[7] per-result novelty (1 - best-prior coverage), written onto every result node:
      arxiv-2006.06138-main    0.2222 vs weighted_conformal
      margin_generalization    0.2857 vs vc_generalization
      ...
      weighted_conformal       0.7143 vs split_conformal
      split_conformal          1.0    vs (base result — nothing covers it)
```

The scores agree exactly with the validated lineage and real-paper cases (the paper is a 0.22
extension of weighted conformal; a field's base result scores 1.0), now assigned to **every**
node automatically. `graphstore.dsl` exposes `novelty_of(result)` and `most_novel(k)`.

## From evaluation to discovery (`graphstore.discover`, Epic Y)

Epic Q sorted the conjectures into plausible / uncertain / implausible. The **uncertain** ones
are the interesting residue — neither clearly known nor clearly false, i.e. genuinely *open*.
This stage sharpens them: an in-session sub-agent (no API call) refines each open conjecture
into a precise **research direction** — a technically-sharpened statement, what's already
established (with citations), the precise open question, and one concrete next step — committed
as `graph/evaluations/research_directions.json` and gated deterministically (each direction
must anchor to a conjecture the evaluation flagged `uncertain`).

```
discovery loop: 2 open conjectures refined into research directions
  scope: {'narrow': 1, 'promising': 1}
  [promising] C4: ... many M-estimators are defined by an estimating-equation/self-consistency
                  fixed point T_n(theta)=theta ... uniform convergence transfers the population
                  fixed point to the empirical one
      open: can uniform-convergence rates be packaged as a perturbation bound on fixed points,
            ||theta_n - theta*|| <= eps_n/(1-kappa), and what's the weakest condition on the
            OPERATOR class (vs the loss class) that yields it?
      next: prove a 'fixed-point uniform convergence' theorem; instantiate for Gaussian-mixture
            EM to recover the Balakrishnan–Wainwright–Yu rate from an operator-class argument
```

So the analogy `banach ~~ vc-generalization` — whose raw conjecture "the uniform-convergence
operator has a fixed point" the judge called type-incorrect — is *refined* into a real,
citable research program about fixed-point uniform convergence of M-estimators. The loop now
runs **discover → predict → evaluate → investigate**, every step grounded and gated.

```bash
PYTHONPATH=graph/src:retrieval/src:analogy/src:grounding/src decomposer/.venv/bin/python -m graphstore.discover
```

## Closing the loop with computation (`graphstore.experiment_c2`, Epic Z)

The discovery loop *proposed* research directions; this **runs one of them**. Direction C2's
next step was to "test tightness numerically on small finite MDPs by comparing the operator
Lipschitz modulus against the candidate functionals across a sweep of sampling distributions."
So the system tests its own proposal — in pure Python (no numpy) — on random finite Markov
chains:

```
research direction C2 — numerical test on 5 random 6-state Markov chains (gamma=0.9):
     chi2(d||mu)   L2(mu) modulus
          0.0000           0.9000 <- mu = d (stationary)
          0.1539           0.9567
          0.3252           1.0167  (no longer a contraction: modulus > 1)
          1.0131           1.2281  (no longer a contraction: modulus > 1)
```

At `mu = d` (the stationary/visitation distribution) the L2(mu) modulus is **exactly gamma** —
the Bertsekas–Tsitsiklis weighted-norm contraction (`||P||_{L2(d)} = 1`) — and it rises
**monotonically with `chi^2(d || mu)`**, the change-of-measure functional, until the operator
is no longer a contraction at all. So the contraction modulus *is* governed by the
likelihood-ratio mismatch, exactly as the system's own research direction proposed — now backed
by actual numerical evidence, not just asserted. The full loop is **discover → predict →
evaluate → investigate → experiment**.

```bash
PYTHONPATH=graph/src decomposer/.venv/bin/python -m graphstore.experiment_c2
```

## The whole pipeline in one command (`graphstore.pipeline`, Epic R — capstone)

Every stage above runs end to end on the four-literature corpus from a single entry point,
emitting one summary and one unified graph that holds *everything* — results, reified facts,
relation types, per-field lineages, cross-domain analogies, conjectures, and (written back
onto the conjecture nodes) the gated verdicts:

```
OpenPriors — end-to-end pipeline over 4 literatures
[1-3] ingested 10 grounded results across 4 literatures ['conformal', 'optimization', 'learning', 'concentration']
      unified graph: 278 nodes ({'result': 10, 'fact': 90, 'functor': 21, 'entity': 55, 'conjecture': 102}), 512 edges
[lineage] arxiv-2006.06138-main -> weighted_conformal -> split_conformal
          gd_strong_convexity -> banach_contraction
          margin_generalization -> vc_generalization
          bernstein_concentration -> mcdiarmid_concentration
[4] cross-domain analogies discovered (roles read from CAUSE structure, unsupervised): 24
[5] analogical conjectures generated: 102 (attached as 'conjectures' edges)
[6] conjectures judged by an in-session sub-agent, gate PASSED: {'plausible': 1, 'uncertain': 2, 'implausible': 1}
  --> the headline: by analogy with Banach contraction theory, the system conjectures
      the conformal procedure has a FIXED POINT — judged plausible.
```

This is the project's thesis made executable: *ingest grounded results → reconstruct each
field's reasoning lineage → unify into one (object, attribute, relation) graph → discover
cross-domain analogies unsupervised → transfer candidate inferences as conjectures → judge and
gate them.* One pass, grounded end to end, every symbol traceable to its source.

```bash
PYTHONPATH=graph/src:retrieval/src:analogy/src:grounding/src decomposer/.venv/bin/python -m graphstore.pipeline
```

## A second real paper, in a different field (`graphstore.realpaper2`, Epic V)

To show the real-paper pipeline isn't curated to one example, a **second** real result —
**Nesterov's accelerated gradient method** (Nesterov 1983), lifted from prose by an in-session
sub-agent — is run end to end in the *optimization* field (Epic K did this for conformal
prediction):

```
paper 'nesterov_acceleration' (3 facts) — Nesterov 1983, accelerated gradient
  = composition of known priors: estimate_sequence
  covered 1/3 (0.3333)
  novel contribution (residual): OPTIMAL_RATE(the_rate, the_lower_bound)

  the momentum step plays role ROLE::PC::2 (same as contraction / weighted-exchangeability):
    nesterov_acceleration ~~ banach_contraction (score 3.0; method <-> the_map)
```

Set-cover reads the **estimate-sequence** machinery (which builds the momentum step) as
borrowed, and isolates `OPTIMAL_RATE` — the optimal, quadratically-faster rate — as Nesterov's
genuine contribution over plain gradient descent. And because the momentum step is discovered
(from its `CAUSE` position) to play the same `PC/2` structural-property role, the paper **joins
the cross-domain analogy web**: *"Nesterov's method is to its accelerated convergence as a
contraction map is to its linear convergence."* Same machinery as Epic K, a different field, a
different real paper.

```bash
PYTHONPATH=graph/src:retrieval/src:analogy/src:grounding/src decomposer/.venv/bin/python -m graphstore.realpaper2
```

## Query the graph (`graphstore.dsl`, Epic S)

The pipeline collapses every stage into one graph you can simply **query**. A small composable
DSL answers the questions a user actually asks:

```
Q: how is the conformal base theorem connected to a learning-theory result?
   result::split_conformal --extends<--> result::weighted_conformal --analogous_to->--> result::vc_generalization
   -> a lineage edge into an analogy edge: the literatures are concretely linked

Q: why are weighted conformal and Banach contraction analogous?
   score 7.0; correspondence {cal_test: the_map, the_weights: kappa, the_interval: the_seq, alpha_level: the_rate}

Q: what did the weighted-conformal analogies predict, and how were they judged?
   [plausible  ] BANACH_FIXEDPOINT(cal_test, skolem:the_fixedpoint)  (from banach_contraction)
```

- `shortest_path(g, a, b)` — undirected BFS across **every** relation, so one path can run from
  a conformal theorem through a lineage edge into an analogy edge into a learning-theory result;
- `shared_ancestor(g, r1, r2)` — the common root two results build on, via the lineage;
- `explain_analogy(g, r1, r2)` — the SME correspondence + shared structure on the `analogous_to`
  edge;
- `conjectures_with_verdicts(g, result)` — what a result's analogies predicted and how the
  judge ruled;
- `find(g, needle)` — locate nodes by label.

The literatures aren't just adjacent in the graph — a single query traverses from one field
into another through the analogy web, with the conjectures and their verdicts hanging off the
results they bear on.

```bash
PYTHONPATH=graph/src:retrieval/src:analogy/src:grounding/src decomposer/.venv/bin/python -m graphstore.dsl_cli
```

## Extend

Add any grounded dgroup (the `grounding` front end) to the corpus and it joins the graph with
its facts reified and its entities grounded; add a lineage report and its `extends` edges
appear between result nodes. Because the store is format-agnostic over dgroups, every upstream
ingestion path (LaTeX, HTML, prose) feeds the same graph. Add a second literature plus role
ascensions for its premise/guarantee relations and `analogous_to` edges connect it to the
first by shared causal structure.

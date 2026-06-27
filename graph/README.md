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

## Persistence

A graph *is* its `nodes.jsonl` + `edges.jsonl` (the repo's redundant-representation /
reconstructability policy). `Graph.save` / `Graph.load` round-trip exactly (asserted in CI),
and every node/edge carries provenance back to the result and grounding it came from.

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

## Extend

Add any grounded dgroup (the `grounding` front end) to the corpus and it joins the graph with
its facts reified and its entities grounded; add a lineage report and its `extends` edges
appear between result nodes. Because the store is format-agnostic over dgroups, every upstream
ingestion path (LaTeX, HTML, prose) feeds the same graph. Add a second literature plus role
ascensions for its premise/guarantee relations and `analogous_to` edges connect it to the
first by shared causal structure.

# Lit-review — (object, attribute, relation) representation for concepts & reasoning

*Produced by an in-session Claude Code sub-agent (no API call), 2026-06-21. Web-sourced.*
*Serves Epic B (concept_graph). Decisions adopted in this module's build/schema.*

**Bottom line:** property-graph model in memory (objects-with-attributes + typed,
property-bearing edges); serialize as **sorted JSONL** (diffable, one record/line); reserve
a **higher-order / reified Step** relation so reasoning steps and SME's `CAUSE`-over-relations
fall out of one mechanism; keep an N-Triples exporter for interop.

## 1. Triple / graph models

| Model | Edge attrs | Higher-order | Diffable | Fit |
|---|---|---|---|---|
| RDF triples (Turtle/JSON-LD) | no (reification) | via reification | N-Triples line-based ✅ | substrate, weak edge props |
| RDF-star / RDF 1.2 | yes (triple terms) | native | tooling immature | strong but partial write support |
| **Property graph** | native node+edge props | awkward (edges can't point at edges) | no standard text ❌ | best model, worst audit |
| Hypergraph | n-ary native | natural | no canonical text | overkill |

**(object, attribute, relation)** = the property-graph mental model (object=node,
attributes=properties, relations=typed edges). **(subject, predicate, object)** = RDF, which
collapses the attribute/relation distinction we need for SME. → **property-graph in memory,
persisted as triples/JSONL.**

## 2. Reasoning-chain / argument representations

All converge on a **bipartite typed DAG**: content nodes + inference nodes.
- **AIF**: I-nodes (claims/premises) never connect directly — an **S-node** (scheme/inference)
  mediates: in-edges = premises, out-edge = conclusion.
- **Toulmin**: claim ← data, warrant, backing, qualifier, rebuttal (edge roles into an
  inference node).
- **Proof DAGs / LeanDojo / ProofFlow**: V partitioned (conditions/definitions/lemmas/steps),
  edge (u,v) = "u is prerequisite for v"; premise def-site/use-site edges.

→ Model a derivation step as a **reified `Step` node** with typed in-edges
(`premise`/`uses_lemma`/`uses_equation`) and an out-edge `concludes`; chains = DAGs of Steps.

## 3. SME / MAC-FAC connection (why this is the right shape)

SME consumes a typed higher-order predicate calculus (dgroups) with exactly three predicate
kinds: **attributes** (1-place, `(RED ball)`), **relations** (n-ary, `(GREATER p1 p2)`),
**higher-order relations** (predicates over predicates, `(CAUSE (GREATER ...) (FLOW ...))`).
**Systematicity** = prefer mappings carrying interconnected higher-order relations. MAC/FAC's
stage-1 filter uses **content vectors** = bag-of-predicate-labels whose dot product estimates
SME match size.

→ Our `(object, attribute, relation)` model is a *direct* serialization of SME dgroups; our
`proves`/`derives_from` (reified Step) relations *are* higher-order relations. So emit
`to_dgroup()` (entities/attributes/relations/higher_order) and `content_vector()` (predicate
bag) to feed a future SME/MAC-FAC matcher (Epic C) with zero remodeling.

## 4. On-disk format

Sorted **JSONL** (one node/edge per line, sorted keys, stable IDs, deterministic ordering):
keeps property-graph edge attributes *and* N-Triples line-diffability. Avoid Turtle (ordering
varies) and blank nodes (nondeterministic); mint stable/content-addressed IDs. Keep a
`to_ntriples()` exporter for interop / SHACL validation.

## 5. Tooling

| Tool | pip | pure-Py | use |
|---|---|---|---|
| rdflib | ✅ | ✅ | canonical store, N-Triples/JSON-LD |
| pyoxigraph | ✅ | ⚠ wheels | fast SPARQL store at scale |
| networkx | ✅ | ✅ | DAG ops (topo-sort, ancestors, cycle checks) |
| pySHACL | ✅ | ✅ | schema/shape validation |
| kglab | ✅ | ✅ | glue layer |

**Decision for this module:** keep the **pure-Python pydantic** model as source of truth
(zero new hard deps, fully auditable), emit sorted JSONL + an `to_ntriples()` exporter, and do
DAG checks in pure Python (cycle-safe). rdflib/networkx/pySHACL/pyoxigraph are recorded as
optional integrations for when SPARQL/SHACL/scale is needed — the JSONL contract makes adding
them non-invasive.

**Sources:** [property vs RDF (puppygraph)](https://www.puppygraph.com/blog/property-graph-vs-rdf) ·
[Neo4j RDF vs PG](https://neo4j.com/blog/knowledge-graph/rdf-vs-property-graphs-knowledge-graphs/) ·
[RDF vs LPG survey (arXiv 2304.13097)](https://arxiv.org/pdf/2304.13097) ·
[AIF spec](http://www.arg-tech.org/wp-content/uploads/2011/09/aif-spec.pdf) ·
[LeanDojo (arXiv 2306.15626)](https://arxiv.org/pdf/2306.15626) ·
[ProofFlow (arXiv 2510.15981)](https://arxiv.org/pdf/2510.15981) ·
[SME (Wikipedia)](https://en.wikipedia.org/wiki/Structure_mapping_engine) ·
[MAC/FAC (QRG)](https://www.qrg.northwestern.edu/ideas/macfac.htm) ·
[N-Triples](https://en.wikipedia.org/wiki/N-Triples) ·
[rdflib](https://pypi.org/project/rdflib/) · [networkx](https://networkx.org/) ·
[pyoxigraph](https://pypi.org/project/pyoxigraph/) · [kglab](https://github.com/DerwenAI/kglab)

"""Unsupervised cross-domain analogy over THREE literatures (Epic O).

Epic N connected two fields, but with a hand-declared role ascension. This drops that last
piece of injected knowledge: the ascension is **discovered** from each functor's position in
the shared ``CAUSE`` structure (``crossdomain.discover_role_ascension``), and a third
literature (statistical learning theory) is added to show it generalizes. The result is one
graph holding three fields' lineages, connected by ``analogous_to`` edges that were found with
zero hand-coded domain knowledge — surfacing the three-way analogy

    weighted exchangeability : coverage  ::  contraction : convergence  ::  uniform convergence : generalization

i.e. *the structural property that earns the guarantee*, recognized as the same role across
conformal prediction, optimization, and learning theory.
"""

from __future__ import annotations

import itertools
from pathlib import Path

from .build import add_lineage, add_result
from .crossdomain import (_load_corpus, cross_domain_analogies, add_analogies,
                          discover_role_ascension)
from .model import Graph
from .query import analogies_of

CORPORA = [
    ("conformal", "retrieval/library/conformal_theorems.json"),
    ("optimization", "grounding/dgroups/optimization_corpus.json"),
    ("learning", "grounding/dgroups/learning_corpus.json"),
    ("concentration", "grounding/dgroups/concentration_corpus.json"),
    ("online", "grounding/dgroups/online_learning_corpus.json"),
]


def _load_all(repo):
    import json

    from retrieval.engine import expr_from_json
    from analogy.predicates import Dgroup

    domains = {}
    for name, rel in CORPORA:
        corpus, texts, gr = _load_corpus(repo / rel)
        domains[name] = (corpus, texts, gr)
    # add the real paper to the conformal corpus
    paper = json.loads(
        (repo / "grounding" / "dgroups" / "arxiv_2006_06138_main.json").read_text())["target"]
    conf, ctext, cgr = domains["conformal"]
    conf[paper["name"]] = Dgroup(paper["name"], [expr_from_json(f) for f in paper["facts"]])
    ctext[paper["name"]] = paper.get("text", "")
    cgr[paper["name"]] = paper.get("groundings", {})
    return domains


def build_multidomain_graph(repo):
    from retrieval.lineage import lineage

    domains = _load_all(repo)
    ascension = discover_role_ascension(*[c for c, _, _ in domains.values()])

    g = Graph()
    for dname, (corpus, texts, gr) in domains.items():
        for name, dg in corpus.items():
            add_result(g, name, dg, texts.get(name, ""), gr.get(name, {}), domain=dname)
        add_lineage(g, lineage(corpus))

    analogies = []
    for da, db in itertools.combinations(domains, 2):       # every unordered domain pair
        analogies += cross_domain_analogies(domains[da][0], domains[db][0], ascension=ascension)
    add_analogies(g, analogies)
    return g, domains, ascension, analogies


def main(argv=None) -> int:
    here = Path(__file__).resolve().parents[2]
    repo = here.parent
    g, domains, ascension, analogies = build_multidomain_graph(repo)

    out = here / "results"
    out.mkdir(parents=True, exist_ok=True)
    g.save(out / "multidomain_nodes.jsonl", out / "multidomain_edges.jsonl")

    st = g.stats()
    print(f"multi-domain graph: {st['n_nodes']} nodes, {st['n_edges']} edges "
          f"({len(domains)} literatures: {', '.join(domains)})")
    print(f"  edge relations: {st['edge_relations']}")
    print(f"\nrole ascension DISCOVERED from CAUSE structure (no hand-declared map):")
    for fn, role in sorted(ascension.items()):
        print(f"    {fn:24s} -> {role}")
    print(f"\ncross-domain analogies (auto-discovered ascension): {len(analogies)}")

    # the N-way analogy: one representative result per field, pairwise analogous
    reps = ["weighted_conformal", "banach_contraction", "vc_generalization",
            "mcdiarmid_concentration", "online_gradient_descent"]
    print(f"\nthe {len(reps)}-way analogy — '{' : '.join(reps)}':")
    for r in reps:
        peers = [a["result"] for a in analogies_of(g, r)]
        print(f"  {r:24s} analogous to {sorted(set(peers) & set(reps) - {r})}")

    # invariants (CI gate; explicit raise so it holds under `python -O`)
    pairset = {(a["a"], a["b"]) for a in analogies}
    asc = ascension
    # the structural-property (PC/2) and guarantee (C/2) roles, discovered identical across ALL
    # five fields with no hand-declared map
    prop_roles = {asc.get(f) for f in
                  ("WEIGHTED_EXCHANGEABLE", "CONTRACTION", "UNIFORM_CONVERGENCE",
                   "BOUNDED_MARTINGALE", "NO_REGRET")}
    guar_roles = {asc.get(f) for f in
                  ("COVERAGE", "LINEAR_CONVERGENCE", "GENERALIZATION", "CONCENTRATION",
                   "SUBLINEAR_REGRET")}
    reps_set = set(reps)

    def _analogous(x, y):
        return (x, y) in pairset or (y, x) in pairset

    checks = [
        (len(prop_roles) == 1 and None not in prop_roles,
         "the PC/2 'structural property' role must be discovered identical across all 5 fields"),
        (len(guar_roles) == 1 and None not in guar_roles,
         "the C/2 'guarantee' role must be discovered identical across all 5 fields"),
        (all(_analogous(a, b) for a in reps_set for b in reps_set if a != b),
         "every pair of field representatives must be cross-domain analogous"),
        (Graph.load(out / "multidomain_nodes.jsonl", out / "multidomain_edges.jsonl").stats() == st,
         "save/load round-trip must preserve the multi-domain graph"),
    ]
    for ok, msg in checks:
        if not ok:
            raise SystemExit(f"multidomain invariant violated: {msg}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

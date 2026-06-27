"""Build the unified graph over the conformal corpus, persist it, and answer the questions
the whole project set out to answer — now as one queryable (object, attribute, relation)
graph rather than separate passes.
"""

from __future__ import annotations

import json
from pathlib import Path

from analogy.predicates import Dgroup

from .build import build
from .model import Graph
from .query import (entities_of, expr_string, extends_chain, facts_of,
                    reasoning_subgraph, results_using_functor)


def _load_inputs(repo, retr):
    import sys
    sys.path.insert(0, str(retr / "src"))
    from retrieval.engine import expr_from_json, load_library
    from retrieval.lineage import lineage

    lib = load_library(retr / "library" / "conformal_theorems.json")
    lib_raw = json.loads((retr / "library" / "conformal_theorems.json").read_text())
    paper = json.loads(
        (repo / "grounding" / "dgroups" / "arxiv_2006_06138_main.json").read_text())["target"]

    corpus = dict(lib)
    corpus[paper["name"]] = Dgroup(paper["name"], [expr_from_json(f) for f in paper["facts"]])

    texts = {k: v.get("text", "") for k, v in lib_raw.items() if not k.startswith("_")}
    texts[paper["name"]] = paper.get("text", "")
    groundings = {k: v.get("groundings", {}) for k, v in lib_raw.items() if not k.startswith("_")}
    groundings[paper["name"]] = paper.get("groundings", {})
    return corpus, texts, groundings, lineage(corpus)


def main(argv=None) -> int:
    here = Path(__file__).resolve().parents[2]
    repo = here.parent
    retr = repo / "retrieval"
    corpus, texts, groundings, lin = _load_inputs(repo, retr)

    g = build(corpus, texts, groundings, lin)
    out = here / "results"
    out.mkdir(parents=True, exist_ok=True)
    g.save(out / "nodes.jsonl", out / "edges.jsonl")

    st = g.stats()
    print(f"unified graph: {st['n_nodes']} nodes, {st['n_edges']} edges")
    print(f"  node kinds: {st['node_kinds']}")
    print(f"  edge relations: {st['edge_relations']}")

    paper = "arxiv-2006.06138-main"
    print(f"\nQ1 reasoning chain to COVERAGE in the paper (reified, reconstructed):")
    cov_fact = next((f for f in facts_of(g, paper) if g.nodes[f].label == "CAUSE"
                     and "COVERAGE" in expr_string(g, f)), None)
    if cov_fact:
        sub = reasoning_subgraph(g, cov_fact)
        print(f"  {sub['expr']}")
        print(f"  ({len(sub['nodes'])} nodes, {len(sub['edges'])} arg-edges in the chain)")

    print(f"\nQ2 which results use the LIKELIHOOD_RATIO relation?")
    print(f"  {results_using_functor(g, 'LIKELIHOOD_RATIO')}")

    print(f"\nQ3 lineage chain of the paper (extends edges):")
    print(f"  {' -> '.join(extends_chain(g, paper))}")

    # invariants (CI gate; explicit raise so it holds under `python -O`)
    rt = Graph.load(out / "nodes.jsonl", out / "edges.jsonl")
    checks = [
        (rt.stats() == st, "save/load round-trip must preserve the graph"),
        (results_using_functor(g, "LIKELIHOOD_RATIO") ==
         sorted(["weighted_conformal", "importance_weighting", paper]),
         "LIKELIHOOD_RATIO must be used by importance_weighting, weighted_conformal, paper"),
        (extends_chain(g, paper) == [paper, "weighted_conformal", "split_conformal"],
         "paper's lineage chain must be paper -> weighted -> split"),
        (cov_fact is not None and "COVERAGE" in reasoning_subgraph(g, cov_fact)["expr"],
         "the paper's CAUSE->COVERAGE reasoning chain must be reconstructable from the graph"),
    ]
    for ok, msg in checks:
        if not ok:
            raise SystemExit(f"graph invariant violated: {msg}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

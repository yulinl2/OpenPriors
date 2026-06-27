"""Generate analogical conjectures across the three-literature graph (Epic P).

Builds the unsupervised three-domain graph (Epic O), then for each discovered cross-domain
analogy runs candidate-inference transfer in BOTH directions, attaching the projected
conjectures to the target result. The headline: the analogy between conformal prediction and
Banach contraction theory generates the structural conjecture that the conformal calibration
procedure has a *fixed point* — a hypothesis produced purely from cross-domain structure.
"""

from __future__ import annotations

from pathlib import Path

from .model import Graph
from .multidomain import build_multidomain_graph
from .transfer import add_conjectures, transfer


def _corpus_of(domains, name):
    for corpus, _, _ in domains.values():
        if name in corpus:
            return corpus[name]
    return None


def main(argv=None) -> int:
    here = Path(__file__).resolve().parents[2]
    repo = here.parent
    g, domains, ascension, analogies = build_multidomain_graph(repo)

    # transfer across every discovered analogy, both directions
    total = 0
    for an in analogies:
        a, b = an["a"], an["b"]
        for base, target in ((a, b), (b, a)):
            conj = transfer(_corpus_of(domains, base), _corpus_of(domains, target), ascension)
            add_conjectures(g, base, target, conj)
            total += len(conj)

    out = here / "results"
    out.mkdir(parents=True, exist_ok=True)
    g.save(out / "transfer_nodes.jsonl", out / "transfer_edges.jsonl")

    st = g.stats()
    print(f"graph with analogical conjectures: {st['n_nodes']} nodes, {st['n_edges']} edges")
    print(f"  conjecture nodes: {st['node_kinds'].get('conjecture', 0)}; "
          f"conjectures edges: {st['edge_relations'].get('conjectures', 0)}")

    # the headline conjecture: conformal calibration has a fixed point (from Banach)
    fp = transfer(_corpus_of(domains, "banach_contraction"),
                  _corpus_of(domains, "weighted_conformal"), ascension)
    print(f"\nby analogy banach_contraction ~~ weighted_conformal, the system conjectures:")
    for c in fp:
        print(f"  [{c['status']}, conf {c['confidence']}] {c['projection']}")
        print(f"     (projecting {c['base_fact']}: the calibration map's Banach fixed point)")

    # a confirmation example: project the paper's extra structure onto weighted_conformal
    print(f"\nby analogy arxiv-2006.06138-main ~~ banach_contraction, the system conjectures "
          f"for the optimization domain:")
    for c in transfer(_corpus_of(domains, "arxiv-2006.06138-main"),
                      _corpus_of(domains, "banach_contraction"), ascension)[:3]:
        print(f"  [{c['status']}, conf {c['confidence']}] {c['projection']}")

    # invariants (CI gate; explicit raise so it holds under `python -O`)
    fixed_point = [c for c in fp if c["projection"].startswith("BANACH_FIXEDPOINT(cal_test")]
    rt = Graph.load(out / "transfer_nodes.jsonl", out / "transfer_edges.jsonl")
    checks = [
        (len(fixed_point) == 1 and fixed_point[0]["status"] == "novel",
         "the Banach->conformal analogy must yield the novel fixed-point conjecture"),
        ("skolem:" in fixed_point[0]["projection"] if fixed_point else False,
         "the conjectured fixed point must be an invented (skolem) object"),
        (total > 0 and st["node_kinds"].get("conjecture", 0) > 0,
         "conjectures must be generated and attached to the graph"),
        (rt.stats() == st, "save/load round-trip must preserve the conjecture graph"),
    ]
    for ok, msg in checks:
        if not ok:
            raise SystemExit(f"transfer invariant violated: {msg}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

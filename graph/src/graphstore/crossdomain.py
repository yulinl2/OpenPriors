"""Cross-domain analogy edges (Epic N): connect two literatures by shared causal structure.

Everything so far has run within one literature (conformal prediction). This module is the
project's core mechanism — SME structural analogy — operating ACROSS domains. Two results
from different literatures share no base vocabulary (``COVERAGE`` vs ``LINEAR_CONVERGENCE``),
so vanilla SME finds nothing (identicality constraint). But both are causal theorems of the
same abstract shape ``CAUSE(structural-premise -> guarantee)``. A small, declared **role
ascension** abstracts each domain's premise/guarantee relations to shared roles; under it,
SME aligns the ``CAUSE`` skeleton across domains and *discovers the object correspondence* —
e.g. weighted-conformal's calibration data ↔ Banach's contraction map, its interval ↔ the
iterate sequence. That correspondence, surfaced automatically, is the analogy.

The ascension is the only domain knowledge injected, and it is auditable: it states which
concrete relations play the *premise* vs *guarantee* role in a "structure ⇒ guarantee"
theorem. Everything else (the correspondence, the score) is computed by SME.
"""

from __future__ import annotations

from analogy.align import align, fmt_expr
from analogy.predicates import Dgroup

from .model import Edge, Graph

# Concrete relations -> the role they play in a "structural premise ⇒ guarantee" theorem.
# CAUSE stays identical across domains (it is the shared higher-order glue, not ascended).
ROLE_ASCENSION = {
    # statistical coverage literature
    "EXCHANGEABLE": "STRUCTURAL_PREMISE",
    "WEIGHTED_EXCHANGEABLE": "STRUCTURAL_PREMISE",
    "COVERAGE": "GUARANTEE",
    # contraction / convex-optimization literature
    "CONTRACTION": "STRUCTURAL_PREMISE",
    "STRONG_CONVEXITY_BOUND": "STRUCTURAL_PREMISE",
    "LINEAR_CONVERGENCE": "GUARANTEE",
}


def cross_domain_analogies(domain_a: dict[str, Dgroup], domain_b: dict[str, Dgroup],
                           ascension: dict | None = None, min_score: float = 3.0) -> list[dict]:
    """Every cross-domain result pair whose CAUSE skeleton aligns (under role ascension)
    above ``min_score``, with the SME-discovered object correspondence."""
    ascension = ROLE_ASCENSION if ascension is None else ascension
    out = []
    for na, da in domain_a.items():
        for nb, db in domain_b.items():
            g = align(da, db, ascension=ascension)
            if g.score >= min_score and g.correspondences:
                out.append({
                    "a": na, "b": nb,
                    "score": round(g.score, 3),
                    "correspondences": dict(sorted(g.correspondences.items())),
                    "shared_structure": sorted(fmt_expr(e) for e in g.matched_base),
                })
    return sorted(out, key=lambda r: (-r["score"], r["a"], r["b"]))


def add_analogies(g: Graph, analogies: list[dict]) -> None:
    """Add ``analogous_to`` edges between result nodes for each cross-domain analogy."""
    for an in analogies:
        src, dst = f"result::{an['a']}", f"result::{an['b']}"
        if src in g.nodes and dst in g.nodes:
            g.add_edge(Edge(src, dst, "analogous_to",
                            attrs={"score": an["score"],
                                   "correspondences": an["correspondences"],
                                   "shared_structure": an["shared_structure"]},
                            provenance="crossdomain"))


def _load_corpus(path):
    import json
    from pathlib import Path

    from retrieval.engine import expr_from_json

    raw = json.loads(Path(path).read_text())
    corpus, texts, groundings = {}, {}, {}
    for k, v in raw.items():
        if k.startswith("_"):
            continue
        corpus[v["name"]] = Dgroup(v["name"], [expr_from_json(f) for f in v["facts"]])
        texts[v["name"]] = v.get("text", "")
        groundings[v["name"]] = v.get("groundings", {})
    return corpus, texts, groundings


def build_two_domain_graph(repo):
    from retrieval.engine import expr_from_json
    from retrieval.lineage import lineage

    from .build import add_lineage, add_result

    conf, ctext, cgr = _load_corpus(repo / "retrieval" / "library" / "conformal_theorems.json")
    import json
    paper = json.loads(
        (repo / "grounding" / "dgroups" / "arxiv_2006_06138_main.json").read_text())["target"]
    conf[paper["name"]] = Dgroup(paper["name"], [expr_from_json(f) for f in paper["facts"]])
    ctext[paper["name"]] = paper.get("text", "")
    cgr[paper["name"]] = paper.get("groundings", {})

    opt, otext, ogr = _load_corpus(repo / "grounding" / "dgroups" / "optimization_corpus.json")

    g = Graph()
    for name, dg in conf.items():
        add_result(g, name, dg, ctext.get(name, ""), cgr.get(name, {}), domain="conformal")
    add_lineage(g, lineage(conf))
    for name, dg in opt.items():
        add_result(g, name, dg, otext.get(name, ""), ogr.get(name, {}), domain="optimization")
    add_lineage(g, lineage(opt))

    analogies = cross_domain_analogies(conf, opt)
    add_analogies(g, analogies)
    return g, conf, opt, analogies


def main(argv=None) -> int:
    from pathlib import Path

    from .query import analogies_of, extends_chain

    here = Path(__file__).resolve().parents[2]
    repo = here.parent
    g, conf, opt, analogies = build_two_domain_graph(repo)

    out = here / "results"
    out.mkdir(parents=True, exist_ok=True)
    g.save(out / "crossdomain_nodes.jsonl", out / "crossdomain_edges.jsonl")

    st = g.stats()
    print(f"two-domain graph: {st['n_nodes']} nodes, {st['n_edges']} edges")
    print(f"  edge relations: {st['edge_relations']}")
    print(f"\noptimization-domain lineage (same machinery, different literature):")
    print(f"  {' -> '.join(extends_chain(g, 'gd_strong_convexity'))}")
    print(f"\ncross-domain analogies (conformal ~~ optimization):")
    for an in analogies:
        print(f"  {an['a']}  ~~  {an['b']}   (score {an['score']})")
    top = analogies_of(g, "weighted_conformal")[0]
    print(f"\nexplaining one analogy — weighted_conformal ~~ {top['result']}:")
    print(f"  \"weighted conformal coverage is to its calibration data + reweighting")
    print(f"   as Banach convergence is to its contraction map + modulus\"")
    print(f"  SME correspondence: {top['correspondences']}")

    # invariants (CI gate; explicit raise so it holds under `python -O`)
    checks = [
        (extends_chain(g, "gd_strong_convexity") == ["gd_strong_convexity", "banach_contraction"],
         "optimization lineage must be gd_strong_convexity -> banach_contraction"),
        (any(a["a"] == "weighted_conformal" and a["b"] == "banach_contraction" for a in analogies),
         "weighted_conformal must be analogous to banach_contraction"),
        (top["correspondences"].get("cal_test") == "the_map",
         "the analogy must map the calibration data to the contraction map"),
        (top["correspondences"].get("the_interval") == "the_seq",
         "the analogy must map the prediction interval to the iterate sequence"),
        (Graph.load(out / "crossdomain_nodes.jsonl", out / "crossdomain_edges.jsonl").stats() == st,
         "save/load round-trip must preserve the two-domain graph"),
    ]
    for ok, msg in checks:
        if not ok:
            raise SystemExit(f"cross-domain invariant violated: {msg}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

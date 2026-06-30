"""Cross-domain analogy edges (Epic N): the SME mechanism operating across two literatures.

A declared role ascension abstracts each domain's premise/guarantee relations to shared
roles; under it, SME aligns the CAUSE skeleton across domains and discovers the object
correspondence. The conformal lineage and the contraction lineage live in one graph,
connected by analogous_to edges — domain-agnosticism plus genuine cross-domain analogy.
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(REPO / "analogy" / "src"))
sys.path.insert(0, str(REPO / "retrieval" / "src"))
sys.path.insert(0, str(REPO / "grounding" / "src"))

from analogy.predicates import Dgroup
from graphstore.crossdomain import (ROLE_ASCENSION, cross_domain_analogies,
                                    _load_corpus, build_two_domain_graph)
from graphstore.query import analogies_of, extends_chain
from retrieval.engine import expr_from_json

OPT, _, _ = _load_corpus(REPO / "grounding" / "dgroups" / "optimization_corpus.json")
CONF, _, _ = _load_corpus(REPO / "retrieval" / "library" / "conformal_theorems.json")
_paper = json.loads(
    (REPO / "grounding" / "dgroups" / "arxiv_2006_06138_main.json").read_text())["target"]
CONF[_paper["name"]] = Dgroup(_paper["name"], [expr_from_json(f) for f in _paper["facts"]])


def test_optimization_corpus_is_grounded():
    from grounding.verify import check_section
    raw = json.loads((REPO / "grounding" / "dgroups" / "optimization_corpus.json").read_text())
    for k, v in raw.items():
        if not k.startswith("_"):
            assert check_section(v)["passed"], k


def test_lineage_machinery_is_domain_agnostic():
    from retrieval.lineage import lineage
    rep = lineage(OPT)
    # the SAME lineage code recovers a development line in the contraction literature
    parents = rep["parents"]
    assert parents["gd_strong_convexity"] == "banach_contraction"
    edge = next(e for e in rep["edges"] if e["child"] == "gd_strong_convexity")
    assert any(s.startswith("STRONG_CONVEXITY_BOUND") for s in edge["novel_contributions"])


def test_no_cross_domain_match_without_ascension():
    # different base vocabulary -> SME's identicality constraint yields nothing
    assert cross_domain_analogies(CONF, OPT, ascension={}) == []


def test_cross_domain_analogy_is_discovered_under_role_ascension():
    ans = cross_domain_analogies(CONF, OPT)
    pairs = {(a["a"], a["b"]) for a in ans}
    # the weighted-conformal results are analogous to the contraction results
    assert ("weighted_conformal", "banach_contraction") in pairs
    assert (_paper["name"], "banach_contraction") in pairs
    # and the discovered correspondence is the meaningful one
    wc = next(a for a in ans if a["a"] == "weighted_conformal" and a["b"] == "banach_contraction")
    assert wc["correspondences"]["cal_test"] == "the_map"        # calibration data ~ contraction map
    assert wc["correspondences"]["the_interval"] == "the_seq"    # interval ~ iterate sequence
    assert wc["score"] >= 3.0


def test_split_conformal_does_not_spuriously_match():
    # split conformal's premise is 1-ary plain exchangeability; it can't align with the
    # 2-ary structural premises, so it yields no (false) cross-domain analogy.
    ans = cross_domain_analogies(CONF, OPT)
    assert not any(a["a"] == "split_conformal" for a in ans)


def test_role_ascension_only_injects_role_knowledge():
    # the only domain knowledge is which concrete relations are premises vs guarantees;
    # CAUSE (the shared higher-order glue) is deliberately NOT ascended.
    assert set(ROLE_ASCENSION.values()) == {"STRUCTURAL_PREMISE", "GUARANTEE"}
    assert "CAUSE" not in ROLE_ASCENSION


def test_two_domain_graph_has_both_lineages_and_analogy_edges():
    g, conf, opt, analogies = build_two_domain_graph(REPO)
    rels = g.stats()["edge_relations"]
    assert rels.get("extends", 0) >= 3 and rels.get("analogous_to", 0) >= 4
    # result nodes are tagged by domain
    assert g.nodes["result::banach_contraction"].attrs["domain"] == "optimization"
    assert g.nodes["result::weighted_conformal"].attrs["domain"] == "conformal"
    # analogies are queryable from a node
    a = analogies_of(g, "weighted_conformal")
    assert any(x["result"] == "banach_contraction" for x in a)
    # both literatures' lineages coexist in the one graph
    assert extends_chain(g, "gd_strong_convexity") == ["gd_strong_convexity", "banach_contraction"]
    assert extends_chain(g, _paper["name"])[:2] == [_paper["name"], "weighted_conformal"]

"""Unsupervised cross-domain analogy over three literatures (Epic O).

The role ascension is DISCOVERED from each functor's position in the CAUSE structure (no
hand-declared map), and reproduces the Epic N analogies while extending to a third field
(learning theory). The three-way analogy weighted-conformal ~~ Banach ~~ VC-generalization
falls out, and the deeper two-step chains score higher.
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

from graphstore.crossdomain import (_load_corpus, cross_domain_analogies,
                                    discover_role_ascension)
from graphstore.multidomain import build_multidomain_graph
from graphstore.query import analogies_of, extends_chain

CONF, _, _ = _load_corpus(REPO / "retrieval" / "library" / "conformal_theorems.json")
OPT, _, _ = _load_corpus(REPO / "grounding" / "dgroups" / "optimization_corpus.json")
LEARN, _, _ = _load_corpus(REPO / "grounding" / "dgroups" / "learning_corpus.json")


def test_learning_corpus_is_grounded():
    from grounding.verify import check_section
    raw = json.loads((REPO / "grounding" / "dgroups" / "learning_corpus.json").read_text())
    for k, v in raw.items():
        if not k.startswith("_"):
            assert check_section(v)["passed"], k


def test_discovered_roles_align_the_three_fields():
    asc = discover_role_ascension(CONF, OPT, LEARN)
    # the "structural property" relation gets the SAME discovered role in all three fields
    assert asc["WEIGHTED_EXCHANGEABLE"] == asc["CONTRACTION"] == asc["UNIFORM_CONVERGENCE"]
    # so does the "guarantee" relation
    assert asc["COVERAGE"] == asc["LINEAR_CONVERGENCE"] == asc["GENERALIZATION"]
    # the role token encodes CAUSE-position (P/C) and arity, and CAUSE itself is not a role
    assert asc["WEIGHTED_EXCHANGEABLE"].endswith("::2") and "CAUSE" not in asc
    # a premise-only 1-ary relation is a distinct role (won't match the 2-ary structural ones)
    assert asc["EXCHANGEABLE"] != asc["WEIGHTED_EXCHANGEABLE"]


def test_cause_is_never_ascended_even_when_nested():
    # a (hypothetical) corpus with a nested CAUSE-of-CAUSE must NOT give CAUSE a role token,
    # or it could match a non-CAUSE functor of the same arity and corrupt alignment.
    from analogy.predicates import Dgroup
    inner = ("CAUSE", ("A", "x", "y"), ("B", "x", "y"))
    nested = Dgroup("n", [["CAUSE", inner, ("C", "x", "y")]])
    asc = discover_role_ascension({"n": nested})
    assert "CAUSE" not in asc


def test_discovered_ascension_reproduces_epic_n_analogy():
    asc = discover_role_ascension(CONF, OPT)
    ans = cross_domain_analogies(CONF, OPT, ascension=asc)
    wc = next((a for a in ans if a["a"] == "weighted_conformal" and a["b"] == "banach_contraction"),
              None)
    assert wc is not None and wc["score"] == 7.0
    assert wc["correspondences"]["cal_test"] == "the_map"
    assert wc["correspondences"]["the_interval"] == "the_seq"


def test_no_hand_declared_ascension_needed():
    # with NO ascension at all there is no cross-domain match; the discovery supplies it
    assert cross_domain_analogies(CONF, LEARN, ascension={}) == []
    asc = discover_role_ascension(CONF, LEARN)
    assert cross_domain_analogies(CONF, LEARN, ascension=asc)


def test_three_way_analogy_in_one_graph():
    g, domains, asc, analogies = build_multidomain_graph(REPO)
    assert set(domains) == {"conformal", "optimization", "learning"}
    # one representative per field, all pairwise analogous
    reps = {"weighted_conformal", "banach_contraction", "vc_generalization"}
    for r in reps:
        peers = {a["result"] for a in analogies_of(g, r)}
        assert reps - {r} <= peers, r
    # all three lineages coexist
    assert extends_chain(g, "margin_generalization") == ["margin_generalization", "vc_generalization"]
    assert extends_chain(g, "gd_strong_convexity") == ["gd_strong_convexity", "banach_contraction"]


def test_deeper_causal_chain_scores_higher():
    # gd (strong-convexity -> contraction -> convergence) ~~ margin (margin -> uniform conv ->
    # generalization): both two-step chains, so the systematic match outscores a one-step pair.
    asc = discover_role_ascension(OPT, LEARN)
    ans = cross_domain_analogies(OPT, LEARN, ascension=asc)
    deep = next(a for a in ans if a["a"] == "gd_strong_convexity" and a["b"] == "margin_generalization")
    shallow = next(a for a in ans if a["a"] == "banach_contraction" and a["b"] == "vc_generalization")
    assert deep["score"] > shallow["score"]

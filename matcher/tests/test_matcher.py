"""Tests for MAC retrieval + renaming-invariance + systematicity."""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(REPO / "concept_graph" / "src"))

from concept_graph.schema import Concept, ConceptGraph, Relation
from concept_graph.sme import content_vector
from matcher import invariance, mac


def _g(slug="g"):
    cs = [Concept(id="a", kind="theorem", role="assert", source_node="a"),
          Concept(id="b", kind="proof", role="assert", source_node="b"),
          Concept(id="c", kind="equation", role="formalize", source_node="c")]
    rs = [Relation(id="r1", subject="b", predicate="proves", object="a",
                   higher_order=True, provenance="x"),
          Relation(id="r2", subject="b", predicate="derives_from", object="c",
                   higher_order=True, provenance="y")]
    return ConceptGraph(slug=slug, concepts=cs, relations=rs)


def test_cosine_basics():
    assert mac.cosine({"x": 1}, {"x": 1}) == 1.0
    assert mac.cosine({"x": 1}, {"y": 1}) == 0.0
    assert 0 < mac.cosine({"x": 1, "y": 1}, {"x": 1}) < 1


def test_renaming_invariance_holds():
    r = invariance.check_renaming_invariance(_g())
    assert r["passed"] and r["content_vector_invariant"] and r["relation_multiset_invariant"]


def test_content_vector_is_not_trivially_constant():
    """Non-vacuity: the vector MUST change if a predicate changes, else invariance is empty."""
    g = _g()
    g2 = g.model_copy(deep=True)
    g2.relations[0].predicate = "cites"   # change a predicate label
    assert content_vector(g) != content_vector(g2)


def test_systematicity_depth():
    s = invariance.systematicity(_g())
    assert s["n_higher_order_relations"] == 2 and s["max_reasoning_depth"] >= 1


def test_rank_against_uses_dot_and_excludes_self():
    vs = {"a": {"x": 2, "y": 1}, "b": {"x": 2, "y": 1}, "c": {"z": 1}}
    ranking = mac.rank_against("a", vs)
    # ranks by the sound dot-product MAC score: dot(a,b)=5, dot(a,c)=0
    assert ranking[0] == ("b", 5.0) and dict(ranking)["c"] == 0.0 and "a" not in dict(ranking)
    assert mac.mac_score is mac.dot  # the retrieval primitive is the dot product


def test_real_graphs_all_invariant():
    from matcher.cli import load_graphs
    graphs = load_graphs(REPO / "concept_graph" / "graphs")
    assert graphs, "concept graphs must exist"
    for slug, g in graphs.items():
        assert invariance.check_renaming_invariance(g)["passed"], slug

"""Query DSL over the unified graph (Epic S): the pipeline graph is interrogable.

Path-finding crosses lineage into analogy edges (the literatures are concretely linked),
shared_ancestor walks the lineage, explain_analogy exposes the SME correspondence, and
conjectures_with_verdicts surfaces predictions + how they were judged.
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(REPO / "analogy" / "src"))
sys.path.insert(0, str(REPO / "retrieval" / "src"))
sys.path.insert(0, str(REPO / "grounding" / "src"))

from graphstore.dsl import (conjectures_with_verdicts, explain_analogy, find,
                            shared_ancestor, shortest_path)
from graphstore.pipeline import run_pipeline

G = run_pipeline(REPO)["graph"]


def test_path_crosses_lineage_and_analogy_to_link_literatures():
    p = shortest_path(G, "result::split_conformal", "result::vc_generalization")
    assert p and p[-1]["to"] == "result::vc_generalization"
    rels = {s["relation"] for s in p}
    # the only way across fields is an analogy edge; the path uses one
    assert "analogous_to" in rels


def test_path_to_missing_node_is_none():
    assert shortest_path(G, "result::split_conformal", "nope::x") is None
    assert shortest_path(G, "nope::x", "result::split_conformal") is None


def test_shared_ancestor_walks_the_lineage():
    assert shared_ancestor(G, "arxiv-2006.06138-main", "split_conformal") == "split_conformal"
    assert shared_ancestor(G, "margin_generalization", "vc_generalization") == "vc_generalization"
    # two results in different fields share no lineage ancestor
    assert shared_ancestor(G, "weighted_conformal", "banach_contraction") is None


def test_explain_analogy_exposes_the_correspondence():
    ex = explain_analogy(G, "weighted_conformal", "banach_contraction")
    assert ex and ex["score"] == 7.0
    assert ex["correspondences"]["cal_test"] == "the_map"
    # symmetric: queryable from either endpoint
    assert explain_analogy(G, "banach_contraction", "weighted_conformal") is not None
    # non-analogous pair -> None
    assert explain_analogy(G, "split_conformal", "weighted_conformal") is None


def test_conjectures_with_verdicts_surface_judgments():
    cs = conjectures_with_verdicts(G, "weighted_conformal")
    assert cs
    # judged ones sort before unjudged; at least one carries a plausible verdict
    assert any(c["verdict"] == "plausible" for c in cs)
    fp = [c for c in cs if (c["projection"] or "").startswith("BANACH_FIXEDPOINT(cal_test")]
    assert fp and fp[0]["verdict"] == "plausible"


def test_find_locates_nodes_by_label():
    hits = find(G, "FIXEDPOINT")
    assert any("functor::BANACH_FIXEDPOINT" == h for h in hits)
    assert find(G, "BANACH_FIXEDPOINT", kind="functor") == ["functor::BANACH_FIXEDPOINT"]
    assert find(G, "this label does not exist") == []

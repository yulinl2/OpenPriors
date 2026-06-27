"""Reasoning lineage (Epic L): reconstruct a literature's *extends* DAG from grounded
structure. Over the conformal corpus the backbone must come out as the real development line
split_conformal -> weighted_conformal -> arxiv 2006.06138, each edge carrying the residual
the descendant adds — with importance_weighting recovered as an independent lemma.
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(REPO / "analogy" / "src"))
sys.path.insert(0, str(REPO / "grounding" / "src"))

from analogy.predicates import Dgroup
from retrieval.engine import expr_from_json, load_library
from retrieval.lineage import _coverage, lineage

LIB = load_library(ROOT / "library" / "conformal_theorems.json")
PAPER_JSON = REPO / "grounding" / "dgroups" / "arxiv_2006_06138_main.json"


def _corpus():
    corpus = dict(LIB)
    p = json.loads(PAPER_JSON.read_text())["target"]
    corpus[p["name"]] = Dgroup(p["name"], [expr_from_json(f) for f in p["facts"]])
    return corpus


def test_backbone_is_the_real_development_line():
    rep = lineage(_corpus())
    parents = rep["parents"]
    assert parents["weighted_conformal"] == "split_conformal"
    assert parents["arxiv-2006.06138-main"] == "weighted_conformal"
    # the paper's DIRECT parent is the most specific ancestor (weighted), not split —
    # transitive reduction, even though split is also reused by the paper.
    edge = next(e for e in rep["edges"] if e["child"] == "arxiv-2006.06138-main")
    assert "split_conformal" in [n["result"] for n in rep["nodes"]]
    assert edge["parent"] == "weighted_conformal"


def test_each_edge_isolates_the_descendants_contribution():
    rep = lineage(_corpus())
    edges = {e["child"]: e for e in rep["edges"]}
    # weighted conformal's novelty over split = the covariate-shift / reweighting machinery
    w = edges["weighted_conformal"]["novel_contributions"]
    assert any(s.startswith("WEIGHTED_EXCHANGEABLE") for s in w)
    assert any(s.startswith("COVARIATE_SHIFT") for s in w)
    # the paper's novelty over weighted = counterfactual + nested ITE (and ONLY that)
    p = edges["arxiv-2006.06138-main"]["novel_contributions"]
    assert any(s.startswith("COUNTERFACTUAL") for s in p)
    assert any(s.startswith("NESTED") for s in p)
    assert not any(s.startswith("WEIGHTED_EXCHANGEABLE") for s in p)


def test_novelty_decreases_along_the_chain():
    rep = lineage(_corpus())
    edges = {e["child"]: e for e in rep["edges"]}
    # the paper reuses far more of its parent than weighted conformal reused of split:
    # a later, more incremental step has lower novelty.
    assert edges["arxiv-2006.06138-main"]["novelty"] < edges["weighted_conformal"]["novelty"]
    assert 0.0 < edges["arxiv-2006.06138-main"]["novelty"] < 1.0


def test_importance_weighting_is_a_lemma_root():
    rep = lineage(_corpus())
    # the 1-fact likelihood-ratio lemma has no ancestor in the corpus -> it's a root,
    # but it is reused (an ancestor) by both weighted conformal and the paper.
    assert "importance_weighting" in rep["roots"]
    reusers = [n["result"] for n in rep["nodes"] if "importance_weighting" in n["ancestors"]]
    assert "weighted_conformal" in reusers and "arxiv-2006.06138-main" in reusers


def test_coverage_is_asymmetric():
    c = _corpus()
    # the paper contains all of weighted conformal's structure, but not vice versa:
    # that asymmetry is what orients the lineage.
    assert _coverage(c["weighted_conformal"], c["arxiv-2006.06138-main"]) == 1.0
    assert _coverage(c["arxiv-2006.06138-main"], c["weighted_conformal"]) < 1.0

"""Real published paper, end-to-end (Epic K): arXiv 2006.06138 (Lei & Candes, Conformal
Inference of Counterfactuals and ITE) lifted from prose into a grounded dgroup, then
decomposed against the conformal-prediction theorems it builds on.

The whole pipeline on a genuine paper: MAC retrieves the correct nearest prior (weighted
conformal prediction), FAC quantifies the reuse, and set-cover isolates the residual —
which is exactly the paper's contribution: applying weighted conformal prediction to
COUNTERFACTUAL outcomes and the NESTED individual-treatment-effect procedure.
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
from retrieval.decompose import decompose
from retrieval.engine import expr_from_json, load_library, retrieve

LIB = load_library(ROOT / "library" / "conformal_theorems.json")
PAPER_JSON = REPO / "grounding" / "dgroups" / "arxiv_2006_06138_main.json"


def _paper():
    d = json.loads(PAPER_JSON.read_text())["target"]
    return Dgroup(d["name"], [expr_from_json(f) for f in d["facts"]])


def test_mac_retrieves_weighted_conformal_as_nearest_prior():
    r = retrieve(_paper(), LIB, mac_k=len(LIB))
    # MAC ranks weighted conformal prediction top, well above the split-conformal and
    # importance-weighting distractors (concrete margin, not a vacuous "non-empty").
    ranking = dict(r["mac_ranking"])
    assert r["mac_ranking"][0][0] == "weighted_conformal"
    assert ranking["weighted_conformal"] > 0.9
    assert ranking["weighted_conformal"] - ranking["split_conformal"] > 0.4
    # FAC confirms it as the nearest prior with substantial (but partial) reuse.
    assert r["nearest_prior"] == "weighted_conformal"
    assert 0.15 < r["nearest_novelty"] < 0.35


def test_decomposition_residual_is_counterfactual_and_nested():
    rep = decompose(_paper(), LIB)
    # the paper is covered by exactly one known theorem — weighted conformal prediction —
    assert rep["covering_priors"] == ["weighted_conformal"]
    assert rep["covered_facts"] == 7 and rep["n_facts"] == 9
    # and what's left is its genuine contribution: counterfactual outcomes + the nested ITE.
    novel = rep["novel_contributions"]
    assert any(s.startswith("COUNTERFACTUAL") for s in novel)
    assert any(s.startswith("NESTED") for s in novel)
    # the borrowed conformal machinery is NOT reported as novel
    assert not any(s.startswith("WEIGHTED_EXCHANGEABLE") for s in novel)
    assert not any(s.startswith("CONFORMAL_INTERVAL") for s in novel)


def test_residual_is_a_strict_nonempty_fraction():
    rep = decompose(_paper(), LIB)
    # a real contribution: not fully reducible to the prior, not disjoint from it either
    assert 0.0 < rep["coverage_fraction"] < 1.0 and rep["residual_facts"]


def test_paper_and_library_are_grounded():
    from grounding.verify import check_section
    assert check_section(json.loads(PAPER_JSON.read_text())["target"])["passed"]
    lib_data = json.loads((ROOT / "library" / "conformal_theorems.json").read_text())
    for key, entry in lib_data.items():
        if not key.startswith("_"):
            assert check_section(entry)["passed"], key

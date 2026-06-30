"""Per-result novelty scoring across the unified graph (Epic W).

Every result gets a precise novelty = 1 - best-prior coverage (the IP-judge / MDL framing),
written onto its node. The scores must agree with the validated lineage (a descendant's
novelty = its residual over its parent; a field's base result = 1.0) and the real-paper cases.
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(REPO / "analogy" / "src"))
sys.path.insert(0, str(REPO / "retrieval" / "src"))
sys.path.insert(0, str(REPO / "grounding" / "src"))

from analogy.predicates import Dgroup
from graphstore.novelty_graph import coverage_of, result_novelty
from graphstore.pipeline import run_pipeline

REP = run_pipeline(REPO)
G = REP["graph"]
NOV = REP["novelty"]


def test_base_results_are_maximally_novel():
    # a field's base result has no covering prior -> novelty 1.0, nearest_prior None
    for base in ("split_conformal", "banach_contraction", "vc_generalization",
                 "mcdiarmid_concentration"):
        assert NOV[base]["novelty"] == 1.0 and NOV[base]["nearest_prior"] is None


def test_novelty_matches_the_validated_lineage_and_papers():
    # the real paper is a low-novelty extension of weighted conformal (cf. Epic K)
    assert NOV["arxiv-2006.06138-main"]["nearest_prior"] == "weighted_conformal"
    assert NOV["arxiv-2006.06138-main"]["novelty"] == 0.2222
    # weighted conformal is a substantial extension of split conformal (cf. lineage 0.71)
    assert NOV["weighted_conformal"]["nearest_prior"] == "split_conformal"
    assert NOV["weighted_conformal"]["novelty"] == 0.7143
    # a descendant is strictly less novel than its own ancestor
    assert NOV["arxiv-2006.06138-main"]["novelty"] < NOV["weighted_conformal"]["novelty"]


def test_residual_is_the_contribution_over_the_nearest_prior():
    # the paper's residual = COUNTERFACTUAL + NESTED (its contribution over weighted conformal)
    novel = NOV["arxiv-2006.06138-main"]["novel_contributions"]
    assert any(s.startswith("COUNTERFACTUAL") for s in novel)
    assert any(s.startswith("NESTED") for s in novel)


def test_scores_are_written_onto_the_result_nodes():
    n = G.nodes["result::weighted_conformal"]
    assert n.attrs["novelty"] == 0.7143
    assert n.attrs["nearest_prior"] == "split_conformal"


def test_coverage_helper_is_capped_and_directional():
    P = Dgroup("p", [("REL", "a", "b")])
    R = Dgroup("r", [("REL", "x", "y"), ("OTHER", "x", "y")])
    # P covers exactly the one matching fact of R's two -> 0.5, never above 1.0
    assert coverage_of(P, R) == 0.5
    # a larger prior can fully cover, but result_novelty excludes priors larger than R
    assert coverage_of(R, P) == 1.0


def test_larger_descendant_does_not_cover_its_ancestor():
    # the paper (9 facts) contains weighted conformal (7), but novelty must rank weighted by a
    # NOT-larger prior (split), never by the paper -> weighted stays novel, not ~0
    assert NOV["weighted_conformal"]["nearest_prior"] != "arxiv-2006.06138-main"
    assert NOV["weighted_conformal"]["novelty"] > 0.5

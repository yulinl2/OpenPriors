"""Second real paper end-to-end (Epic V): Nesterov's accelerated gradient method.

Parallels Epic K in the optimization field: the paper is lifted into a grounded dgroup,
decomposed against the priors it builds on (residual = the OPTIMAL accelerated rate), and its
structural property joins the cross-domain analogy web at the same discovered role.
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

from graphstore.realpaper2 import run

REP = run(REPO)


def test_paper_and_priors_are_grounded():
    from grounding.verify import check_section
    paper = json.loads((REPO / "grounding" / "dgroups" / "nesterov_paper.json").read_text())["target"]
    assert check_section(paper)["passed"]
    lib = json.loads((REPO / "retrieval" / "library" / "nesterov_priors.json").read_text())
    for k, v in lib.items():
        if not k.startswith("_"):
            assert check_section(v)["passed"], k


def test_decomposition_isolates_the_optimal_rate_as_the_contribution():
    dec = REP["decompose"]
    # the estimate-sequence machinery is read as borrowed...
    assert dec["covering_priors"] == ["estimate_sequence"]
    # ...and what's left is Nesterov's genuine contribution: the optimal accelerated rate
    assert any(s.startswith("OPTIMAL_RATE") for s in dec["novel_contributions"])
    # gradient_descent_smooth (sublinear, no momentum) covers nothing -> not in the cover
    assert "gradient_descent_smooth" not in dec["covering_priors"]


def test_real_contribution_is_partial_reuse_not_full_nor_disjoint():
    dec = REP["decompose"]
    assert 0.0 < dec["coverage_fraction"] < 1.0 and dec["residual_facts"]


def test_momentum_is_discovered_as_the_structural_property_role():
    asc = REP["ascension"]
    # the momentum step is read (from its CAUSE position) as the same PC/2 "structural
    # property that earns the guarantee" role as contraction
    assert asc.get("MOMENTUM") == asc.get("CONTRACTION")
    assert asc.get("MOMENTUM", "").startswith("ROLE::PC::")


def test_paper_joins_the_cross_domain_analogy_web():
    analogies = REP["analogies"]
    a = next((x for x in analogies if x["a"] == "nesterov_acceleration"
              and x["b"] == "banach_contraction"), None)
    assert a is not None and a["score"] >= 3.0
    # "Nesterov's method is to its accelerated convergence as the contraction map is to ..."
    assert a["correspondences"].get("method") == "the_map"

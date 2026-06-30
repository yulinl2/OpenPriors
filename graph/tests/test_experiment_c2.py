"""Numerical experiment for research direction C2 (Epic Z): the discovery loop's proposed
direction, backed by actual computation. The system's own conjecture-refinement said to test
the contraction-modulus-vs-concentrability relationship on small finite MDPs; this runs it.
"""

import json
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from graphstore.experiment_c2 import (_stationary, _stochastic, chi2, op_norm_L2mu,
                                      run_experiment)

REP = run_experiment(seed=0)


def test_modulus_at_stationary_is_exactly_gamma():
    # Bertsekas-Tsitsiklis: ||P||_{L2(d)} = 1, so T = gamma*P has L2(d) modulus = gamma
    g = REP["gamma"]
    for tr in REP["trials"]:
        assert abs(tr["points"][0]["modulus"] - g) < 1e-3


def test_modulus_grows_monotonically_with_chi2_mismatch():
    for tr in REP["trials"]:
        pts = tr["points"]
        for a, b in zip(pts, pts[1:]):
            assert b["chi2"] >= a["chi2"] - 1e-4
            assert b["modulus"] >= a["modulus"] - 1e-4


def test_strong_mismatch_breaks_contraction():
    # a badly-weighted operator need not be a contraction at all (modulus > gamma, even > 1)
    for tr in REP["trials"]:
        assert tr["points"][-1]["modulus"] > REP["gamma"] + 1e-3
    assert any(tr["points"][-1]["modulus"] > 1.0 for tr in REP["trials"])


def test_chi2_is_zero_at_perfect_match_and_positive_otherwise():
    d = [0.4, 0.3, 0.2, 0.1]
    assert abs(chi2(d, d)) < 1e-12
    assert chi2(d, [0.25, 0.25, 0.25, 0.25]) > 0


def test_op_norm_at_stationary_is_one():
    rng = random.Random(3)
    P = _stochastic(5, rng)
    d = _stationary(P)
    # the un-discounted operator norm of P under L2(d) is 1 (up to power-iteration tolerance)
    assert abs(op_norm_L2mu(P, d) - 1.0) < 5e-3


def test_experiment_is_deterministic():
    assert run_experiment(seed=0) == run_experiment(seed=0)
    assert run_experiment(seed=0) != run_experiment(seed=1)


def test_experiment_realizes_the_committed_c2_research_direction():
    # tie-back: the experiment is exactly what research direction C2's next_step proposed
    art = json.loads((REPO / "graph" / "evaluations" / "research_directions.json").read_text())
    c2 = next(d for d in art["directions"] if d["id"] == "C2")
    assert "finite MDP" in c2["next_step"] and "chi-square" in c2["next_step"]

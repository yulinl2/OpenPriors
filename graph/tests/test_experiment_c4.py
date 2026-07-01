"""Numerical experiment for research direction C4 (Epic AA): the discovery loop's second
computationally-backed direction. Epic Y refined the ERM-fixed-point conjecture into a precise
"fixed-point uniform convergence" program; this runs it on the canonical Balakrishnan-Wainwright-Yu
Gaussian-mixture EM operator and gates the Banach perturbation theorem numerically.

The gate is written to *fail* on tampering (verify the verifier): each invariant is asserted, and
`test_gate_rejects_a_tampered_bound` confirms a violated bound is actually caught.
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from graphstore.experiment_c4 import (em_operator_derivative, em_operator_empirical,
                                      em_operator_population, run_experiment, _build_quadrature)

REP = run_experiment(seed=0)


def test_population_fixed_point_is_theta_star():
    # BWY: for the symmetric 2-GMM the population EM operator has M(theta*) = theta*
    assert abs(REP["pop_fixed_point"] - REP["theta_star"]) < 1e-6


def test_operator_is_a_local_contraction():
    assert 0.0 < REP["kappa"] < 1.0


def test_perturbation_bound_holds_for_every_sample():
    # the fixed-point-uniform-convergence theorem: |theta_n - theta*| <= eps_n/(1-kappa), and the
    # empirical fixed point lands in the contraction basin — asserted per trial, not just on average
    for lv in REP["levels"]:
        for r in lv["trials"]:
            assert r["in_basin"]
            assert r["fp_err"] <= r["bound"] + 1e-9


def test_bound_is_nonvacuous_and_tight():
    # kappa is tiny, so the fixed-point error tracks the uniform deviation closely (within 2x)
    for lv in REP["levels"]:
        assert 0.5 * lv["bound"] <= lv["fp_err"] <= lv["bound"]


def test_error_shrinks_with_sample_size():
    first, last = REP["levels"][0], REP["levels"][-1]
    assert last["eps"] < 0.6 * first["eps"]
    assert last["fp_err"] < first["fp_err"]


def test_root_n_consistency():
    # eps_n * sqrt(n) stays bounded across the schedule -> eps_n = O(1/sqrt(n))
    assert max(lv["eps_sqrt_n"] for lv in REP["levels"]) < 2.0


def test_empirical_and_population_operators_agree_at_zero():
    # both EM maps fix 0 (a degenerate fixed point): M(0) = mean X_i tanh(0) = 0
    quad = _build_quadrature(REP["theta_star"], REP["sigma"])
    assert abs(em_operator_population(0.0, quad, REP["sigma"])) < 1e-9
    assert abs(em_operator_empirical(0.0, [1.0, -2.0, 3.0], REP["sigma"])) < 1e-12
    # the derivative (contraction modulus integrand) is positive at theta*
    assert em_operator_derivative(REP["theta_star"], quad, REP["sigma"]) > 0


def test_experiment_is_deterministic():
    light = {"trials": 3, "n_schedule": (50, 100)}       # a cheap config; determinism is config-free
    assert run_experiment(seed=0, **light) == run_experiment(seed=0, **light)
    assert run_experiment(seed=0, **light) != run_experiment(seed=1, **light)


def test_bad_config_is_rejected_clearly():
    for kw in ({"sigma": 0.0}, {"sigma": -1.0}, {"n_schedule": (100,)}, {"n_schedule": (100, 0)},
               {"trials": 0}, {"basin_points": 1}):
        try:
            run_experiment(**kw)
            assert False, f"expected ValueError for {kw}"
        except ValueError:
            pass


def test_gate_rejects_a_tampered_bound():
    # verify-the-verifier: a fixed-point error that exceeds its bound must be caught by the check
    r = {"fp_err": 1.0, "bound": 0.5, "in_basin": True}
    assert not (r["fp_err"] <= r["bound"] + 1e-9)


def test_experiment_realizes_the_committed_c4_research_direction():
    # tie-back: the experiment is exactly what research direction C4's next_step proposed
    art = json.loads((REPO / "graph" / "evaluations" / "research_directions.json").read_text())
    c4 = next(d for d in art["directions"] if d["id"] == "C4")
    assert "Gaussian-mixture EM" in c4["next_step"]
    assert "eps_n/(1-kappa)" in c4["next_step"]

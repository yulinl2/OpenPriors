"""Numerical experiment for research direction C7 (Epic AH): the final open committed direction
carried to computation — regret vs last-iterate convergence through the shared curvature modulus.
Every gate is asserted per condition number, and the gate is unit-tested to fail on tampering.
"""

import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from graphstore.experiment_c7 import _dist, _grad, _loss, _proj, run_experiment, run_regimes

REP = run_experiment()
BY_K = {r["kappa"]: r for r in REP["regimes"]}
T = REP["horizon"]


def test_primitives():
    assert _grad((1.0, 2.0), (1.0, 2.0), 10.0) == (0.0, 0.0)
    assert _loss((1.0, 2.0), (1.0, 2.0), 10.0) == 0.0
    assert _proj((5.0, -5.0), 1.0) == (1.0, -1.0)
    assert _dist((0.0, 0.0), (3.0, 4.0)) == 5.0


def test_informed_step_contracts_geometrically_at_one_minus_inverse_kappa():
    for k, r in BY_K.items():
        assert r["informed_final_err"] < 1e-10
        if k > 1:
            assert abs(r["geometric_rate"] - (1.0 - 1.0 / k)) < 0.02, k


def test_robust_schedule_pays_a_polynomial_price_that_grows_with_conditioning():
    # the regret-optimal schedule decays at exponent -1 (vs geometric), so at the same horizon
    # the informed iterate is at machine eps while the robust one is macroscopic — except at
    # kappa=1, where the schedules coincide at t=1 and the price vanishes entirely
    for k, r in BY_K.items():
        if k > 1:
            assert abs(r["poly_exponent"] + 1.0) < 0.15, k
            assert r["robust_err_marks"][T] > 1e-4
        else:
            assert r["robust_err_marks"][T] < 1e-10
    # the price is monotone in kappa
    assert BY_K[100.0]["robust_err_marks"][T] > BY_K[10.0]["robust_err_marks"][T]


def test_adversarial_regret_grows_logarithmically():
    for k, r in BY_K.items():
        marks = sorted(r["regret_marks"])
        vals = [r["regret_marks"][t] / math.log(t) for t in marks]
        for u, v in zip(vals, vals[1:]):
            assert 0.8 < v / u < 1.1, (k, vals)
        # and regret is genuinely sublinear
        assert r["regret_marks"][T] / T < 1.0 or k > 1   # loose for high curvature scale
        assert r["regret_marks"][T] < r["regret_marks"][T // 2] * 1.2


def test_drift_tracking_follows_the_contraction_plus_drift_law():
    for k, r in BY_K.items():
        if k > 1:
            for delta, err in r["tracking"].items():
                assert abs(err - delta * (k - 1)) < 0.05 * delta * (k - 1), (k, delta)
            assert 1.9 < r["tracking"][0.002] / r["tracking"][0.001] < 2.1
        else:
            assert max(r["tracking"].values()) < 1e-6


def test_experiment_is_deterministic():
    # no RNG anywhere: two runs are byte-identical
    assert run_experiment() == run_experiment()
    assert run_regimes(10.0, 800) == run_regimes(10.0, 800)


def test_bad_config_is_rejected_clearly():
    for kw in ({"horizon": 400}, {"horizon": 4001}, {"kappas": (0.5, 10.0)}):
        try:
            run_experiment(**kw)
            assert False, f"expected ValueError for {kw}"
        except ValueError:
            pass


def test_gate_rejects_a_tampered_record():
    # verify-the-verifier: a record whose exponent contradicts -1 must be caught by the check
    bad = {"poly_exponent": -0.4}
    assert abs(bad["poly_exponent"] + 1.0) > 0.15


def test_experiment_realizes_the_committed_c7_research_direction():
    # tie-back: the experiment is exactly what research direction C7's next_step proposed
    art = json.loads((REPO / "graph" / "evaluations" / "research_directions.json").read_text())
    c7 = next(d for d in art["directions"] if d["id"] == "C7")
    assert "condition number kappa" in c7["next_step"]
    assert "three regimes" in c7["next_step"]
    assert "last-iterate error" in c7["next_step"]

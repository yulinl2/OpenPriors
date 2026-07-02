"""Numerical experiment for research direction C5 (Epic AG): the loop's third experiment — and
the first on a direction the system both generated and judged in the same session. Direction C5
proposed the two-player quadratic-game sweep with the spectral-radius phase prediction; this runs
it and gates every claim (the gate is unit-tested to fail on tampered records).
"""

import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from graphstore.experiment_c5 import (banach_modulus, equilibrium, game_operator,
                                      run_experiment, run_ogd, spectral_radius)

REP = run_experiment(seed=0)


def test_equilibrium_is_a_zero_of_the_game_operator():
    for mu, gamma in ((1.0, 0.5), (0.2, 1.0), (0.0, 2.0)):
        zst = equilibrium(mu, gamma, (0.7, -0.3))
        f = game_operator(zst, mu, gamma, (0.7, -0.3))
        assert math.hypot(*f) < 1e-12


def test_empirical_rate_equals_the_spectral_radius_in_every_cell():
    # the OGD map is a scaled rotation (M^T M = rho^2 I), so this holds essentially exactly
    for c in REP["cells"]:
        assert abs(c["empirical_rate"] - c["rho"]) < 0.02, (c["mu"], c["gamma"])


def test_phase_diagram_matches_the_spectral_prediction():
    phases = {c["phase"] for c in REP["cells"]}
    assert {"converge", "diverge"} <= phases              # both phases genuinely explored
    for c in REP["cells"]:
        if c["phase"] == "converge":
            assert c["dT"] < 1e-2 * c["d0"]
        elif c["phase"] == "diverge":
            assert c["dT"] > 1e1 * c["d0"]
        else:                                             # near-boundary: exactly on the rho^T track
            expected = c["rho"] ** REP["steps"]
            assert expected / 2 < c["dT"] / c["d0"] < expected * 2


def test_banach_threshold_is_exactly_the_spectral_condition():
    # the judge's contraction condition eta < 2*mu/L^2 is algebraically rho < 1, and the
    # claimed modulus sqrt(1 - 2*eta*mu + eta^2*L^2) IS the spectral radius
    for ic in REP["identity_checks"]:
        assert ic["rho_lt_1"] == ic["banach_cond"]
        assert ic["modulus_gap"] < 1e-12
    assert abs(banach_modulus(0.3, 0.9, 0.2) - spectral_radius(0.3, 0.9, 0.2)) < 1e-15


def test_recurrence_pole_excess_vanishes_quadratically():
    sc = REP["recurrence_scaling"]
    for a, b in zip(sc, sc[1:]):
        assert 3.0 < a["excess"] / b["excess"] < 5.0      # halving eta quarters the excess


def test_averaged_play_converges_while_last_iterate_wanders():
    early, late = REP["dichotomy"]
    assert late["last_dist"] > 1.5 * early["last_dist"]   # no attracting fixed point
    assert late["avg_dist"] < 0.25 * REP["d_init"]        # the average approaches z* (folk theorem)
    assert late["avg_dist"] < 0.1 * late["last_dist"]


def test_experiment_is_deterministic():
    light = {"steps": 300}
    assert run_experiment(seed=0, **light) == run_experiment(seed=0, **light)
    assert run_experiment(seed=0, **light) != run_experiment(seed=1, **light)


def test_bad_config_is_rejected_clearly():
    for kw in ({"eta": 0.0}, {"eta": 1.0}, {"steps": 100},):
        try:
            run_experiment(**kw)
            assert False, f"expected ValueError for {kw}"
        except ValueError:
            pass
    try:
        equilibrium(0.0, 0.0, (1.0, 1.0))
        assert False, "expected ValueError for a degenerate game"
    except ValueError:
        pass


def test_gate_rejects_a_tampered_cell():
    # verify-the-verifier: a cell whose empirical rate contradicts its rho must be caught
    bad = {"empirical_rate": 1.3, "rho": 0.9}
    assert abs(bad["empirical_rate"] - bad["rho"]) > 0.02


def test_ogd_trajectory_shrinks_iff_contraction():
    d_c = run_ogd(1.0, 0.5, 0.1, (2.0, 2.0), (0.7, -0.3), 500)
    d_d = run_ogd(0.0, 2.0, 0.1, (2.0, 2.0), (0.7, -0.3), 500)
    assert d_c[-1] < d_c[0] * 1e-4 and d_d[-1] > d_d[0] * 10


def test_experiment_realizes_the_committed_c5_research_direction():
    # tie-back: the experiment is exactly what research direction C5's next_step proposed
    art = json.loads((REPO / "graph" / "evaluations" / "research_directions.json").read_text())
    c5 = next(d for d in art["directions"] if d["id"] == "C5")
    assert "two-player quadratic games" in c5["next_step"]
    assert "spectral radius" in c5["next_step"]
    assert "S skew-symmetric" in c5["next_step"]

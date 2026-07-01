"""Numerical experiment for research direction C4 (Epic AA): the second computationally-backed
direction, closing another turn of the discover -> predict -> evaluate -> investigate ->
experiment loop.

The discovery loop (Epic Y) refined the open ERM-fixed-point conjecture into a precise, literature-
grounded direction C4 whose ``next_step`` reads: *"Prove a 'fixed-point uniform convergence'
theorem ... combine with Banach perturbation (``||theta_n - theta*|| <= eps_n/(1-kappa)``) to get a
finite-sample fixed-point error; instantiate concretely for Gaussian-mixture EM to recover the
Balakrishnan-Wainwright-Yu rate purely from an operator-class uniform-convergence argument."*

This module **runs that experiment**, in pure Python (no numpy — the project doctrine), on exactly
the canonical Balakrishnan-Wainwright-Yu (2017, *Annals of Statistics*) setting: the symmetric
two-component Gaussian mixture ``X ~ (1/2) N(theta*, sigma^2) + (1/2) N(-theta*, sigma^2)`` with
known ``sigma``, whose population EM operator is

    M(theta) = E[ X * tanh(X * theta / sigma^2) ]      (population fixed point M(theta*) = theta*)

and whose empirical EM operator is the sample average ``M_n(theta) = mean_i X_i tanh(X_i theta /
sigma^2)`` — an *estimating-equation / self-consistency* map, precisely the fixed-point structure
C4 identifies for M-estimators.

The defensible core it confirms — the **fixed-point-uniform-convergence theorem** — is the Banach
perturbation bound applied to the EM map: with ``eps_n = sup_theta |M_n(theta) - M(theta)|`` the
uniform (operator-class) deviation on the contraction basin and ``kappa = sup_theta |M'(theta)| < 1``
the local contraction modulus,

    |theta_n - theta*|  <=  eps_n / (1 - kappa),

so a *uniform* closeness of the empirical operator to the population operator transfers directly
into fixed-point closeness. The experiment verifies this bound holds for **every** simulated sample
(not just on average), that it is non-vacuous and tight, and that the empirical fixed-point error
decays at the ``1/sqrt(n)`` uniform-convergence rate — recovering the BWY guarantee purely from an
operator-class uniform-convergence argument, exactly as research direction C4 proposed.
"""

from __future__ import annotations

import math
import random


def _normal_pdf(x: float, mu: float, sigma: float) -> float:
    return math.exp(-0.5 * ((x - mu) / sigma) ** 2) / (sigma * math.sqrt(2.0 * math.pi))


def _mixture_density(x: float, theta_star: float, sigma: float) -> float:
    """Density of the symmetric two-component mixture (1/2)N(theta*,s^2)+(1/2)N(-theta*,s^2)."""
    return 0.5 * _normal_pdf(x, theta_star, sigma) + 0.5 * _normal_pdf(x, -theta_star, sigma)


def _build_quadrature(theta_star: float, sigma: float, points: int = 4001) -> tuple:
    """A fixed deterministic grid + mixture weights for the *population* expectations E[.].

    Riemann quadrature over a wide window (nine sigma past each mode); normalised so the weights
    sum to one. Kept deterministic so the population operator — and hence every reported number —
    is reproducible without any RNG."""
    span = abs(theta_star) + 9.0 * sigma
    lo, hi = -span, span
    dx = (hi - lo) / (points - 1)
    xs = [lo + dx * i for i in range(points)]
    ws = [_mixture_density(x, theta_star, sigma) * dx for x in xs]
    s = sum(ws) or 1.0
    return xs, [w / s for w in ws]


def em_operator_population(theta: float, quad: tuple, sigma: float) -> float:
    """Population EM operator M(theta) = E[ X tanh(X theta / sigma^2) ] for the symmetric 2-GMM."""
    xs, ws = quad
    s2 = sigma * sigma
    return sum(ws[i] * xs[i] * math.tanh(xs[i] * theta / s2) for i in range(len(xs)))


def em_operator_derivative(theta: float, quad: tuple, sigma: float) -> float:
    """M'(theta) = E[ (X^2 / sigma^2) * sech^2(X theta / sigma^2) ] — for the contraction modulus."""
    xs, ws = quad
    s2 = sigma * sigma
    return sum(ws[i] * (xs[i] * xs[i] / s2) / math.cosh(xs[i] * theta / s2) ** 2
               for i in range(len(xs)))


def em_operator_empirical(theta: float, data: list, sigma: float) -> float:
    """Empirical EM operator M_n(theta) = mean_i X_i tanh(X_i theta / sigma^2) — the self-
    consistency map whose fixed point is the EM estimate."""
    s2 = sigma * sigma
    return sum(x * math.tanh(x * theta / s2) for x in data) / len(data)


def _fixed_point(op, x0: float, iters: int = 500, tol: float = 1e-12) -> float:
    """Iterate a contraction op to its fixed point from x0 (Banach iteration)."""
    x = x0
    for _ in range(iters):
        nx = op(x)
        if abs(nx - x) < tol:
            return nx
        x = nx
    # fail loudly: a non-converged last iterate is not a fixed point, so any bound built on it
    # would be meaningless (verify-the-verifier — never report a silent non-solution)
    raise RuntimeError(f"fixed-point iteration failed to converge within {iters} steps "
                       f"(last |delta|={abs(op(x) - x):.2e})")


def _sample(n: int, theta_star: float, sigma: float, rng: random.Random) -> list:
    """Draw n points from the symmetric two-component Gaussian mixture."""
    out = []
    for _ in range(n):
        mu = theta_star if rng.random() < 0.5 else -theta_star
        out.append(rng.gauss(mu, sigma))
    return out


def run_experiment(theta_star: float = 3.0, sigma: float = 1.0,
                   n_schedule: tuple = (100, 200, 400, 800, 1600),
                   trials: int = 30, basin_points: int = 41, seed: int = 0) -> dict:
    """Instantiate the BWY Gaussian-mixture EM setting and measure, for a sweep of sample sizes,
    the uniform operator deviation ``eps_n``, the empirical fixed-point error, and the Banach
    bound ``eps_n / (1 - kappa)`` — the fixed-point-uniform-convergence theorem in action."""
    if sigma <= 0:
        raise ValueError(f"sigma must be positive, got {sigma}")
    if len(n_schedule) < 2:
        raise ValueError(f"n_schedule needs >= 2 sizes to show a rate, got {len(n_schedule)}")
    if any(n <= 0 for n in n_schedule):
        raise ValueError(f"all sample sizes must be positive, got {n_schedule}")
    if trials <= 0:
        raise ValueError(f"trials must be positive, got {trials}")
    if basin_points < 2:
        raise ValueError(f"basin_points needs >= 2 to form a grid, got {basin_points}")

    quad = _build_quadrature(theta_star, sigma)
    pop_fixed_point = _fixed_point(lambda t: em_operator_population(t, quad, sigma), theta_star * 0.5)

    # the local contraction basin around theta*, and the modulus kappa = sup |M'| over it
    lo, hi = theta_star * 0.5, theta_star * 1.5
    basin = [lo + (hi - lo) * i / (basin_points - 1) for i in range(basin_points)]
    kappa = max(abs(em_operator_derivative(t, quad, sigma)) for t in basin)

    levels = []
    for n in n_schedule:
        recs = []
        for tr in range(trials):
            # seed on the distinct string "seed:trial:n" — random.Random hashes it with SHA-512,
            # so the stream is deterministic across runs and injective in (seed, trial, n) for any n
            rng = random.Random(f"{seed}:{tr}:{n}")
            data = _sample(n, theta_star, sigma, rng)
            theta_n = _fixed_point(lambda t: em_operator_empirical(t, data, sigma), theta_star)
            eps = max(abs(em_operator_empirical(t, data, sigma)
                          - em_operator_population(t, quad, sigma)) for t in basin)
            bound = eps / (1.0 - kappa)
            recs.append({"eps": eps, "fp_err": abs(theta_n - pop_fixed_point), "bound": bound,
                         "in_basin": lo <= theta_n <= hi})
        aeps = sum(r["eps"] for r in recs) / trials
        afp = sum(r["fp_err"] for r in recs) / trials
        levels.append({"n": n, "eps": aeps, "fp_err": afp, "bound": aeps / (1.0 - kappa),
                       "eps_sqrt_n": aeps * math.sqrt(n), "trials": recs})

    return {"theta_star": theta_star, "sigma": sigma, "kappa": kappa,
            "pop_fixed_point": pop_fixed_point, "n_schedule": list(n_schedule), "levels": levels}


def main(argv=None) -> int:
    rep = run_experiment()
    k = rep["kappa"]
    print(f"research direction C4 — fixed-point uniform convergence on the Balakrishnan-Wainwright-"
          f"Yu\n  symmetric 2-Gaussian-mixture EM operator M(theta)=E[X tanh(X theta/sigma^2)] "
          f"(theta*={rep['theta_star']}, sigma={rep['sigma']}):")
    print(f"  population fixed point M(theta*)=theta* recovered as {rep['pop_fixed_point']:.6f}; "
          f"local contraction modulus kappa={k:.4f} (< 1)\n")
    print(f"  claim: uniform operator closeness transfers to fixed-point closeness — "
          f"|theta_n - theta*| <= eps_n/(1-kappa).\n")
    print(f"  {'n':>6} {'eps_n (sup|M_n-M|)':>20} {'fp error':>12} {'bound eps_n/(1-k)':>18} "
          f"{'eps_n*sqrt(n)':>14}")
    for lv in rep["levels"]:
        print(f"  {lv['n']:>6} {lv['eps']:>20.4f} {lv['fp_err']:>12.4f} {lv['bound']:>18.4f} "
              f"{lv['eps_sqrt_n']:>14.3f}")

    # invariants (CI gate; explicit raise so it holds under `python -O`)
    if abs(rep["pop_fixed_point"] - rep["theta_star"]) > 1e-6:
        raise SystemExit(f"population EM fixed point should be theta*={rep['theta_star']}, "
                         f"got {rep['pop_fixed_point']}")
    if not (0.0 < k < 1.0):
        raise SystemExit(f"EM operator must be a local contraction (0 < kappa < 1), got {k}")
    # 1. the fixed-point-uniform-convergence theorem holds for EVERY simulated sample
    for lv in rep["levels"]:
        for r in lv["trials"]:
            if not r["in_basin"]:
                raise SystemExit("empirical fixed point left the contraction basin")
            if r["fp_err"] > r["bound"] + 1e-9:
                raise SystemExit(f"perturbation bound violated at n={lv['n']}: "
                                 f"fp_err={r['fp_err']} > bound={r['bound']}")
    # 2. the bound is non-vacuous and tight (kappa tiny => error tracks eps_n closely)
    for lv in rep["levels"]:
        if not (0.5 * lv["bound"] <= lv["fp_err"] <= lv["bound"]):
            raise SystemExit(f"bound should be tight (fp_err within [0.5, 1]x bound) at n={lv['n']}")
    # 3. the empirical fixed-point error shrinks with sample size (uniform-convergence consistency)
    first, last = rep["levels"][0], rep["levels"][-1]
    if last["eps"] > 0.6 * first["eps"]:
        raise SystemExit("uniform deviation eps_n should fall clearly as n grows")
    # 4. it decays at the 1/sqrt(n) rate: eps_n * sqrt(n) stays bounded across the schedule
    if max(lv["eps_sqrt_n"] for lv in rep["levels"]) > 2.0:
        raise SystemExit("eps_n should decay at the root-n rate (eps_n*sqrt(n) bounded)")
    print(f"\n  confirmed: M(theta*)=theta* and kappa={k:.4f}<1; the Banach bound "
          f"|theta_n-theta*| <= eps_n/(1-kappa) holds for\n  all {len(rep['levels']) * len(rep['levels'][0]['trials'])} "
          f"samples and is tight, and the fixed-point error decays at the root-n uniform-\n  "
          f"convergence rate — recovering the Balakrishnan-Wainwright-Yu guarantee from an "
          f"operator-class\n  uniform-convergence argument, as research direction C4 proposed.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

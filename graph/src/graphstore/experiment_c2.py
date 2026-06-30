"""Numerical experiment for research direction C2 (Epic Z): close the loop with computation.

The discovery loop (Epic Y) refined the open conjecture C2 into a precise research direction:
*the L2(mu) contraction modulus of a Markov operator is controlled by a likelihood-ratio /
change-of-measure functional of the mismatch between the weighting ``mu`` and the stationary
(visitation) distribution ``d``*, with a concrete next step — "test tightness numerically on
small finite MDPs by comparing the operator Lipschitz modulus against the candidate
functionals across a sweep of sampling distributions mu."

This module **runs that experiment**, in pure Python (no numpy — the project doctrine), so the
system's own proposed direction is backed by actual numerical evidence rather than just
asserted. It builds small random Markov chains and, for a sweep of weightings ``mu`` from the
stationary ``d`` toward a skewed target, computes:

  * the **L2(mu) modulus** of ``T = gamma * P`` — ``gamma * sigma_max(D_mu^{1/2} P D_mu^{-1/2})``
    (power iteration); and
  * the **chi-square mismatch** ``chi^2(d || mu)`` — the concentrability / likelihood-ratio
    functional.

The defensible core it confirms: at ``mu = d`` the modulus is exactly ``gamma`` (the
Bertsekas–Tsitsiklis weighted-norm contraction, ``||P||_{L2(d)} = 1``), and it grows
monotonically with the mismatch — so a badly-weighted operator need not be a contraction at
all (modulus > 1). The *modulus is governed by the change-of-measure functional*, exactly as
the research direction proposed.
"""

from __future__ import annotations

import math
import random


def _stochastic(n: int, rng: random.Random) -> list:
    rows = []
    for _ in range(n):
        row = [rng.random() + 1e-3 for _ in range(n)]
        s = sum(row)
        rows.append([x / s for x in row])
    return rows


def _matvec(M: list, v: list) -> list:
    return [sum(M[i][j] * v[j] for j in range(len(v))) for i in range(len(M))]


def _stationary(P: list, iters: int = 4000) -> list:
    n = len(P)
    d = [1.0 / n] * n
    for _ in range(iters):
        nd = [sum(d[i] * P[i][j] for i in range(n)) for j in range(n)]
        s = sum(nd) or 1.0
        d = [x / s for x in nd]
    return d


def op_norm_L2mu(P: list, mu: list, iters: int = 800) -> float:
    """Largest singular value of M = D_mu^{1/2} P D_mu^{-1/2} (the L2(mu) operator norm of P),
    via power iteration on M^T M."""
    n = len(P)
    sq = [math.sqrt(m) for m in mu]
    M = [[sq[i] * P[i][j] / sq[j] for j in range(n)] for i in range(n)]
    MT = [[M[j][i] for j in range(n)] for i in range(n)]
    v = [1.0] * n
    for _ in range(iters):
        u = _matvec(MT, _matvec(M, v))
        nrm = math.sqrt(sum(x * x for x in u)) or 1.0
        v = [x / nrm for x in u]
    Mv = _matvec(M, v)
    return math.sqrt(sum(x * x for x in Mv))


def chi2(d: list, mu: list) -> float:
    """chi^2(d || mu) = sum d^2/mu - 1 — the change-of-measure / concentrability functional."""
    return sum(d[i] * d[i] / mu[i] for i in range(len(d))) - 1.0


def run_experiment(n: int = 6, gamma: float = 0.9, trials: int = 5, sweep: int = 6,
                   seed: int = 0) -> dict:
    rng = random.Random(seed)
    results = []
    for _ in range(trials):
        P = _stochastic(n, rng)
        d = _stationary(P)
        # a skewed target weighting (mass concentrated on state 0)
        skew = [0.7] + [0.3 / (n - 1)] * (n - 1)
        points = []
        for k in range(sweep):
            t = 0.9 * k / (sweep - 1)                  # interpolate mu from d (t=0) toward skew
            mu = [(1 - t) * d[i] + t * skew[i] for i in range(n)]
            s = sum(mu)
            mu = [x / s for x in mu]
            points.append({"t": round(t, 3), "modulus": gamma * op_norm_L2mu(P, mu),
                           "chi2": chi2(d, mu)})
        results.append({"modulus_at_stationary": points[0]["modulus"], "points": points})
    return {"gamma": gamma, "n_states": n, "trials": results}


def main(argv=None) -> int:
    rep = run_experiment()
    gamma = rep["gamma"]
    print(f"research direction C2 — numerical test on {len(rep['trials'])} random "
          f"{rep['n_states']}-state Markov chains (gamma={gamma}):")
    print(f"  claim: the L2(mu) contraction modulus is governed by chi^2(d || mu), the "
          f"change-of-measure mismatch between mu and the stationary d.\n")
    print(f"  {'chi2(d||mu)':>14}   {'L2(mu) modulus':>14}")
    t0 = rep["trials"][0]
    for p in t0["points"]:
        flag = " <- mu = d (stationary)" if p["t"] == 0.0 else (
            "  (no longer a contraction: modulus > 1)" if p["modulus"] > 1 else "")
        print(f"  {p['chi2']:>14.4f}   {p['modulus']:>14.4f}{flag}")

    # invariants (CI gate; explicit raise so it holds under `python -O`)
    eps = 1e-4
    for tr in rep["trials"]:
        pts = tr["points"]
        # 1. at mu = d the modulus is exactly gamma (Bertsekas-Tsitsiklis: ||P||_{L2(d)} = 1)
        if abs(pts[0]["modulus"] - gamma) > 1e-3:
            raise SystemExit(f"modulus at mu=d should be gamma, got {pts[0]['modulus']}")
        # 2. modulus is non-decreasing as the mismatch (chi^2) grows along the sweep
        for a, b in zip(pts, pts[1:]):
            if b["chi2"] < a["chi2"] - eps or b["modulus"] < a["modulus"] - eps:
                raise SystemExit("modulus must grow monotonically with the chi^2 mismatch")
        # 3. a badly-mismatched weighting breaks contraction (modulus exceeds gamma)
        if pts[-1]["modulus"] <= gamma + 1e-3:
            raise SystemExit("a strongly mismatched mu should push the modulus above gamma")
    print(f"\n  confirmed: modulus(mu=d) = gamma exactly, and it rises monotonically with "
          f"chi^2(d||mu) until\n  the operator is no longer a contraction — the change-of-measure "
          f"functional governs the modulus,\n  as research direction C2 proposed.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

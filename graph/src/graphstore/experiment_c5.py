"""Numerical experiment for research direction C5 (Epic AG): the third computationally-backed
direction — and the first the system both *generated and judged* in the same loop.

The fifth literature (online learning, Epic AC) projected the conjecture *"no-regret play has a
fixed point"* (from the Banach analogy); the in-session judge ruled it **uncertain** — false in
general (last-iterate cycling in zero-sum games; averaged play converges to the coarse-correlated-
equilibrium set), literally true under strong monotonicity. The discovery loop (Epic AF) refined
that into direction C5, whose ``next_step`` proposes: *"a sweep on parametrized two-player
quadratic games: operator F(z) = (mu*I + gamma*S)z + b with S skew-symmetric ... run vanilla
projected OGD ... and separately compute the spectral radius of the linearized map. Plot the
empirical convergence/cycling phase diagram against the predicted spectral-radius-equals-1
curve."*

This module **runs that experiment**, in pure Python (no numpy — the project doctrine), on the
2-D instance of exactly that family, where everything is checkable in closed form:

  * OGD is the linear map ``M = I - eta*(mu*I + gamma*S)`` with eigenvalues
    ``(1 - eta*mu) ± i*eta*gamma``, so the spectral radius is
    ``rho = sqrt((1 - eta*mu)^2 + (eta*gamma)^2)``;
  * the judge's Banach-contraction condition ``eta < 2*mu/L^2`` (with ``L = sqrt(mu^2+gamma^2)``)
    is algebraically **identical** to ``rho < 1``, and the claimed contraction modulus
    ``sqrt(1 - 2*eta*mu + eta^2*L^2)`` **equals** ``rho`` — the experiment verifies both;
  * sweeping the strong-monotonicity dial ``mu`` and rotation dial ``gamma`` produces the phase
    diagram: the **empirical per-step rate matches rho** in every cell, cells with ``rho < 1``
    converge geometrically, cells with ``rho > 1`` diverge (the bilinear pole ``mu = 0`` spirals
    out at exactly ``sqrt(1 + eta^2*gamma^2)``), and the growth rate vanishes as ``eta -> 0``
    at the quadratic scaling ``rho - 1 ~ eta^2*gamma^2/2`` (the continuous-time recurrence pole);
  * at the bilinear pole with vanishing step the **averaged play stays bounded while the last
    iterate wanders away** — the C5 dichotomy (CCE-style averaged limit vs. no attracting fixed
    point) observed directly.

The constrained cells (does projection convert recurrence into convergence?) remain the
direction's open frontier and are deliberately NOT gated here.
"""

from __future__ import annotations

import math
import random


def game_operator(z: tuple, mu: float, gamma: float, b: tuple) -> tuple:
    """F(z) = (mu*I + gamma*S) z + b for the 2-D skew matrix S = [[0, 1], [-1, 0]]."""
    x, y = z
    return (mu * x + gamma * y + b[0], mu * y - gamma * x + b[1])


def equilibrium(mu: float, gamma: float, b: tuple) -> tuple:
    """The unique z* with F(z*) = 0 (det = mu^2 + gamma^2 > 0 whenever the game is nontrivial)."""
    det = mu * mu + gamma * gamma
    if det <= 0:
        raise ValueError(f"degenerate game: mu^2 + gamma^2 must be positive, got mu={mu}, gamma={gamma}")
    return ((-b[0] * mu + b[1] * gamma) / det, (-b[1] * mu - b[0] * gamma) / det)


def spectral_radius(mu: float, gamma: float, eta: float) -> float:
    """Closed-form spectral radius of the OGD map M = I - eta*(mu*I + gamma*S)."""
    return math.sqrt((1.0 - eta * mu) ** 2 + (eta * gamma) ** 2)


def banach_modulus(mu: float, gamma: float, eta: float) -> float:
    """The judge's claimed contraction modulus sqrt(1 - 2*eta*mu + eta^2*L^2), L^2 = mu^2+gamma^2."""
    return math.sqrt(1.0 - 2.0 * eta * mu + eta * eta * (mu * mu + gamma * gamma))


def run_ogd(mu: float, gamma: float, eta: float, z0: tuple, b: tuple, steps: int) -> list:
    """Vanilla constant-step OGD from z0; returns the distance-to-equilibrium trajectory."""
    zst = equilibrium(mu, gamma, b)
    z = z0
    dists = [math.hypot(z[0] - zst[0], z[1] - zst[1])]
    for _ in range(steps):
        f = game_operator(z, mu, gamma, b)
        z = (z[0] - eta * f[0], z[1] - eta * f[1])
        dists.append(math.hypot(z[0] - zst[0], z[1] - zst[1]))
    return dists


def run_experiment(eta: float = 0.1, steps: int = 2000, seed: int = 0) -> dict:
    """Sweep the (mu, gamma) phase plane and measure, per cell, the empirical asymptotic
    per-step rate of the last iterate against the closed-form spectral radius; plus the
    threshold identity, the recurrence-pole scaling, and the averaged-play dichotomy."""
    if not (0.0 < eta < 1.0):
        raise ValueError(f"eta must be in (0, 1), got {eta}")
    if steps < 200:
        raise ValueError(f"steps must be >= 200 for a stable rate estimate, got {steps}")
    rng = random.Random(seed)
    b = (0.7, -0.3)

    # 1. the phase diagram: empirical rate vs closed-form rho in every cell
    cells = []
    for mu in (1.0, 0.5, 0.2, 0.1, 0.0):
        for gamma in (0.5, 1.0, 2.0):
            zst = equilibrium(mu, gamma, b)              # gamma > 0 throughout the sweep, so det > 0
            z0 = (zst[0] + rng.uniform(0.5, 1.5), zst[1] + rng.uniform(0.5, 1.5))
            d = run_ogd(mu, gamma, eta, z0, b, steps)
            # M = I - eta*(mu*I + gamma*S) is a scaled rotation (M^T M = rho^2 I), so the
            # per-step rate is exactly rho at every step; measure over an early window so a
            # strongly-contracting cell hasn't underflowed to zero yet
            k = min(200, steps)
            emp = (d[k] / d[0]) ** (1.0 / k) if d[0] > 0 else 0.0
            rho = spectral_radius(mu, gamma, eta)
            band = 5e-3                                  # cells within the band sit near rho = 1
            phase = ("converge" if rho < 1.0 - band
                     else "diverge" if rho > 1.0 + band else "boundary")
            cells.append({"mu": mu, "gamma": gamma, "rho": rho, "empirical_rate": emp,
                          "phase": phase, "d0": d[0], "dT": d[-1]})

    # 2. threshold identity + modulus identity at random points
    identity_checks = []
    for _ in range(50):
        mu, gamma, e = rng.uniform(0.01, 1.0), rng.uniform(0.0, 2.0), rng.uniform(0.01, 0.5)
        L2 = mu * mu + gamma * gamma
        identity_checks.append({
            "rho_lt_1": spectral_radius(mu, gamma, e) < 1.0,
            "banach_cond": e < 2.0 * mu / L2,
            "modulus_gap": abs(spectral_radius(mu, gamma, e) - banach_modulus(mu, gamma, e)),
        })

    # 3. recurrence-pole scaling: at mu=0, rho - 1 ~ eta^2*gamma^2/2 as eta -> 0
    gamma0 = 1.0
    scaling = [{"eta": e, "excess": spectral_radius(0.0, gamma0, e) - 1.0}
               for e in (0.2, 0.1, 0.05, 0.025)]

    # 4. averaged-play dichotomy at the bilinear pole, vanishing step eta_t = c/sqrt(t)
    zst = (-b[1] / gamma0, b[0] / gamma0)                # limit of equilibrium as mu -> 0
    z = (zst[0] + 1.0, zst[1] + 1.0)
    d_init = math.hypot(1.0, 1.0)
    sx = sy = 0.0
    marks, dichotomy = (100, 20000), []
    for t in range(1, 20001):
        et = 0.5 / math.sqrt(t)
        f = game_operator(z, 0.0, gamma0, b)
        z = (z[0] - et * f[0], z[1] - et * f[1])
        sx += z[0]
        sy += z[1]
        if t in marks:
            dichotomy.append({"t": t,
                              "last_dist": math.hypot(z[0] - zst[0], z[1] - zst[1]),
                              "avg_dist": math.hypot(sx / t - zst[0], sy / t - zst[1])})

    return {"eta": eta, "steps": steps, "cells": cells, "identity_checks": identity_checks,
            "recurrence_scaling": scaling, "dichotomy": dichotomy, "d_init": d_init}


def main(argv=None) -> int:
    rep = run_experiment()
    eta = rep["eta"]
    print(f"research direction C5 — the last-iterate convergence/recurrence phase diagram of "
          f"vanilla OGD\n  on two-player quadratic games F(z) = (mu*I + gamma*S)z + b "
          f"(eta={eta}, {rep['steps']} steps):\n")
    print(f"  {'mu':>5} {'gamma':>6} {'rho (spectral)':>15} {'empirical rate':>15} {'phase':>10}")
    for c in rep["cells"]:
        print(f"  {c['mu']:>5.2f} {c['gamma']:>6.2f} {c['rho']:>15.4f} "
              f"{c['empirical_rate']:>15.4f} {c['phase']:>10}")
    print(f"\n  recurrence pole (mu=0): excess growth rho-1 vs eta "
          f"(quadratic vanishing => cycling in the continuous-time limit):")
    for s in rep["recurrence_scaling"]:
        print(f"    eta={s['eta']:<6} rho-1={s['excess']:.6f}")
    d = rep["dichotomy"]
    print(f"\n  averaged-play dichotomy at mu=0 (vanishing step): last iterate wanders, "
          f"average stays put:")
    for m in d:
        print(f"    t={m['t']:>6}  last-iterate dist={m['last_dist']:8.4f}   "
              f"averaged dist={m['avg_dist']:8.4f}")

    # invariants (CI gate; explicit raise so it holds under `python -O`)
    for c in rep["cells"]:
        # 1. the empirical asymptotic rate matches the closed-form spectral radius per cell
        if abs(c["empirical_rate"] - c["rho"]) > 0.02:
            raise SystemExit(f"empirical rate {c['empirical_rate']:.4f} != rho {c['rho']:.4f} "
                             f"at mu={c['mu']}, gamma={c['gamma']}")
        # 2. the phase behaviour matches the sign of rho - 1; near-boundary cells are gated
        #    exactly (the map is a scaled rotation, so dT/d0 = rho^steps up to fp noise)
        if c["phase"] == "converge" and not c["dT"] < 1e-2 * c["d0"]:
            raise SystemExit(f"rho<1 cell failed to converge at mu={c['mu']}, gamma={c['gamma']}")
        if c["phase"] == "diverge" and not c["dT"] > 1e1 * c["d0"]:
            raise SystemExit(f"rho>1 cell failed to diverge at mu={c['mu']}, gamma={c['gamma']}")
        if c["phase"] == "boundary":
            expected = c["rho"] ** rep["steps"]
            if not expected / 2.0 < c["dT"] / c["d0"] < expected * 2.0:
                raise SystemExit(f"near-boundary cell off its exact rho^T track at "
                                 f"mu={c['mu']}, gamma={c['gamma']}")
    # 3. the judge's Banach condition eta < 2*mu/L^2 is exactly rho < 1, and the claimed
    #    contraction modulus equals the spectral radius
    for ic in rep["identity_checks"]:
        if ic["rho_lt_1"] != ic["banach_cond"]:
            raise SystemExit("threshold identity rho<1 <=> eta < 2mu/L^2 violated")
        if ic["modulus_gap"] > 1e-12:
            raise SystemExit("claimed Banach modulus != spectral radius")
    # 4. the excess growth at the bilinear pole vanishes quadratically in eta (ratio ~4 per halving)
    sc = rep["recurrence_scaling"]
    for a, bb in zip(sc, sc[1:]):
        ratio = a["excess"] / bb["excess"]
        if not 3.0 < ratio < 5.0:
            raise SystemExit(f"recurrence-pole scaling not quadratic: excess ratio {ratio:.2f}")
    # 5. the dichotomy: last iterate grows from its early mark; the average stays bounded and
    #    ends far below the last iterate
    early, late = rep["dichotomy"]
    if not late["last_dist"] > 1.5 * early["last_dist"]:
        raise SystemExit("last iterate should wander away at the bilinear pole")
    if not (late["avg_dist"] < 1.5 * rep["d_init"] and late["avg_dist"] < 0.25 * late["last_dist"]):
        raise SystemExit("averaged play should stay bounded while the last iterate wanders")

    print(f"\n  confirmed: the empirical rate equals the spectral radius in every phase-plane "
          f"cell; the judge's\n  Banach condition eta < 2mu/L^2 is exactly rho < 1 (modulus = "
          f"spectral radius, gap < 1e-12); the\n  bilinear pole diverges at rate "
          f"sqrt(1+eta^2*gamma^2) with quadratically-vanishing excess (recurrence\n  in the "
          f"continuous-time limit); and averaged play stays bounded while the last iterate "
          f"wanders —\n  the spectral characterization research direction C5 proposed, confirmed "
          f"on its own proposed family.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

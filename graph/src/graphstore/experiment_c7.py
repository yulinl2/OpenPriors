"""Numerical experiment for research direction C7 (Epic AH): the fourth — and final open —
committed research direction carried to computation. Every direction the loop has produced is
now backed by numbers.

The fifth literature's conjecture *"a curvature bound makes the offline gradient-descent map a
no-regret play"* was judged **uncertain** (type-incorrect, but the same modulus drives both
theorems); the discovery loop refined it into direction C7, whose ``next_step`` proposes:
quadratics ``f_t(x) = 0.5*(x - c_t)' H (x - c_t)`` with ``H`` of condition number kappa, *three
regimes* — fixed ``c_t`` (offline pole), drifting ``c_t`` with controlled path length, and
adversarially alternating ``c_t`` — logging both cumulative regret and last-iterate error, to
verify the predicted ``log T / T`` vs geometric vs contraction-plus-drift rates and measure the
price of adversarial robustness.

This module **runs that experiment**, in pure Python (no numpy — the project doctrine), with
``H = diag(1, kappa)`` (so ``mu = 1``, ``L = kappa``) and projected OGD. What it confirms:

  * **offline pole, informed step** ``eta = 1/L``: the last iterate contracts geometrically at
    exactly ``1 - 1/kappa`` per step (measured; and to machine precision by ``T``);
  * **offline pole, adversarially-robust step** ``eta_t = min(1/L, 1/(mu*t))`` (the schedule
    that earns O(log T) strongly-convex regret): the last iterate decays only **polynomially**,
    with measured exponent ``-1`` — the *price of robustness*: at the same horizon the informed
    iterate sits at machine epsilon while the robust one is >= 1e-4, a super-geometric gap;
  * **adversarial regime**: cumulative regret of the same robust schedule grows like
    ``log T`` (the regret/log T ratio is stable across doubling horizons) — Hazan–Agarwal–Kale;
  * **drift regime**: with per-step drift ``delta``, the informed iterate *tracks* at a steady
    error equal to ``delta*(kappa - 1)`` (measured within 5%, and linear in ``delta``) — the
    contraction-plus-drift law, the interpolation C7's sharpened program describes.

The remaining frontier — a *parameter-free* algorithm sitting at both poles simultaneously,
with a matching lower bound — is the direction's open question and is deliberately NOT gated.
"""

from __future__ import annotations

import math


def _grad(x: tuple, c: tuple, kappa: float) -> tuple:
    """Gradient of f(x) = 0.5*(x-c)' diag(1, kappa) (x-c)."""
    return (x[0] - c[0], kappa * (x[1] - c[1]))


def _loss(x: tuple, c: tuple, kappa: float) -> float:
    return 0.5 * ((x[0] - c[0]) ** 2 + kappa * (x[1] - c[1]) ** 2)


def _proj(x: tuple, r: float) -> tuple:
    """Projection onto the box [-r, r]^2 (keeps the robust schedule stable at high kappa)."""
    return (max(-r, min(r, x[0])), max(-r, min(r, x[1])))


def _dist(a: tuple, b: tuple) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def run_regimes(kappa: float, horizon: int) -> dict:
    """Run the three C7 regimes for one condition number; everything is deterministic."""
    mu, L = 1.0, kappa
    x0, cstar = (2.0, 2.0), (0.3, -0.4)

    # A. offline pole — informed constant step vs the adversarially-robust capped schedule
    xc, xs = x0, x0
    dists_c, err_marks = [_dist(x0, cstar)], {}
    for t in range(1, horizon + 1):
        gc = _grad(xc, cstar, kappa)
        xc = _proj((xc[0] - gc[0] / L, xc[1] - gc[1] / L), 3.0)
        dists_c.append(_dist(xc, cstar))
        eta = min(1.0 / L, 1.0 / (mu * t))
        gs = _grad(xs, cstar, kappa)
        xs = _proj((xs[0] - eta * gs[0], xs[1] - eta * gs[1]), 3.0)
        if t in (horizon // 4, horizon):
            err_marks[t] = _dist(xs, cstar)
    # geometric rate over an adaptive early window (before underflow)
    a = 5
    b = a
    for t in range(a, min(400, horizon) + 1):
        if dists_c[t] > 1e-10:
            b = t
    emp_rate = (dists_c[b] / dists_c[a]) ** (1.0 / (b - a)) if b > a and dists_c[a] > 0 else 0.0
    quarter, full = horizon // 4, horizon
    poly_exponent = (math.log(err_marks[full] / err_marks[quarter]) / math.log(full / quarter)
                     if err_marks[quarter] > 0 else 0.0)

    # B. adversarial regime — alternating targets; regret vs the best fixed point (the origin)
    x, regret, regret_marks = x0, 0.0, {}
    for t in range(1, horizon + 1):
        c = (0.5, 0.5) if t % 2 else (-0.5, -0.5)
        regret += _loss(x, c, kappa) - _loss((0.0, 0.0), c, kappa)
        eta = min(1.0 / L, 1.0 / (mu * t))
        g = _grad(x, c, kappa)
        x = _proj((x[0] - eta * g[0], x[1] - eta * g[1]), 1.0)
        if t in (horizon // 8, horizon // 4, horizon // 2, horizon):
            regret_marks[t] = regret

    # C. drift regime — the minimizer moves delta per step; the informed iterate tracks it
    tracking = {}
    for delta in (0.001, 0.002):
        x, c = x0, (0.0, 0.0)
        tail = []
        for t in range(1, horizon + 1):
            c = (c[0] + delta, c[1] + delta)
            g = _grad(x, c, kappa)
            x = (x[0] - g[0] / L, x[1] - g[1] / L)
            if t > horizon // 2:
                tail.append(_dist(x, c))
        tracking[delta] = sum(tail) / len(tail)

    return {"kappa": kappa, "geometric_rate": emp_rate, "rate_window": (a, b),
            "informed_final_err": dists_c[-1], "robust_err_marks": err_marks,
            "poly_exponent": poly_exponent, "regret_marks": regret_marks,
            "tracking": tracking}


def run_experiment(horizon: int = 4000, kappas: tuple = (1.0, 10.0, 100.0)) -> dict:
    if horizon < 800 or horizon % 8:
        raise ValueError(f"horizon must be >= 800 and divisible by 8, got {horizon}")
    if any(k < 1.0 for k in kappas):
        raise ValueError(f"condition numbers must be >= 1 (mu = 1), got {kappas}")
    return {"horizon": horizon, "regimes": [run_regimes(k, horizon) for k in kappas]}


def main(argv=None) -> int:
    rep = run_experiment()
    T = rep["horizon"]
    print(f"research direction C7 — regret vs last-iterate on quadratics f_t(x) = "
          f"0.5*(x-c_t)' diag(1,kappa) (x-c_t)\n  three regimes (offline / adversarial / "
          f"drifting), horizon T={T}:\n")
    print(f"  {'kappa':>6} {'geom rate (1-1/k)':>18} {'robust exponent':>16} "
          f"{'informed err@T':>15} {'robust err@T':>13} {'track err/delta(k-1)':>21}")
    for r in rep["regimes"]:
        k = r["kappa"]
        pred = 1.0 - 1.0 / k
        track_ratio = (r["tracking"][0.001] / (0.001 * (k - 1))) if k > 1 else float("nan")
        print(f"  {k:>6.0f} {r['geometric_rate']:>8.4f} ({pred:.4f}) {r['poly_exponent']:>16.2f} "
              f"{r['informed_final_err']:>15.1e} {r['robust_err_marks'][T]:>13.2e} "
              f"{track_ratio:>21.3f}")
        marks = sorted(r["regret_marks"])
        ratios = " ".join(f"t={t}:{r['regret_marks'][t] / math.log(t):.2f}" for t in marks)
        print(f"         adversarial regret/log t: {ratios}")

    # invariants (CI gate; explicit raise so it holds under `python -O`)
    for r in rep["regimes"]:
        k = r["kappa"]
        # 1. informed constant step converges geometrically at 1 - 1/kappa (to machine eps by T)
        if r["informed_final_err"] > 1e-10:
            raise SystemExit(f"informed iterate should reach machine precision at kappa={k}")
        if k > 1 and abs(r["geometric_rate"] - (1.0 - 1.0 / k)) > 0.02:
            raise SystemExit(f"geometric rate {r['geometric_rate']:.4f} != 1-1/kappa at kappa={k}")
        # 2 & 3. for kappa > 1 the robust (regret-optimal) schedule decays only polynomially
        # (exponent -1) — a super-geometric price of robustness at the same horizon. At
        # kappa = 1 the robust schedule's first step IS the informed step (eta = 1/L = 1/mu
        # jumps exactly to the optimum), so the price vanishes: it grows with conditioning.
        if k > 1:
            if abs(r["poly_exponent"] + 1.0) > 0.15:
                raise SystemExit(f"robust-schedule exponent {r['poly_exponent']:.2f} != -1 "
                                 f"at kappa={k}")
            if not r["robust_err_marks"][T] > 1e-4:
                raise SystemExit(f"robust schedule should still be far from the optimum "
                                 f"at kappa={k}")
        elif r["robust_err_marks"][T] > 1e-10:
            raise SystemExit("at kappa=1 the robust schedule should pay no price at all")
        # 4. adversarial regret grows like log T (stable regret/log t across doubling horizons)
        marks = sorted(r["regret_marks"])
        vals = [r["regret_marks"][t] / math.log(t) for t in marks]
        for u, v in zip(vals, vals[1:]):
            if not 0.8 < v / u < 1.1:
                raise SystemExit(f"regret/log t not stable at kappa={k}: {vals}")
        # 5. drift tracking follows the contraction-plus-drift law: err = delta*(kappa-1),
        #    linear in delta
        if k > 1:
            for delta, err in r["tracking"].items():
                if abs(err - delta * (k - 1)) > 0.05 * delta * (k - 1):
                    raise SystemExit(f"tracking error off the delta*(kappa-1) law at kappa={k}")
            lin = r["tracking"][0.002] / r["tracking"][0.001]
            if not 1.9 < lin < 2.1:
                raise SystemExit(f"tracking error not linear in delta at kappa={k}")
        else:
            if max(r["tracking"].values()) > 1e-6:
                raise SystemExit("at kappa=1 the informed step tracks exactly (one-step jump)")

    print(f"\n  confirmed: the same curvature modulus drives both theorems, through a lossy "
          f"bridge — the informed\n  step contracts geometrically at exactly 1-1/kappa while the "
          f"regret-optimal schedule (which earns\n  stable regret/log T) decays only "
          f"polynomially (exponent -1), a super-geometric price of robustness;\n  and under "
          f"drift the informed iterate tracks at exactly delta*(kappa-1) — the "
          f"contraction-plus-drift\n  interpolation research direction C7 proposed.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

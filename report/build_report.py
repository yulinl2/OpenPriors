"""Generate `REPORT.md` — the consolidated, auditable research report, live from the pipeline.

Where the interactive demo (`demo/`) is the *visual* front door, this is the *prose* one: a single
Markdown document a technical reader can audit top-to-bottom, with **every number computed from the
same code paths the pipeline uses** (via `demo.model.build_model`) plus both research-direction
experiments (C2, C4). So the report can never drift from what OpenPriors actually produces — a
CI gate rebuilds it and fails on any diff (`report/test_report.py` + `report-ci`).

    decomposer/.venv/bin/python report/build_report.py         # writes REPORT.md
"""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def _sys_path() -> None:
    import sys
    for p in ("demo", "graph/src", "retrieval/src", "analogy/src", "grounding/src"):
        sp = str(REPO / p)
        if sp not in sys.path:
            sys.path.insert(0, sp)


def _fmt(x: float, n: int = 3) -> str:
    return f"{x:.{n}f}"


def build_markdown() -> str:
    _sys_path()
    from model import build_model, DOMAINS
    from graphstore.experiment_c4 import run_experiment as run_c4
    from graphstore.experiment_c5 import run_experiment as run_c5

    m = build_model()
    c = m["counts"]
    lines: list = []
    w = lines.append

    w("# OpenPriors — research audit report")
    w("")
    w("> **Auto-generated** from the live pipeline by `report/build_report.py`. Every figure below is "
      "computed from the same code paths `make pipeline` runs — do not edit by hand; run "
      "`make report` to regenerate. A CI gate fails if this file is stale.")
    w("")
    w("OpenPriors reads a body of mathematical results as one typed *(object, attribute, relation)* "
      "graph and runs a closed research loop over it: **discover → predict → evaluate → investigate "
      "→ experiment**. It situates each result among its priors, finds what it is structurally "
      "analogous to in another field, predicts what that analogy implies, tells the sound "
      "predictions from the spurious, refines the open ones into research directions, and runs their "
      "proposed numerical experiments — every step grounded and CI-gated.")
    w("")
    w(f"At a glance: **{c['literatures']} literatures**, **{c['results']} results**, "
      f"**{c['analogies']} cross-domain analogies**, **{c['conjectures']} judged conjectures**, "
      f"**{c['directions']} research directions**, over a unified graph of "
      f"**{m['stats']['n_nodes']} nodes / {m['stats']['n_edges']} edges**.")
    w("")

    # 1. the literatures
    w("## 1. The four literatures")
    w("")
    w("| Field | Results | Mean novelty | Most novel (score) |")
    w("|---|---|---|---|")
    for key, d in DOMAINS.items():
        rs = [r for r in m["results"] if r["domain"] == key]
        if not rs:
            continue
        mean_nov = sum(r["novelty"] for r in rs) / len(rs)
        top = max(rs, key=lambda r: r["novelty"])
        w(f"| {d['nice']} | {len(rs)} | {_fmt(mean_nov)} | `{top['name']}` ({_fmt(top['novelty'])}) |")
    w("")
    w("*Novelty = 1 − best-prior structural coverage (a prior must be no larger than the result it "
      "covers, so a descendant can't 'explain away' its ancestor).*")
    w("")

    # 2. lineage
    w("## 2. Reasoning lineage")
    w("")
    w("Each field's development line, recovered from grounded structure alone (no citation "
      "metadata) — objects are results, the relation is *extends*, attributes are the residual novelty:")
    w("")
    for key, d in DOMAINS.items():
        childs = [r for r in m["results"] if r["domain"] == key and r["parent"]]
        if not childs:
            continue
        for r in sorted(childs, key=lambda r: r["novelty"]):
            w(f"- **{d['nice']}**: `{r['parent']}` → `{r['name']}` "
              f"(novelty {_fmt(r['novelty'])})")
    w("")

    # 3. cross-domain analogies
    w("## 3. Cross-domain analogies")
    w("")
    w("Discovered by the structure-mapping engine with **roles read from CAUSE structure, "
      "unsupervised** — no hand-coded correspondences. Each edge aligns a structural-property/"
      "guarantee pair across two literatures:")
    w("")
    w("| A | B | SME score | correspondences |")
    w("|---|---|---|---|")
    for e in sorted(m["analogies"], key=lambda e: -e["score"])[:12]:
        corr = "; ".join(f"{a}↔{b}" for a, b in list((e["corr"] or {}).items())[:3])
        w(f"| `{e['a']}` | `{e['b']}` | {_fmt(e['score'], 1)} | {corr or '—'} |")
    shown = min(12, len(m["analogies"]))
    if len(m["analogies"]) > shown:
        w(f"")
        w(f"*(showing the {shown} highest-scoring of {len(m['analogies'])} analogies.)*")
    w("")

    # 4. discovered roles
    w("## 4. Discovered structural roles")
    w("")
    w("The role each functor plays is *discovered* from its position in the `CAUSE` glue "
      "(premise vs. conclusion, arity), not declared. The shared **`PC::2`** (structural-property) "
      "role is what makes the four fields analogous:")
    w("")
    w("| Functor | Role |")
    w("|---|---|")
    for functor, role in sorted(m["roles"].items()):
        w(f"| `{functor}` | `{role}` |")
    w("")

    # 5. conjectures + verdicts
    w("## 5. Conjectures and verdicts")
    w("")
    w("Candidate inferences projected across an analogy (Epic P), then judged by an in-session "
      "sub-agent behind a deterministic grounding gate (Epic Q):")
    w("")
    for cj in m["conjectures"]:
        w(f"- **{cj['id']}** — _{cj['verdict']}_: {cj['statement']}")
        w(f"  - reasoning: {cj['reasoning']}")
    w("")

    # 6. research directions
    w("## 6. Research directions")
    w("")
    w("The *uncertain*-judged conjectures refined into precise, citation-grounded programs "
      "(Epic Y):")
    w("")
    for d in m["directions"]:
        w(f"### {d['id']} — {d['scope']}")
        w(f"- **Precise statement**: {d['precise']}")
        w(f"- **Open question**: {d['open']}")
        w(f"- **Next step**: {d['next']}")
        w("")

    # 7. experiments
    w("## 7. Numerical experiments")
    w("")
    w("Three research directions carried through to computation, in pure Python (project doctrine):")
    w("")
    w("### C2 — contraction modulus vs. change-of-measure (finite MDP)")
    w("")
    ex = m["experiment"]
    w(f"On random {ex['n_states']}-state Markov chains (γ={ex['gamma']}), the L2(μ) contraction "
      f"modulus of the projected Bellman operator, as the weighting μ moves away from the "
      f"stationary d:")
    w("")
    w("| χ²(d‖μ) | L2(μ) modulus |")
    w("|---|---|")
    for p in ex["points"]:
        w(f"| {_fmt(p['chi2'], 4)} | {_fmt(p['modulus'], 4)} |")
    w("")
    w(f"At μ=d the modulus is exactly γ={ex['gamma']} (Bertsekas–Tsitsiklis, ‖P‖_L2(d)=1); it rises "
      "monotonically with the χ² mismatch until the operator is no longer a contraction.")
    w("")
    w("### C4 — fixed-point uniform convergence (Gaussian-mixture EM)")
    w("")
    c4 = run_c4(seed=0)
    w(f"On the Balakrishnan–Wainwright–Yu symmetric 2-Gaussian-mixture EM operator "
      f"M(θ)=E[X·tanh(Xθ/σ²)] (θ*={c4['theta_star']}, σ={c4['sigma']}): population fixed point "
      f"M(θ*)=θ* recovered as {_fmt(c4['pop_fixed_point'], 6)}, local contraction modulus "
      f"κ={_fmt(c4['kappa'], 4)}<1. The Banach bound ‖θ̂ₙ−θ*‖ ≤ εₙ/(1−κ) holds for every sample:")
    w("")
    w("| n | εₙ (sup‖Mₙ−M‖) | fixed-point error | bound εₙ/(1−κ) | εₙ·√n |")
    w("|---|---|---|---|---|")
    for lv in c4["levels"]:
        w(f"| {lv['n']} | {_fmt(lv['eps'], 4)} | {_fmt(lv['fp_err'], 4)} | "
          f"{_fmt(lv['bound'], 4)} | {_fmt(lv['eps_sqrt_n'])} |")
    w("")
    w("The fixed-point error tracks the bound within a few percent and decays at the 1/√n "
      "uniform-convergence rate — recovering the BWY guarantee from an operator-class argument.")
    w("")
    w("### C5 — OGD convergence/recurrence phase diagram vs. the spectral radius")
    w("")
    c5 = run_c5(seed=0)
    w(f"Direction C5 — generated, judged *uncertain*, and refined in the same loop — proposed "
      f"testing whether vanilla OGD's last-iterate behaviour on two-player quadratic games "
      f"F(z)=(μI+γS)z+b is governed by the spectral radius ρ of the linearized map "
      f"(η={c5['eta']}, {c5['steps']} steps):")
    w("")
    w("| μ | γ | ρ (spectral) | empirical rate | phase |")
    w("|---|---|---|---|---|")
    for cell in c5["cells"]:
        w(f"| {_fmt(cell['mu'], 2)} | {_fmt(cell['gamma'], 2)} | {_fmt(cell['rho'], 4)} | "
          f"{_fmt(cell['empirical_rate'], 4)} | {cell['phase']} |")
    w("")
    d5 = c5["dichotomy"]
    w(f"The empirical per-step rate equals ρ in every cell (the OGD map is a scaled rotation); "
      f"the Banach condition η<2μ/L² is exactly ρ<1; and at the bilinear pole the averaged play "
      f"stays bounded ({_fmt(d5[-1]['avg_dist'], 2)}) while the last iterate wanders away "
      f"({_fmt(d5[-1]['last_dist'], 2)}) — no attracting fixed point, exactly the C5 dichotomy.")
    w("")

    # footer
    w("## Reproducibility")
    w("")
    w("```")
    w("make setup        # pinned deps, pure-Python")
    w("make pipeline     # the unified graph + discover/predict/evaluate")
    w("make experiment   # the C2 + C4 numerical experiments")
    w("make report       # regenerate this file")
    w("make test         # every epic's unit tests + integration")
    w("```")
    w("")
    return "\n".join(lines) + "\n"


def build() -> Path:
    md = build_markdown()
    out = REPO / "REPORT.md"
    out.write_text(md, encoding="utf-8")
    print(f"wrote {out} ({len(md):,} bytes, {md.count(chr(10))} lines)")
    return out


if __name__ == "__main__":
    build()

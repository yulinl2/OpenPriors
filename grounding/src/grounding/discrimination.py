"""Discrimination control: a novelty detector must DISCRIMINATE, not just confirm.

The Banach case study showed *low* novelty for a true instance (problem_07 Q1 IS Banach).
This control aligns the SAME Banach base against two targets:
  * Q1 (contraction/fixed-point)         -> should be LOW novelty (an instance), and
  * Q2 (M-estimator asymptotic normality) -> should be HIGH novelty (a different theorem),
proving the detector is not vacuous (it does not label everything an "instance"). The wide
novelty margin between the two is the discrimination signal.
"""

from __future__ import annotations

import json
from pathlib import Path

from analogy.align import align
from analogy.novelty import novelty_report
from analogy.predicates import Dgroup

from .casestudy import _verdict
from .load import expr_from_json
from .verify import check_section


def _dgroup(section: dict, name: str) -> Dgroup:
    return Dgroup(name, [expr_from_json(f) for f in section["facts"]])


def run_discrimination(banach_path: str | Path, q2_path: str | Path) -> dict:
    banach = json.loads(Path(banach_path).read_text(encoding="utf-8"))
    q2doc = json.loads(Path(q2_path).read_text(encoding="utf-8"))

    base = _dgroup(banach["base"], "banach")
    targets = [
        ("q1_contraction", _dgroup(banach["target"], "q1"), banach["target"]),
        ("q2_asymptotic_normality", _dgroup(q2doc["target"], "q2"), q2doc["target"]),
    ]

    results = {}
    for name, tdg, traw in targets:
        g = align(base, tdg)
        rep = novelty_report(base, tdg, g)
        results[name] = {
            "grounding_passed": check_section(traw)["passed"],
            "mapping_size": len(g.correspondences),
            "structural_score": g.score,
            "target_coverage": rep["target_coverage"],
            "novelty_score": rep["novelty_score"],
            "verdict": _verdict(rep["novelty_score"]),
        }

    n1 = results["q1_contraction"]["novelty_score"]
    n2 = results["q2_asymptotic_normality"]["novelty_score"]
    return {
        "results": results,
        "novelty_margin": round(n2 - n1, 4),
        "discriminates": n1 <= 0.15 and n2 >= 0.6,
    }


def main(argv=None) -> int:
    here = Path(__file__).resolve().parents[2]
    rep = run_discrimination(here / "dgroups" / "banach_case.json",
                             here / "dgroups" / "q2_target.json")
    out = here / "results"; out.mkdir(parents=True, exist_ok=True)
    (out / "discrimination.json").write_text(
        json.dumps(rep, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, r in rep["results"].items():
        print(f"banach vs {name:26} novelty={r['novelty_score']:.2f} "
              f"coverage={r['target_coverage']:.2f}  {r['verdict']}")
    print(f"novelty margin (distinct - instance) = {rep['novelty_margin']}; "
          f"discriminates = {rep['discriminates']}")
    return 0 if rep["discriminates"] else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

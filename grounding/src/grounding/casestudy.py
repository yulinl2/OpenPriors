"""Real-content case study: is problem_07 Q1 an instance of Banach's theorem?

Runs the full novelty detector on two grounded dgroups (abstract Banach theorem vs the
exam problem's Q1 contraction argument). Expected: near-complete structural coverage =>
low novelty (problem_07 Q1 is "known machinery on a relabeled map"), with the one
unmatched target fact — the explicit iteration-complexity bound — flagged as the genuinely
novel addition. This is the "shortcut under fancy disguise" detection the project exists for.
"""

from __future__ import annotations

import json
from pathlib import Path

from analogy.align import align, fmt_expr
from analogy.novelty import novelty_report
from analogy.predicates import Dgroup

from .load import expr_from_json
from .verify import check_section


def load_case(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    base = Dgroup(data["base"]["name"], [expr_from_json(f) for f in data["base"]["facts"]])
    target = Dgroup(data["target"]["name"], [expr_from_json(f) for f in data["target"]["facts"]])
    return {"base": base, "target": target, "raw": data}


def run_case(path: str | Path) -> dict:
    case = load_case(path)
    base, target, raw = case["base"], case["target"], case["raw"]

    grounding = {
        "base": check_section(raw["base"]),
        "target": check_section(raw["target"]),
    }
    grounding["all_passed"] = grounding["base"]["passed"] and grounding["target"]["passed"]

    g = align(base, target)
    rep = novelty_report(base, target, g)
    matched_t = {repr(e) for e in g.matched_target}
    novel_target_facts = [fmt_expr(f) for f in target.facts if repr(f) not in matched_t]

    return {
        "base": base.name,
        "target": target.name,
        "grounding_all_passed": grounding["all_passed"],
        "mapping": g.correspondences,
        "structural_score": g.score,
        "target_coverage": rep["target_coverage"],
        "novelty_score": rep["novelty_score"],
        "shortcut_signal": rep["shortcut_signal"],
        "novel_target_facts": novel_target_facts,
        "candidate_inferences": [ci["projection"] for ci in g.candidate_inferences],
        "verdict": _verdict(rep["novelty_score"]),
    }


def _verdict(novelty: float) -> str:
    if novelty <= 0.15:
        return "INSTANCE of the base theorem (known machinery on relabeled objects) — low novelty"
    if novelty <= 0.5:
        return "partial reuse of the base structure — moderate novelty"
    return "structurally distinct — high novelty"


def main(argv=None) -> int:
    here = Path(__file__).resolve().parents[2]
    path = (argv[0] if argv else None) or str(here / "dgroups" / "banach_case.json")
    out_dir = here / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    rep = run_case(path)
    (out_dir / "banach_case.json").write_text(
        json.dumps(rep, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"BASE   {rep['base']}")
    print(f"TARGET {rep['target']}")
    print(f"grounding_passed={rep['grounding_all_passed']}  mapping={rep['mapping']}")
    print(f"coverage={rep['target_coverage']}  novelty={rep['novelty_score']}  "
          f"score={rep['structural_score']}")
    print(f"novel (unmatched target) facts: {rep['novel_target_facts']}")
    print(f"VERDICT: {rep['verdict']}")
    return 0 if rep["grounding_all_passed"] else 1


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))

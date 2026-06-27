"""CLI: retrieve the nearest known prior for each problem_07 question against the library."""

from __future__ import annotations

import json
from pathlib import Path

from analogy.predicates import Dgroup

from .engine import expr_from_json, load_library, retrieve


def _target_from(path: Path, name: str) -> Dgroup:
    data = json.loads(path.read_text(encoding="utf-8"))
    sect = data["target"]
    return Dgroup(name, [expr_from_json(f) for f in sect["facts"]])


def main(argv=None) -> int:
    here = Path(__file__).resolve().parents[2]
    repo = here.parent
    library = load_library(here / "library" / "theorems.json")
    gdir = repo / "grounding" / "dgroups"
    targets = {
        "problem_07-Q1": _target_from(gdir / "banach_case.json", "problem_07-Q1"),
        "problem_07-Q2": _target_from(gdir / "q2_target.json", "problem_07-Q2"),
    }
    out = here / "results"; out.mkdir(parents=True, exist_ok=True)
    report = {}
    for tname, tdg in targets.items():
        r = retrieve(tdg, library)
        report[tname] = r
        mac_top = f"{r['mac_ranking'][0][0]} ({r['mac_ranking'][0][1]})" if r["mac_ranking"] else "—"
        nov = f"{r['nearest_novelty']:.2f}" if r["nearest_novelty"] is not None else "n/a"
        print(f"[{tname}] MAC top: {mac_top}  -> nearest prior = {r['nearest_prior']} "
              f"(novelty {nov}) :: {r['verdict']}")
    (out / "retrieval.json").write_text(
        json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

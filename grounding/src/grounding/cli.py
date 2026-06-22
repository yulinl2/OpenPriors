"""CLI: ground-check the prose dgroups and solve all four riddles by structure mapping."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import load, verify
from .solve import solve


def _canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=2)


def main(argv=None) -> int:
    here = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(prog="grounding", description=__doc__)
    ap.add_argument("--dgroups", default=str(here / "dgroups" / "riddles.json"))
    ap.add_argument("--out", default=str(here / "results"))
    args = ap.parse_args(argv)

    riddles = load.load_riddles(args.dgroups)
    raw = {k: v["raw"] for k, v in riddles.items()}
    grounding = verify.check_riddles(raw)

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    (out / "grounding.json").write_text(_canon(grounding) + "\n", encoding="utf-8")

    solutions = {}
    for key, r in riddles.items():
        sol = solve(r["source"], r["target"], r["raw"])
        solutions[key] = sol
        print(f"[{key}] relation={sol['blank_defining_relation']:7} "
              f"maps_answer->blank={sol['answer_maps_to_blank']}  "
              f"=> {sol['structural_answer']}  ({sol['numeric_answer']})")
    (out / "solutions.json").write_text(_canon(solutions) + "\n", encoding="utf-8")

    ok = grounding["all_passed"] and all(s["answer_maps_to_blank"] for s in solutions.values())
    print(f"grounding all_passed={grounding['all_passed']}; "
          f"distinct answers => {sorted({s['numeric_answer'] for s in solutions.values()})}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

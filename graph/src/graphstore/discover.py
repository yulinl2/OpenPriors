"""Discovery loop (Epic Y): turn the OPEN conjectures into precise research directions.

Epic Q judged each analogical conjecture plausible / uncertain / implausible. The *uncertain*
ones are the interesting residue — neither clearly known nor clearly false, i.e. genuinely
open. This stage sharpens them: an **in-session Claude Code sub-agent** (no API call) refines
each uncertain conjecture into a precise research direction — a sharpened statement, what's
established, the open question, and one concrete next step — committed as
``graph/evaluations/research_directions.json``.

This module is the **deterministic gate** over that artifact (no model call), the same
discipline ``grounding.verify`` and ``graphstore.evaluate`` apply. It checks the artifact is
well-formed AND that every research direction is anchored to a real conjecture the evaluation
stage judged ``uncertain`` — so a direction can't be invented for a conjecture the system
never flagged as open. It closes the loop discover -> predict -> evaluate -> **investigate**.
"""

from __future__ import annotations

import json
from pathlib import Path

SCOPE_VERDICTS = {"promising", "narrow", "ill_posed"}
REQUIRED_FIELDS = ("precise_statement", "whats_established", "open_question", "next_step")


def _uncertain_ids(repo: Path) -> set:
    data = json.loads(
        (repo / "graph" / "evaluations" / "conjecture_evaluations.json").read_text())
    return {e["id"] for e in data.get("evaluations", []) if e.get("verdict") == "uncertain"}


def verify(repo: Path) -> dict:
    art = repo / "graph" / "evaluations" / "research_directions.json"

    def _fail(problem: str) -> dict:
        return {"n_directions": 0, "anchored_ok": [], "scope_distribution": {},
                "problems": [problem], "passed": False}

    try:
        data = json.loads(art.read_text())
    except (OSError, json.JSONDecodeError) as ex:
        return _fail(f"cannot read/parse research_directions artifact: {ex}")
    directions = data.get("directions")
    if not isinstance(directions, list):
        return _fail("artifact has no 'directions' list")

    open_ids = _uncertain_ids(repo)
    problems, checked = [], []
    for d in directions:
        did = d.get("id", "?")
        # 1. anchoring: the direction must refine a conjecture the evaluation flagged uncertain
        if did not in open_ids:
            problems.append(f"{did}: not an 'uncertain'-judged conjecture {sorted(open_ids)}")
        # 2. schema
        for f in REQUIRED_FIELDS:
            if not str(d.get(f, "")).strip():
                problems.append(f"{did}: empty {f}")
        if d.get("scope_verdict") not in SCOPE_VERDICTS:
            problems.append(f"{did}: scope_verdict {d.get('scope_verdict')!r} not in {sorted(SCOPE_VERDICTS)}")
        if did in open_ids and all(str(d.get(f, "")).strip() for f in REQUIRED_FIELDS) \
                and d.get("scope_verdict") in SCOPE_VERDICTS:
            checked.append(did)

    dist: dict[str, int] = {}
    for d in directions:
        dist[d.get("scope_verdict", "?")] = dist.get(d.get("scope_verdict", "?"), 0) + 1
    return {
        "n_directions": len(directions),
        "anchored_ok": checked,
        "scope_distribution": dist,
        "problems": problems,
        "passed": not problems and len(checked) == len(directions) and len(directions) > 0,
    }


def main(argv=None) -> int:
    here = Path(__file__).resolve().parents[2]
    repo = here.parent
    rep = verify(repo)
    data = json.loads(
        (repo / "graph" / "evaluations" / "research_directions.json").read_text())

    print(f"discovery loop: {rep['n_directions']} open conjectures refined into research "
          f"directions by an in-session sub-agent")
    print(f"  scope: {rep['scope_distribution']}")
    print(f"  all anchored to 'uncertain'-judged conjectures: "
          f"{len(rep['anchored_ok'])}/{rep['n_directions']}")
    for d in data["directions"]:
        print(f"\n  [{d['scope_verdict']:9s}] {d['id']}: {d['precise_statement']}")
        print(f"      open: {d['open_question']}")
        print(f"      next: {d['next_step']}")

    if not rep["passed"]:
        raise SystemExit(f"discovery gate failed: {rep['problems']}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

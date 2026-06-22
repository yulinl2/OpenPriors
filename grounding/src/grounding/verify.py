"""Deterministic grounding check — the gate on the sub-agent's NL extraction.

Doctrine (decomposer/docs/principles.md): an LLM/sub-agent does the irreducible NL work, but its
output is admitted only if a *deterministic* check passes. Here: every symbol the extractor
introduced must be **grounded** in a verbatim substring of the source prose, and every entity
used in a fact must be grounded. This catches hallucinated symbols without trusting the LLM.
"""

from __future__ import annotations

from .load import entities_in_facts


def check_section(section: dict) -> dict:
    text = section["text"]
    groundings = section.get("groundings", {})
    facts = section["facts"]

    # 1. every grounding value is a NON-EMPTY verbatim substring of the source text
    #    (an empty/whitespace grounding would trivially pass `"" in text`, a loophole).
    bad_substrings = sorted(s for s, sub in groundings.items()
                            if not sub.strip() or sub not in text)
    # 2. every entity used in the facts is grounded
    used = entities_in_facts(facts)
    ungrounded = sorted(e for e in used if e not in groundings)

    passed = not bad_substrings and not ungrounded
    return {
        "passed": passed,
        "n_entities": len(used),
        "n_grounded": len(groundings),
        "ungrounded_entities": ungrounded,
        "non_verbatim_groundings": bad_substrings,
    }


def check_riddles(raw_by_key: dict) -> dict:
    report = {}
    for key, r in raw_by_key.items():
        if key.startswith("_"):
            continue
        s = check_section(r["source"])
        t = check_section(r["target"])
        report[key] = {"source": s, "target": t, "passed": s["passed"] and t["passed"]}
    report["all_passed"] = all(v["passed"] for k, v in report.items() if not k.startswith("_") and k != "all_passed")
    return report

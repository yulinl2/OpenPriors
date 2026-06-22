"""Tests for the prose->dgroup front end: deterministic grounding gate + structural solve."""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(REPO / "analogy" / "src"))

from grounding import load, verify
from grounding.solve import solve

DGROUPS = ROOT / "dgroups" / "riddles.json"


def _riddles():
    return load.load_riddles(DGROUPS)


def test_entities_exclude_functors():
    facts = [["DIVIDES", "total", "count", "each"], ["CAUSE", ["SAME", "x"], "each"]]
    ents = load.entities_in_facts(facts)
    assert ents == {"total", "count", "each", "x"}
    assert "DIVIDES" not in ents and "CAUSE" not in ents and "SAME" not in ents


def test_grounding_passes_for_all_riddles():
    raw = {k: v["raw"] for k, v in _riddles().items()}
    rep = verify.check_riddles(raw)
    assert rep["all_passed"], rep


def test_grounding_fails_on_hallucinated_symbol():
    section = {
        "text": "3 people, total of 3 hours.",
        "groundings": {"a": "3 people", "ghost": "elephants in space"},  # not in text
        "facts": [["TOTAL", "a"]],
    }
    r = verify.check_section(section)
    assert not r["passed"] and "ghost" in r["non_verbatim_groundings"]


def test_grounding_fails_on_empty_grounding():
    # an empty/whitespace grounding must NOT pass via `"" in text`
    section = {"text": "3 people.", "groundings": {"x": "  "}, "facts": [["TOTAL", "x"]]}
    r = verify.check_section(section)
    assert not r["passed"] and "x" in r["non_verbatim_groundings"]


def test_grounding_fails_on_ungrounded_entity():
    section = {"text": "3 people.", "groundings": {}, "facts": [["TOTAL", "x"]]}
    r = verify.check_section(section)
    assert not r["passed"] and "x" in r["ungrounded_entities"]


def test_solve_divides_vs_equals_gives_different_answers():
    riddles = _riddles()
    sol = {k: solve(v["source"], v["target"], v["raw"]) for k, v in riddles.items()}
    assert sol["riddle_1"]["blank_defining_relation"] == "DIVIDES"
    assert sol["riddle_1"]["numeric_answer"] == "1 hour"   # singularized at value 1
    assert sol["riddle_3"]["blank_defining_relation"] == "EQUALS"
    assert sol["riddle_3"]["numeric_answer"] == "3 hours"
    # the structural crux: near-identical surface -> two distinct answers
    assert {s["numeric_answer"] for s in sol.values()} == {"1 hour", "3 hours"}


def test_answer_maps_to_blank_via_alignment():
    for k, v in _riddles().items():
        sol = solve(v["source"], v["target"], v["raw"])
        assert sol["answer_maps_to_blank"], k  # SME maps the known answer onto the blank

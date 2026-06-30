"""Discovery loop (Epic Y): the deterministic gate over the sub-agent's research directions.

Each open (uncertain-judged) conjecture is refined in-session into a research direction; this
gate (no model call) checks the artifact is well-formed and anchored to a real uncertain
conjecture. Like the other gates, it is unit-tested to FAIL on broken input.
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(REPO / "analogy" / "src"))
sys.path.insert(0, str(REPO / "retrieval" / "src"))
sys.path.insert(0, str(REPO / "grounding" / "src"))

from graphstore.discover import REQUIRED_FIELDS, SCOPE_VERDICTS, _uncertain_ids, verify

ART = REPO / "graph" / "evaluations" / "research_directions.json"


def test_committed_directions_pass_the_gate():
    rep = verify(REPO)
    assert rep["passed"], rep["problems"]
    assert rep["n_directions"] == len(rep["anchored_ok"]) and rep["n_directions"] > 0


def test_every_direction_refines_an_uncertain_conjecture():
    data = json.loads(ART.read_text())
    open_ids = _uncertain_ids(REPO)
    assert open_ids  # there are genuinely-open conjectures to refine
    for d in data["directions"]:
        assert d["id"] in open_ids
        assert d["scope_verdict"] in SCOPE_VERDICTS
        for f in REQUIRED_FIELDS:
            assert str(d[f]).strip()


def _verify_mutated(mutate):
    data = json.loads(ART.read_text())
    mutate(data)
    import graphstore.discover as dv
    orig = pathlib.Path.read_text

    def fake(self, *a, **k):
        return json.dumps(data) if self == ART else orig(self, *a, **k)

    pathlib.Path.read_text = fake
    try:
        return dv.verify(REPO)
    finally:
        pathlib.Path.read_text = orig


def test_gate_fails_on_unanchored_direction():
    rep = _verify_mutated(lambda d: d["directions"][0].__setitem__("id", "C999"))
    assert not rep["passed"] and any("uncertain" in p for p in rep["problems"])


def test_gate_fails_on_empty_field():
    rep = _verify_mutated(lambda d: d["directions"][0].__setitem__("next_step", "  "))
    assert not rep["passed"] and any("next_step" in p for p in rep["problems"])


def test_gate_fails_on_bad_scope_verdict():
    rep = _verify_mutated(lambda d: d["directions"][0].__setitem__("scope_verdict", "great"))
    assert not rep["passed"]


def test_gate_reports_malformed_artifact_without_crashing():
    import graphstore.discover as dv
    orig = pathlib.Path.read_text

    def fake(self, *a, **k):
        return "{ not json" if self == ART else orig(self, *a, **k)

    pathlib.Path.read_text = fake
    try:
        rep = dv.verify(REPO)
    finally:
        pathlib.Path.read_text = orig
    assert not rep["passed"] and rep["problems"]

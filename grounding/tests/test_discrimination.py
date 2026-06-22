"""Discrimination control: the detector must separate an instance from a distinct theorem."""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "analogy" / "src"))

from grounding.discrimination import run_discrimination

BANACH = ROOT / "dgroups" / "banach_case.json"
Q2 = ROOT / "dgroups" / "q2_target.json"


def _rep():
    return run_discrimination(BANACH, Q2)


def test_both_targets_are_grounded():
    r = _rep()["results"]
    assert r["q1_contraction"]["grounding_passed"]
    assert r["q2_asymptotic_normality"]["grounding_passed"]


def test_instance_is_low_novelty():
    assert _rep()["results"]["q1_contraction"]["novelty_score"] <= 0.15


def test_distinct_theorem_is_high_novelty():
    # Q2 (asymptotic normality) shares no structure with Banach -> high novelty
    assert _rep()["results"]["q2_asymptotic_normality"]["novelty_score"] >= 0.6


def test_detector_discriminates_with_wide_margin():
    rep = _rep()
    assert rep["discriminates"] is True
    assert rep["novelty_margin"] >= 0.5  # not vacuous: clear separation

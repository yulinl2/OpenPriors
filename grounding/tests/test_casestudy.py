"""The Banach case study: the novelty detector on real mathematics (problem_07 Q1)."""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "analogy" / "src"))

from grounding.casestudy import run_case

CASE = ROOT / "dgroups" / "banach_case.json"


def test_grounding_passes_for_real_math():
    assert run_case(CASE)["grounding_all_passed"]


def test_problem07_q1_detected_as_instance_of_banach():
    rep = run_case(CASE)
    # near-complete structural coverage => low novelty => "known machinery on relabeled map"
    assert rep["target_coverage"] >= 0.85
    assert rep["novelty_score"] <= 0.15
    assert rep["verdict"].startswith("INSTANCE")


def test_mapping_relabels_the_theorem():
    m = run_case(CASE)["mapping"]
    assert m["x_star"] == "theta_star" and m["k"] == "kappa"
    assert m["the_map"] == "the_map"  # T is T in both (renaming-invariant alignment)


def test_only_novel_part_is_the_iteration_bound():
    novel = run_case(CASE)["novel_target_facts"]
    assert len(novel) == 1 and novel[0].startswith("ITERATION_COMPLEXITY")

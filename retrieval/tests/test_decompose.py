"""Multi-prior set-cover decomposition of a full proof into known theorems + residual."""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(REPO / "analogy" / "src"))
sys.path.insert(0, str(REPO / "grounding" / "src"))

from analogy.predicates import Dgroup
from retrieval.decompose import decompose
from retrieval.engine import expr_from_json, load_library

LIB = load_library(ROOT / "library" / "proof_theorems.json")
PROOF_JSON = REPO / "grounding" / "dgroups" / "q1_full_proof.json"


def _proof():
    d = json.loads(PROOF_JSON.read_text())["target"]
    return Dgroup(d["name"], [expr_from_json(f) for f in d["facts"]])


def test_proof_decomposes_into_the_three_theorems():
    rep = decompose(_proof(), LIB)
    assert set(rep["covering_priors"]) == {
        "banach_fixed_point", "strong_convexity", "kantorovich_rubinstein"}
    assert rep["covered_facts"] >= 5


def test_novel_residual_is_the_papers_contribution():
    novel = decompose(_proof(), LIB)["novel_contributions"]
    # the epsilon-sensitivity assumption and the iteration-complexity bound are NOT in any
    # known theorem -> they are the proof's genuine contribution over textbook contraction theory
    assert any(s.startswith("SENSITIVITY") for s in novel)
    assert any(s.startswith("ITERATION_COMPLEXITY") for s in novel)


def test_residual_nonempty_so_proof_is_not_fully_reducible():
    rep = decompose(_proof(), LIB)
    assert 0.0 < rep["coverage_fraction"] < 1.0 and rep["residual_facts"]


def test_proof_and_library_are_grounded():
    from grounding.verify import check_section
    assert check_section(json.loads(PROOF_JSON.read_text())["target"])["passed"]
    lib_data = json.loads((ROOT / "library" / "proof_theorems.json").read_text())
    for key, entry in lib_data.items():
        if not key.startswith("_"):
            assert check_section(entry)["passed"], key

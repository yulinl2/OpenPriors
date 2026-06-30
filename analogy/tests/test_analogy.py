"""Tests for the SME aligner + novelty detector, against the classic ground-truth case."""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from analogy import examples, novelty
from analogy.align import _match, align
from analogy.predicates import Dgroup, order


def test_identicality_match():
    g1 = ("GREATER", ("MASS", "a"), ("MASS", "b"))
    g2 = ("GREATER", ("MASS", "c"), ("MASS", "d"))
    assert _match(g1, g2) == {("a", "c"), ("b", "d")}
    # different sub-functor (MASS vs TEMP) breaks identicality
    assert _match(g1, ("GREATER", ("TEMP", "c"), ("TEMP", "d"))) is None
    # entity vs predicate is incompatible
    assert _match("a", ("MASS", "c")) is None


def test_order():
    assert order("sun") == 0
    assert order(("MASS", "sun")) == 1
    assert order(("GREATER", ("MASS", "sun"), ("MASS", "p"))) == 2


def test_solar_atom_recovers_known_mapping():
    g = align(examples.solar_system(), examples.atom())
    assert g.correspondences == {"sun": "nucleus", "planet": "electron"}


def test_systematic_inference_outranks_distractor():
    g = align(examples.solar_system(), examples.atom())
    top = g.candidate_inferences[0]
    assert top["base_fact"].startswith("CAUSE")          # systematic causal structure
    temp = [i for i in g.candidate_inferences if i["base_fact"].startswith("GREATER(TEMP")][0]
    assert top["score"] > temp["score"]                  # CAUSE beats the distractor
    assert "nucleus" in top["projection"] and "electron" in top["projection"]


def test_novelty_full_coverage_means_zero_novelty():
    base, target = examples.solar_system(), examples.atom()
    rep = novelty.novelty_report(base, target, align(base, target))
    assert rep["target_coverage"] == 1.0 and rep["novelty_score"] == 0.0
    assert rep["top_inference"].startswith("CAUSE")


def test_unrelated_target_has_novelty():
    base = examples.solar_system()
    other = Dgroup("other", [("LOVES", "alice", "bob"), ("KNOWS", "bob", "carol")])
    rep = novelty.novelty_report(base, other, align(base, other))
    assert rep["target_coverage"] == 0.0 and rep["novelty_score"] == 1.0


def test_loads_corpus_dgroup_and_aligns():
    dg = ROOT.parent / "concept_graph" / "graphs" / "problem_07" / "dgroup.json"
    assert dg.exists(), "concept_graph dgroup fixture must exist"
    b = examples.from_concept_dgroup(dg)
    assert b.facts, "loader must produce facts (attributes + relations)"
    g = align(b, b)  # self-alignment: a graph maps onto itself
    assert g.correspondences and g.score > 0

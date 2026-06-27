"""Analogical inference transfer (Epic P): use an analogy to generate conjectures.

Candidate inferences project the base's unmatched structure onto the target as predictions.
The headline: banach_contraction ~~ weighted_conformal conjectures that the conformal
calibration procedure has a fixed point. A conjecture is confirmed if it matches an existing
target fact (modulo invented entities), else novel.
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

from analogy.predicates import Dgroup
from graphstore.crossdomain import _load_corpus, discover_role_ascension
from graphstore.model import Graph
from graphstore.transfer import _confirms, add_conjectures, transfer
from retrieval.engine import expr_from_json

CONF, _, _ = _load_corpus(REPO / "retrieval" / "library" / "conformal_theorems.json")
OPT, _, _ = _load_corpus(REPO / "grounding" / "dgroups" / "optimization_corpus.json")
PAPER = json.loads(
    (REPO / "grounding" / "dgroups" / "arxiv_2006_06138_main.json").read_text())["target"]
CONF[PAPER["name"]] = Dgroup(PAPER["name"], [expr_from_json(f) for f in PAPER["facts"]])
ASC = discover_role_ascension(CONF, OPT)


def test_banach_to_conformal_conjectures_a_fixed_point():
    conj = transfer(OPT["banach_contraction"], CONF["weighted_conformal"], ASC)
    fp = [c for c in conj if c["projection"].startswith("BANACH_FIXEDPOINT(cal_test")]
    assert len(fp) == 1
    c = fp[0]
    # a genuine prediction: the conformal procedure has no stated fixed point -> novel,
    # and the predicted object is invented (skolem)
    assert c["status"] == "novel"
    assert "skolem:" in c["projection"]
    assert c["base_fact"].startswith("BANACH_FIXEDPOINT(the_map")


def test_cross_domain_conjectures_are_predictions_not_recoveries():
    # genuinely different fields -> the analogy predicts, it doesn't recover existing facts
    conj = transfer(CONF["weighted_conformal"], OPT["banach_contraction"], ASC)
    assert conj and all(c["status"] == "novel" for c in conj)
    # e.g. it predicts a covariate-shift / likelihood-ratio structure on the contraction side
    assert any("LIKELIHOOD_RATIO" in c["projection"] for c in conj)


def test_anchored_conjectures_rank_above_pure_skolem_leaps():
    conj = transfer(CONF["weighted_conformal"], OPT["banach_contraction"], ASC)
    # the CAUSE conjecture (anchored to the matched structural property) outranks bare leaves
    top = conj[0]
    assert top["anchored"] >= 1
    assert top["confidence"] >= max(c["confidence"] for c in conj if c["anchored"] == 0)


def test_confirmation_classifier_detects_existing_structure():
    # _confirms treats skolem entities as wildcards and uses the ascension on functors
    proj = ("BANACH_FIXEDPOINT", "cal_test", "skolem:x")
    assert _confirms(proj, ("BANACH_FIXEDPOINT", "cal_test", "the_fixedpoint"), None)
    assert not _confirms(proj, ("BANACH_FIXEDPOINT", "other", "the_fixedpoint"), None)
    assert not _confirms(proj, ("COVERAGE", "cal_test", "the_fixedpoint"), None)
    # a skolem (an invented leaf object) must NOT wildcard-match a whole predicate sub-tree
    assert not _confirms(("R", "a", "skolem:x"), ("R", "a", ("NESTED", "p", "q")), None)


def test_a_confirmed_conjecture_when_target_already_has_the_structure():
    # base's REL(a, c) can't match REL(x, y) directly (c would collide with the b<->y
    # correspondence the ANCHOR already fixed), so it stays unmatched and is projected as a
    # conjecture REL(x, ?) -- which then CONFIRMS against the target's existing REL(x, y).
    base = Dgroup("b", [("ANCHOR", "a", "b"), ("REL", "a", "c")])
    target = Dgroup("t", [("ANCHOR", "x", "y"), ("REL", "x", "y")])
    conj = transfer(base, target, None)
    rel = [c for c in conj if c["projection"].startswith("REL(")]
    assert rel and rel[0]["status"] == "confirmed"


def test_conjectures_are_attached_to_the_graph(tmp_path):
    from graphstore.build import add_result
    g = Graph()
    add_result(g, "weighted_conformal", CONF["weighted_conformal"])
    conj = transfer(OPT["banach_contraction"], CONF["weighted_conformal"], ASC)
    add_conjectures(g, "banach_contraction", "weighted_conformal", conj)
    cnodes = g.nodes_of_kind("conjecture")
    assert cnodes and all(n.attrs["source_base"] == "banach_contraction" for n in cnodes)
    edges = g.out_edges("result::weighted_conformal", "conjectures")
    assert len(edges) == len(conj)
    # round-trips through JSONL (pytest tmp_path is auto-cleaned)
    g.save(tmp_path / "n.jsonl", tmp_path / "e.jsonl")
    assert Graph.load(tmp_path / "n.jsonl", tmp_path / "e.jsonl").stats() == g.stats()

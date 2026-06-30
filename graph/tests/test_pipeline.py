"""The capstone end-to-end pipeline (Epic R): every stage holds together in one run.

ingest -> lineage -> unify -> discover analogies -> transfer conjectures -> evaluate, all on
the three-literature corpus, producing one unified graph that contains results, reified facts,
relation types, lineages, analogies, conjectures, and (written back onto the conjecture nodes)
the gated verdicts.
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(REPO / "analogy" / "src"))
sys.path.insert(0, str(REPO / "retrieval" / "src"))
sys.path.insert(0, str(REPO / "grounding" / "src"))

from graphstore.model import Graph
from graphstore.pipeline import run_pipeline
from graphstore.query import analogies_of, extends_chain

REP = run_pipeline(REPO)
G = REP["graph"]


def test_four_literatures_ingested_and_unified():
    assert REP["domains"] == ["conformal", "optimization", "learning", "concentration"]
    assert REP["n_results"] >= 10
    kinds = G.stats()["node_kinds"]
    # one graph holds every object kind the project produces
    for k in ("result", "fact", "functor", "entity", "conjecture"):
        assert kinds.get(k, 0) > 0, k


def test_all_four_lineages_present():
    assert extends_chain(G, "arxiv-2006.06138-main")[:2] == ["arxiv-2006.06138-main", "weighted_conformal"]
    assert extends_chain(G, "gd_strong_convexity") == ["gd_strong_convexity", "banach_contraction"]
    assert extends_chain(G, "margin_generalization") == ["margin_generalization", "vc_generalization"]
    assert extends_chain(G, "bernstein_concentration") == ["bernstein_concentration", "mcdiarmid_concentration"]


def test_unsupervised_roles_unify_the_four_fields():
    asc = REP["discovered_roles"]
    assert (asc["WEIGHTED_EXCHANGEABLE"] == asc["CONTRACTION"] == asc["UNIFORM_CONVERGENCE"]
            == asc["BOUNDED_MARTINGALE"])


def test_analogies_and_conjectures_in_the_unified_graph():
    assert REP["n_analogies"] >= 24 and REP["n_conjectures"] > 0
    rels = G.stats()["edge_relations"]
    assert rels.get("analogous_to", 0) >= 24 and rels.get("conjectures", 0) > 0
    # the four-way analogy is reachable from any representative
    peers = {p["result"] for p in analogies_of(G, "weighted_conformal")}
    assert {"banach_contraction", "vc_generalization", "mcdiarmid_concentration"} <= peers


def test_evaluation_gate_passes_with_discriminating_verdicts():
    ev = REP["evaluation"]
    assert ev["passed"]
    dist = ev["verdict_distribution"]
    assert dist.get("plausible", 0) >= 1 and dist.get("implausible", 0) >= 1


def test_verdicts_are_written_onto_conjecture_nodes():
    # the one graph carries the judgment, not just a side report
    assert REP["n_verdicts_in_graph"] >= 1
    judged = [n for n in G.nodes_of_kind("conjecture") if "verdict" in n.attrs]
    assert judged and all(n.attrs["verdict"] in {"plausible", "uncertain", "implausible"}
                          for n in judged)
    # the fixed-point conjecture node carries its 'plausible' verdict
    fp = [n for n in judged if n.attrs.get("projection", "").startswith("BANACH_FIXEDPOINT(cal_test")]
    assert fp and fp[0].attrs["verdict"] == "plausible"


def test_unified_graph_round_trips(tmp_path):
    G.save(tmp_path / "n.jsonl", tmp_path / "e.jsonl")
    assert Graph.load(tmp_path / "n.jsonl", tmp_path / "e.jsonl").stats() == G.stats()

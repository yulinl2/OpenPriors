"""Tests for the concept-graph lift + its independent verifiers (incl. negative cases)."""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from concept_graph import sme, verify
from concept_graph.build import build_from_run, build_graph
from concept_graph.schema import ConceptGraph, Relation

RUNS = REPO / "decomposer" / "runs"

NODES = [
    {"id": "d", "type": "document", "role": "segment"},
    {"id": "d/theorem.1", "type": "theorem", "role": "assert", "text": "T contracts"},
    {"id": "d/proof.1", "type": "proof", "role": "assert", "text": "by Banach"},
    {"id": "d/equation.1", "type": "equation", "role": "formalize", "text": "x=y", "label": "eq:1"},
]
EDGES = [
    {"id": "e1", "relation": "refers_to", "source": "d/proof.1", "target": "d/equation.1", "resolved": True, "attrs": {}},
]


def test_build_lifts_nodes_and_structural_edges():
    g = build_graph(NODES, EDGES, "d")
    assert len(g.concepts) == 4
    preds = {r.predicate for r in g.relations}
    assert "contains" in preds and "refers_to" in preds
    # proof proves the preceding theorem sibling
    assert any(r.predicate == "proves" and r.object == "d/theorem.1" for r in g.relations)
    # refers_to an equation => a derives_from reasoning edge
    assert any(r.predicate == "derives_from" for r in g.relations)


def test_verifiers_pass_on_good_graph():
    g = build_graph(NODES, EDGES, "d")
    results = {r.name: r.passed for r in verify.run_all(g, EDGES)}
    assert all(results.values()), results


def test_edge_conservation_fails_when_a_relation_is_dropped():
    g = build_graph(NODES, EDGES, "d")
    g.relations = [r for r in g.relations if r.provenance != "e1"]  # drop all from edge e1
    assert not verify.check_edge_conservation(g, EDGES).passed


def test_reasoning_dag_detects_cycle():
    g = ConceptGraph(slug="d", concepts=build_graph(NODES, EDGES, "d").concepts)
    g.relations = [
        Relation(id="r1", subject="d/theorem.1", predicate="derives_from",
                 object="d/proof.1", provenance="x"),
        Relation(id="r2", subject="d/proof.1", predicate="derives_from",
                 object="d/theorem.1", provenance="y"),
    ]
    assert not verify.check_reasoning_dag_acyclic(g).passed


def test_sme_bridge_shapes():
    g = build_graph(NODES, EDGES, "d")
    dg = sme.to_dgroup(g)
    assert set(dg) >= {"entities", "attributes", "relations", "higher_order"}
    assert dg["higher_order"], "proves/derives_from should be higher-order"
    assert sme.content_vector(g) and "\n" in sme.to_ntriples(g)


def test_real_corpus_all_pass():
    structs = sorted(RUNS.glob("*/step-30-structure"))
    assert structs, "decomposer runs must exist"
    for struct in structs:
        slug = struct.parent.name
        g = build_from_run(struct, slug)
        from concept_graph.build import _load_jsonl
        edges = _load_jsonl(struct / "edges.jsonl")
        assert all(r.passed for r in verify.run_all(g, edges)), slug

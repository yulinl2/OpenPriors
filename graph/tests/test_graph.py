"""Unified (object, attribute, relation) graph store (Epic M): reification is lossless,
the reasoning chain is a subgraph, and the project's questions are graph traversals.
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
from graphstore.build import build
from graphstore.model import Edge, Graph, Node
from graphstore.query import (entities_of, expr_string, extends_chain, facts_of,
                              reasoning_subgraph, results_using_functor)
from retrieval.engine import expr_from_json, load_library
from retrieval.lineage import lineage

LIB = load_library(REPO / "retrieval" / "library" / "conformal_theorems.json")
PAPER = json.loads(
    (REPO / "grounding" / "dgroups" / "arxiv_2006_06138_main.json").read_text())["target"]
PAPER_NAME = PAPER["name"]


def _corpus():
    c = dict(LIB)
    c[PAPER_NAME] = Dgroup(PAPER_NAME, [expr_from_json(f) for f in PAPER["facts"]])
    return c


def _graph():
    c = _corpus()
    return build(c, lineage_report=lineage(c))


# -- model unit tests -----------------------------------------------------------------

def test_add_edge_requires_existing_endpoints():
    g = Graph()
    g.add_node(Node("a", "entity", "a"))
    try:
        g.add_edge(Edge("a", "missing", "arg:0"))
        assert False, "expected KeyError for missing endpoint"
    except KeyError:
        pass


def test_add_edge_dedupes_identical_triples():
    g = Graph()
    g.add_node(Node("a", "entity", "a"))
    g.add_node(Node("b", "entity", "b"))
    g.add_edge(Edge("a", "b", "arg:0"))
    g.add_edge(Edge("a", "b", "arg:0"))
    assert len(g.edges) == 1


def test_add_node_merges_attrs_idempotently():
    g = Graph()
    g.add_node(Node("x", "entity", "x", attrs={"a": 1}))
    g.add_node(Node("x", "entity", "x", attrs={"b": 2}))
    assert g.nodes["x"].attrs == {"a": 1, "b": 2} and len(g.nodes) == 1


# -- reification is lossless ----------------------------------------------------------

def test_every_fact_reconstructs_to_its_predicate_string():
    g = _graph()
    # the reified graph must reproduce every top-level fact of every result verbatim
    for name, dg in _corpus().items():
        want = sorted(_fmt(f) for f in dg.facts)
        got = sorted(expr_string(g, fid) for fid in facts_of(g, name))
        assert got == want, name


def _fmt(e):
    if isinstance(e, str):
        return e
    return f"{e[0]}({', '.join(_fmt(a) for a in e[1:])})"


def test_nested_cause_is_a_reasoning_subgraph():
    g = _graph()
    cause = next(f for f in facts_of(g, PAPER_NAME)
                 if g.nodes[f].label == "CAUSE" and "COVERAGE" in expr_string(g, f))
    sub = reasoning_subgraph(g, cause)
    # a higher-order CAUSE over two binary sub-facts: 1 + 2 + 4 = 7 nodes, 2 + 4 = 6 arg-edges
    assert sub["expr"].startswith("CAUSE(")
    assert "WEIGHTED_EXCHANGEABLE" in sub["expr"] and "COVERAGE" in sub["expr"]
    assert len(sub["nodes"]) == 7 and len(sub["edges"]) == 6


# -- the project's questions as traversals --------------------------------------------

def test_results_using_functor_is_one_query():
    g = _graph()
    assert results_using_functor(g, "LIKELIHOOD_RATIO") == sorted(
        ["importance_weighting", "weighted_conformal", PAPER_NAME])
    # a paper-only functor is used by exactly one result
    assert results_using_functor(g, "COUNTERFACTUAL") == [PAPER_NAME]
    assert results_using_functor(g, "NONEXISTENT") == []


def test_extends_chain_walks_the_lineage():
    g = _graph()
    assert extends_chain(g, PAPER_NAME) == [PAPER_NAME, "weighted_conformal", "split_conformal"]
    assert extends_chain(g, "split_conformal") == ["split_conformal"]   # a root


def test_entities_are_scoped_per_result():
    g = _graph()
    ents = entities_of(g, PAPER_NAME)
    assert "the_counterfactual" in ents and "the_ite" in ents
    # entity ids are namespaced by result so identical symbols across results don't merge
    assert all(n.id.startswith(f"{PAPER_NAME}::ent::") for n in g.nodes_of_kind("entity")
               if n.provenance == PAPER_NAME)


# -- persistence ----------------------------------------------------------------------

def test_save_load_round_trip(tmp_path):
    g = _graph()
    np_, ep = tmp_path / "nodes.jsonl", tmp_path / "edges.jsonl"
    g.save(np_, ep)
    h = Graph.load(np_, ep)
    assert h.stats() == g.stats()
    assert {n.id for n in h.nodes.values()} == {n.id for n in g.nodes.values()}
    assert {e.key() for e in h.edges} == {e.key() for e in g.edges}


def test_extends_edges_carry_novelty_and_residual():
    g = _graph()
    e = next(e for e in g.out_edges(f"result::{PAPER_NAME}", "extends"))
    assert e.dst == "result::weighted_conformal"
    assert 0.0 < e.attrs["novelty"] < 1.0
    assert any(r.startswith("COUNTERFACTUAL") for r in e.attrs["residual"])

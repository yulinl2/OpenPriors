"""Formal schema for the unified graph (Epic X): the capstone graph satisfies its own
contract, and the validator is unit-tested to FAIL on broken input (verify the validator).
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

from graphstore.model import Edge, Graph, Node
from graphstore.pipeline import run_pipeline
from graphstore.schema import REQUIRED_ATTRS, json_schema, validate

G = run_pipeline(REPO)["graph"]


def _valid_min():
    g = Graph()
    g.add_node(Node("functor::P", "functor", "P"))
    g.add_node(Node("r::ent::x", "entity", "x", attrs={"grounding": "x text"}, provenance="r"))
    g.add_node(Node("r::fact::1::P", "fact", "P", attrs={"functor": "P", "arity": 1}, provenance="r"))
    g.add_node(Node("result::r", "result", "r", attrs={"text": "t", "n_facts": 1}, provenance="r"))
    g.add_edge(Edge("r::fact::1::P", "functor::P", "instance_of"))
    g.add_edge(Edge("r::fact::1::P", "r::ent::x", "arg:0"))
    g.add_edge(Edge("result::r", "r::fact::1::P", "asserts"))
    return g


def test_capstone_graph_satisfies_its_own_schema():
    res = validate(G)
    assert res["ok"], res["errors"][:5]
    assert res["n_nodes"] > 100 and res["n_edges"] > 100


def test_emitted_schema_matches_the_validator():
    # the JSON Schema doc's per-kind required attrs must equal the validator's, no drift
    branch = {b["title"]: b for b in json_schema()["oneOf"]}
    req = {c["if"]["properties"]["kind"]["const"]:
           set(c["then"]["properties"]["attrs"]["required"]) for c in branch["node"]["allOf"]}
    for kind, attrs in REQUIRED_ATTRS.items():
        assert set(attrs) == req[kind], kind
    # and the doc round-trips as JSON
    assert json.loads(json.dumps(json_schema()))["title"]


def test_minimal_graph_is_valid():
    assert validate(_valid_min())["ok"]


# --- verify the validator: malformed graphs must FAIL ---------------------------------

def test_unknown_node_kind_fails():
    g = _valid_min()
    g.nodes["functor::P"] = Node("functor::P", "gizmo", "P")    # bypass add_node identity guard
    assert not validate(g)["ok"]


def test_missing_required_attr_fails():
    g = Graph()
    g.add_node(Node("r::ent::x", "entity", "x"))               # entity with no grounding attr
    rep = validate(g)
    assert not rep["ok"] and any("grounding" in e for e in rep["errors"])


def test_dangling_edge_endpoint_fails():
    g = _valid_min()
    g.edges.append(Edge("result::r", "result::ghost", "extends"))   # dst is not a node
    rep = validate(g)
    assert not rep["ok"] and any("not a node" in e for e in rep["errors"])


def test_unknown_relation_fails():
    g = _valid_min()
    g.edges.append(Edge("result::r", "functor::P", "teleports_to"))
    assert not validate(g)["ok"]


def test_noncontiguous_arg_indices_fail():
    g = _valid_min()
    # add arg:2 without arg:1 -> a gap in the fact's argument structure
    g.add_node(Node("r::ent::y", "entity", "y", attrs={"grounding": "y"}, provenance="r"))
    g.edges.append(Edge("r::fact::1::P", "r::ent::y", "arg:2"))
    rep = validate(g)
    assert not rep["ok"] and any("contiguous" in e for e in rep["errors"])

"""Build the unified graph from grounded dgroups + the reasoning lineage.

Every relational fact is **reified**: a fact node carries the functor, an ``instance_of`` edge
links it to its functor node (so relation types are first-class), and one ``arg:i`` edge per
argument points at the argument's node — an entity, or (for higher-order facts like ``CAUSE``)
another fact node. The result asserts its top-level facts; the lineage supplies ``extends``
edges between result nodes. The output is one graph in which objects, their attributes, and
their relations all live together and are traversable.
"""

from __future__ import annotations

from analogy.predicates import Dgroup, args, functor, is_entity

from .model import Edge, Graph, Node


def _entity_id(result: str, name: str) -> str:
    # entities are per-result skolem variables; scope the id by result to avoid false merges
    return f"{result}::ent::{name}"


def _add_expr(g: Graph, result: str, expr, groundings: dict, counter: list) -> str:
    """Reify ``expr`` into the graph, returning its node id."""
    if is_entity(expr):
        nid = _entity_id(result, expr)
        g.add_node(Node(nid, "entity", expr,
                        attrs={"grounding": groundings.get(expr, "")},
                        provenance=result))
        return nid

    f = functor(expr)
    counter[0] += 1
    fid = f"{result}::fact::{counter[0]}::{f}"
    g.add_node(Node(fid, "fact", f, attrs={"functor": f, "arity": len(args(expr))},
                    provenance=result))
    # functor node + instance_of edge make relation types first-class and queryable
    fn_id = f"functor::{f}"
    g.add_node(Node(fn_id, "functor", f))
    g.add_edge(Edge(fid, fn_id, "instance_of", provenance=result))
    for i, a in enumerate(args(expr)):
        child = _add_expr(g, result, a, groundings, counter)
        g.add_edge(Edge(fid, child, f"arg:{i}", provenance=result))
    return fid


def add_result(g: Graph, name: str, dgroup: Dgroup, text: str = "",
               groundings: dict | None = None) -> None:
    groundings = groundings or {}
    g.add_node(Node(f"result::{name}", "result", name,
                    attrs={"text": text, "n_facts": len(dgroup.facts)}, provenance=name))
    counter = [0]
    for fact in dgroup.facts:
        fid = _add_expr(g, name, fact, groundings, counter)
        g.add_edge(Edge(f"result::{name}", fid, "asserts", provenance=name))
        g.add_edge(Edge(fid, f"result::{name}", "in", provenance=name))


def add_lineage(g: Graph, lineage_report: dict) -> None:
    for e in lineage_report.get("edges", []):
        src, dst = f"result::{e['child']}", f"result::{e['parent']}"
        if src in g.nodes and dst in g.nodes:
            # "residual" carries the FULL residual (incl. CAUSE glue); novel_contributions is
            # the CAUSE-filtered view. Keeping both keeps the attribute name honest.
            g.add_edge(Edge(src, dst, "extends",
                            attrs={"novelty": e.get("novelty"),
                                   "residual": e.get("residual", []),
                                   "novel_contributions": e.get("novel_contributions", [])},
                            provenance="lineage"))


def build(corpus: dict[str, Dgroup], texts: dict | None = None,
          groundings: dict | None = None, lineage_report: dict | None = None) -> Graph:
    texts, groundings = texts or {}, groundings or {}
    g = Graph()
    for name, dg in corpus.items():
        add_result(g, name, dg, texts.get(name, ""), groundings.get(name, {}))
    if lineage_report:
        add_lineage(g, lineage_report)
    return g

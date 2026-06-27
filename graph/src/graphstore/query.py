"""Queries over the unified graph — the questions the whole pipeline was built to answer,
now as graph traversals rather than bespoke passes.
"""

from __future__ import annotations

from .model import Graph


def results_using_functor(g: Graph, functor: str) -> list[str]:
    """Which results assert a fact with this relation type? (functor <- fact <- result)"""
    fn_id = f"functor::{functor}"
    if fn_id not in g.nodes:
        return []
    out = set()
    for e in g.in_edges(fn_id, "instance_of"):          # facts that are this functor
        for ein in g.out_edges(e.src, "in"):            # the result the fact lives in
            out.add(g.nodes[ein.dst].label)
    return sorted(out)


def facts_of(g: Graph, result: str) -> list[str]:
    """Top-level fact node ids the result asserts."""
    return sorted(e.dst for e in g.out_edges(f"result::{result}", "asserts"))


def entities_of(g: Graph, result: str) -> list[str]:
    return sorted(n.label for n in g.nodes_of_kind("entity") if n.provenance == result)


def extends_chain(g: Graph, result: str) -> list[str]:
    """The ancestor path from ``result`` up its direct-parent ``extends`` edges."""
    chain, cur, seen = [result], f"result::{result}", set()
    while True:
        nxt = g.out_edges(cur, "extends")
        if not nxt or cur in seen:
            break
        seen.add(cur)
        cur = nxt[0].dst
        chain.append(g.nodes[cur].label)
    return chain


def expr_string(g: Graph, fact_id: str) -> str:
    """Reconstruct the predicate-calculus string of a (possibly nested) reified fact —
    proof that reification is lossless and the reasoning chain is fully in the graph."""
    node = g.nodes[fact_id]
    if node.kind == "entity":
        return node.label
    arg_edges = sorted((e for e in g.out_edges(fact_id) if e.relation.startswith("arg:")),
                       key=lambda e: int(e.relation.split(":")[1]))
    inner = ", ".join(expr_string(g, e.dst) for e in arg_edges)
    return f"{node.label}({inner})"


def reasoning_subgraph(g: Graph, fact_id: str) -> dict:
    """All nodes/edges reachable through the argument structure of ``fact_id`` — the
    reasoning chain rooted at a (higher-order) fact, e.g. a CAUSE over two sub-facts."""
    nodes, edges, stack = set(), [], [fact_id]
    while stack:
        cur = stack.pop()
        if cur in nodes:
            continue
        nodes.add(cur)
        for e in g.out_edges(cur):
            if e.relation.startswith("arg:"):
                edges.append(e.key())
                stack.append(e.dst)
    return {"root": fact_id, "expr": expr_string(g, fact_id),
            "nodes": sorted(nodes), "edges": sorted(edges)}

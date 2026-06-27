"""A small query DSL over the unified graph (Epic S): make the graph interrogable.

The pipeline produces one graph holding results, facts, relation types, lineages, cross-domain
analogies, conjectures and verdicts. This module is the read layer — a handful of composable
queries that answer the questions a user actually asks of such a graph:

  * ``shortest_path`` — how are two concepts/results connected? (undirected BFS across every
    relation, so a path may cross a lineage edge into an analogy edge into a conjecture);
  * ``shared_ancestor`` — the common root two results build on, via the lineage;
  * ``explain_analogy`` — why are two results analogous? (the SME correspondence + shared
    structure on the ``analogous_to`` edge);
  * ``conjectures_with_verdicts`` — what did a result's analogies predict, and how were those
    predictions judged?
  * ``find`` — locate nodes by label substring.

The point: the whole multi-stage pipeline collapses into one graph you can simply *query*,
and a single path can run from a conformal theorem through the analogy web into a learning
-theory result — the literatures are concretely linked, not just adjacent.
"""

from __future__ import annotations

from collections import deque

from .model import Graph


def find(g: Graph, needle: str, kind: str | None = None) -> list[str]:
    """Node ids whose label contains ``needle`` (optionally filtered by kind)."""
    return sorted(n.id for n in g.nodes.values()
                  if needle.lower() in n.label.lower() and (kind is None or n.kind == kind))


def shortest_path(g: Graph, src: str, dst: str) -> list[dict] | None:
    """Undirected shortest path src->dst as a list of {from, relation, dir, to} steps."""
    if src not in g.nodes or dst not in g.nodes:
        return None
    prev: dict = {src: None}
    q = deque([src])
    while q:
        u = q.popleft()
        if u == dst:
            break
        for e in g.out_edges(u):
            if e.dst not in prev:
                prev[e.dst] = (u, e.relation, "->")
                q.append(e.dst)
        for e in g.in_edges(u):
            if e.src not in prev:
                prev[e.src] = (u, e.relation, "<-")
                q.append(e.src)
    if dst not in prev:
        return None
    steps, cur = [], dst
    while prev[cur] is not None:
        u, rel, d = prev[cur]
        steps.append({"from": u, "relation": rel, "dir": d, "to": cur})
        cur = u
    return list(reversed(steps))


def _ancestors(g: Graph, result: str) -> list[str]:
    chain, cur = [], f"result::{result}"
    seen = set()
    while cur and cur not in seen:
        seen.add(cur)
        chain.append(g.nodes[cur].label)
        nxt = g.out_edges(cur, "extends")
        cur = nxt[0].dst if nxt else None
    return chain


def shared_ancestor(g: Graph, r1: str, r2: str) -> str | None:
    """The most specific common ancestor of two results along the lineage, if any."""
    a1, a2 = _ancestors(g, r1), set(_ancestors(g, r2))
    for a in a1:                       # a1 is ordered self -> ... -> root; first common wins
        if a in a2:
            return a
    return None


def explain_analogy(g: Graph, r1: str, r2: str) -> dict | None:
    """The correspondence + shared structure on the analogous_to edge between two results."""
    n1, n2 = f"result::{r1}", f"result::{r2}"
    for e in g.out_edges(n1, "analogous_to") + g.in_edges(n1, "analogous_to"):
        if e.src in (n1, n2) and e.dst in (n1, n2):
            return {"between": [r1, r2], "score": e.attrs.get("score"),
                    "correspondences": e.attrs.get("correspondences", {}),
                    "shared_structure": e.attrs.get("shared_structure", [])}
    return None


def conjectures_with_verdicts(g: Graph, result: str) -> list[dict]:
    """The conjectures attached to a result, with verdicts where they were judged."""
    out = []
    for e in g.out_edges(f"result::{result}", "conjectures"):
        n = g.nodes[e.dst]
        out.append({"projection": n.attrs.get("projection"),
                    "from_base": n.attrs.get("source_base"),
                    "status": n.attrs.get("status"),
                    "verdict": n.attrs.get("verdict"),
                    "confidence": n.attrs.get("confidence")})
    return sorted(out, key=lambda c: (c["verdict"] is None, -(c["confidence"] or 0)))


def fmt_path(steps: list[dict]) -> str:
    if not steps:
        return "(no path)"
    parts = [steps[0]["from"]]
    for s in steps:
        parts.append(f" --{s['relation']}{s['dir']}--> {s['to']}")
    return "".join(parts)

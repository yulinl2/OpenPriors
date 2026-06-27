"""The unified node/edge graph: the project's target shape, made concrete.

The whole pipeline has been building toward "a package formally representing concepts and
reasoning chains as an (object, attribute, relation) node/edge graph." This module is the
store for that graph — a small, dependency-free, deterministic property graph with JSONL
persistence (matching the repo's redundant-representation policy: a graph is its
``nodes.jsonl`` + ``edges.jsonl``).

Design: a single typed graph holds every kind of object the pipeline produces —

  * **entity** nodes  — grounded symbols (the *objects*), attributes carry the grounding text;
  * **fact** nodes    — every relational fact is **reified** as a node carrying its functor,
    with one ``arg:i`` edge per argument. Reification (rather than a labelled src→dst edge)
    is what lets the same graph hold **n-ary** relations and **nested** higher-order facts
    (``CAUSE`` over two facts) uniformly — so a reasoning chain is literally a subgraph;
  * **functor** nodes — the relation *types* (the *relations*), so "which results use this
    relation?" is one hop; and
  * **result** nodes  — whole results/papers, linked by ``extends`` edges (the lineage).

Every node and edge carries ``attrs`` (its attributes) and a ``provenance`` tag, so any
fact can be traced back to the result and grounding it came from.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Node:
    id: str
    kind: str                       # entity | fact | functor | result
    label: str
    attrs: dict = field(default_factory=dict)
    provenance: str = ""

    def to_json(self) -> dict:
        return {"id": self.id, "kind": self.kind, "label": self.label,
                "attrs": self.attrs, "provenance": self.provenance}

    @staticmethod
    def from_json(d: dict) -> "Node":
        return Node(d["id"], d["kind"], d["label"], d.get("attrs", {}), d.get("provenance", ""))


@dataclass(frozen=True)
class Edge:
    src: str
    dst: str
    relation: str                   # arg:i | instance_of | asserts | in | extends
    attrs: dict = field(default_factory=dict)
    provenance: str = ""

    def key(self) -> tuple:
        return (self.src, self.dst, self.relation)

    def to_json(self) -> dict:
        return {"src": self.src, "dst": self.dst, "relation": self.relation,
                "attrs": self.attrs, "provenance": self.provenance}

    @staticmethod
    def from_json(d: dict) -> "Edge":
        return Edge(d["src"], d["dst"], d["relation"], d.get("attrs", {}), d.get("provenance", ""))


class Graph:
    """An append-only typed property graph with deterministic ordering."""

    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self._edges_by_key: dict[tuple, Edge] = {}
        self.edges: list[Edge] = []

    # -- construction -----------------------------------------------------------------
    def add_node(self, node: Node) -> str:
        # Re-adding the same id is idempotent and merges attrs, but identity (kind/label/
        # provenance) must agree — a mismatch means two different logical nodes collided on
        # an id (an ingestion bug), so we fail loud rather than silently keep the first.
        existing = self.nodes.get(node.id)
        if existing is None:
            self.nodes[node.id] = node
            return node.id
        if (existing.kind, existing.label, existing.provenance) != \
                (node.kind, node.label, node.provenance):
            raise ValueError(
                f"node id {node.id!r} re-added with conflicting identity: "
                f"{(existing.kind, existing.label, existing.provenance)} != "
                f"{(node.kind, node.label, node.provenance)}")
        merged = dict(existing.attrs)
        merged.update(node.attrs)
        self.nodes[node.id] = Node(existing.id, existing.kind, existing.label,
                                   merged, existing.provenance)
        return node.id

    def add_edge(self, edge: Edge) -> None:
        if edge.src not in self.nodes or edge.dst not in self.nodes:
            raise KeyError(f"edge endpoints must exist: {edge.src} -> {edge.dst}")
        prev = self._edges_by_key.get(edge.key())   # dedupe identical (src,dst,relation)
        if prev is not None:
            # identical re-add is a no-op; same triple with different metadata is a bug
            if (prev.attrs, prev.provenance) != (edge.attrs, edge.provenance):
                raise ValueError(
                    f"edge {edge.key()} re-added with conflicting data: "
                    f"{(prev.attrs, prev.provenance)} != {(edge.attrs, edge.provenance)}")
            return
        self._edges_by_key[edge.key()] = edge
        self.edges.append(edge)

    # -- queries ----------------------------------------------------------------------
    def out_edges(self, node_id: str, relation: str | None = None) -> list[Edge]:
        return [e for e in self.edges if e.src == node_id
                and (relation is None or e.relation == relation)]

    def in_edges(self, node_id: str, relation: str | None = None) -> list[Edge]:
        return [e for e in self.edges if e.dst == node_id
                and (relation is None or e.relation == relation)]

    def neighbors(self, node_id: str, relation: str | None = None) -> list[str]:
        return [e.dst for e in self.out_edges(node_id, relation)]

    def nodes_of_kind(self, kind: str) -> list[Node]:
        return sorted((n for n in self.nodes.values() if n.kind == kind), key=lambda n: n.id)

    def stats(self) -> dict:
        kinds: dict[str, int] = {}
        for n in self.nodes.values():
            kinds[n.kind] = kinds.get(n.kind, 0) + 1
        rels: dict[str, int] = {}
        for e in self.edges:
            rels[e.relation] = rels.get(e.relation, 0) + 1
        return {"n_nodes": len(self.nodes), "n_edges": len(self.edges),
                "node_kinds": kinds, "edge_relations": rels}

    # -- persistence ------------------------------------------------------------------
    def save(self, nodes_path, edges_path) -> None:
        nodes_path.write_text(
            "".join(json.dumps(n.to_json(), sort_keys=True, ensure_ascii=False) + "\n"
                    for n in sorted(self.nodes.values(), key=lambda n: n.id)),
            encoding="utf-8")
        edges_path.write_text(
            "".join(json.dumps(e.to_json(), sort_keys=True, ensure_ascii=False) + "\n"
                    for e in sorted(self.edges, key=lambda e: e.key())),
            encoding="utf-8")

    @staticmethod
    def load(nodes_path, edges_path) -> "Graph":
        g = Graph()
        for line in nodes_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                g.add_node(Node.from_json(json.loads(line)))
        for line in edges_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                g.add_edge(Edge.from_json(json.loads(line)))
        return g

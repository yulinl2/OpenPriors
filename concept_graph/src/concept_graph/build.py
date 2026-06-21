"""Build a ConceptGraph from a decomposer bundle (deterministic lift).

Two layers (see docs/principles-continuity.md):
  1. **Structural lift** (lossless, no NL): every node -> a Concept; the containment
     tree + every cite/refers_to edge -> Relations.
  2. **Derived semantic relations** (deterministic heuristics): `proves` (a proof proves
     its preceding theorem-like sibling) and `derives_from` (a reasoning step that
     \\ref/\\eqref's a prior equation) — the latter assembles the **reasoning-chain DAG**.

The fine-grained, in-statement OAR extraction (e.g. "T is a γ-contraction" ->
(T, is-a, contraction)) is the documented sub-agent frontier and is intentionally NOT
done here, to keep this layer deterministic and verifiable.
"""

from __future__ import annotations

import json
from pathlib import Path

from .schema import Concept, ConceptGraph, Relation

ASSERT_KINDS = {"theorem", "definition", "assumption", "remark", "problem_statement"}
FORMALIZE_KINDS = {"equation"}


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _parent_id(node_id: str) -> str | None:
    """Containment parent from the path-based id (`a/b/c` -> `a/b`)."""
    return node_id.rsplit("/", 1)[0] if "/" in node_id else None


def _concept_of(node: dict) -> Concept:
    excerpt = (node.get("text") or "")[:160] or None
    name = node.get("title") or node.get("label") or excerpt
    attrs = {
        "kind": node["type"], "role": node["role"], "depth": node.get("depth", 0),
        "order": node.get("order", 0),
    }
    for k in ("content_sha256", "source_file"):
        if node.get(k):
            attrs[k] = node[k]
    if node.get("attrs"):
        attrs.update({f"x_{k}": v for k, v in node["attrs"].items()})
    return Concept(id=node["id"], kind=node["type"], role=node["role"],
                   name=name, label=node.get("label"), attributes=attrs,
                   source_node=node["id"])


def build_graph(nodes: list[dict], edges: list[dict], slug: str) -> ConceptGraph:
    concepts = [_concept_of(n) for n in nodes]
    cids = {c.id for c in concepts}
    by_id = {n["id"]: n for n in nodes}
    relations: list[Relation] = []
    rid = 0

    def add(subj, pred, obj, *, resolved=True, higher_order=False, prov, **attrs):
        nonlocal rid
        rid += 1
        relations.append(Relation(id=f"r.{rid}", subject=subj, predicate=pred,
                                   object=obj, resolved=resolved,
                                   higher_order=higher_order, attributes=attrs,
                                   provenance=prov))

    # 1a. containment tree -> contains relations
    for n in nodes:
        p = _parent_id(n["id"])
        if p is not None and p in cids:
            add(p, "contains", n["id"], prov=n["id"])

    # 1b. structural edges -> cites / refers_to
    for e in edges:
        rel = e["relation"]
        if rel not in ("cites", "refers_to"):
            continue
        tgt = e["target"]
        resolved = bool(e.get("resolved")) and tgt in cids
        add(e["source"], rel, tgt, resolved=resolved,
            prov=e["id"], external=not resolved, **{k: v for k, v in e.get("attrs", {}).items() if k == "key"})

    # 2a. derived: proof proves nearest preceding theorem-like sibling
    children_by_parent: dict[str, list[dict]] = {}
    for n in nodes:
        children_by_parent.setdefault(_parent_id(n["id"]) or "", []).append(n)
    for sibs in children_by_parent.values():
        sibs_sorted = sorted(sibs, key=lambda x: x.get("order", 0))
        for i, n in enumerate(sibs_sorted):
            if n["type"] == "proof":
                for j in range(i - 1, -1, -1):
                    if sibs_sorted[j]["type"] in ASSERT_KINDS:
                        add(n["id"], "proves", sibs_sorted[j]["id"],
                            higher_order=True, prov=n["id"])
                        break

    # 2b. derived: refers_to a formalize/assert target -> derives_from (reasoning chain)
    for e in edges:
        if e["relation"] != "refers_to":
            continue
        tgt = by_id.get(e["target"])
        src = by_id.get(e["source"])
        if tgt and src and tgt["type"] in (FORMALIZE_KINDS | ASSERT_KINDS):
            add(e["source"], "derives_from", e["target"], higher_order=True,
                prov=e["id"])

    g = ConceptGraph(slug=slug, concepts=concepts, relations=relations)
    from collections import Counter
    pred_counts = dict(Counter(r.predicate for r in relations))
    chain = [r for r in relations if r.predicate in ("derives_from", "proves")]
    g.metrics = {
        "n_concepts": len(concepts),
        "n_relations": len(relations),
        "predicate_counts": pred_counts,
        "n_reasoning_edges": len(chain),
        "n_resolved": sum(r.resolved for r in relations),
        "concept_kind_counts": dict(Counter(c.kind for c in concepts)),
    }
    return g


def build_from_run(run_structure_dir: str | Path, slug: str) -> ConceptGraph:
    d = Path(run_structure_dir)
    nodes = _load_jsonl(d / "nodes.jsonl")
    edges = _load_jsonl(d / "edges.jsonl")
    return build_graph(nodes, edges, slug)

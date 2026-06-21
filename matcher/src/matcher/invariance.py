"""Renaming-invariance: the linchpin property of the whole OpenPriors thesis.

Structure-mapping is "isomorphism under renaming, not lexical overlap"
(`Imports/structure mapping notes.md` §1). So the retrieval signal must be **invariant
under a bijective relabeling of entities**: rename every concept id and the content
vector, the relation multiset, and therefore every MAC score must be unchanged.

This module relabels a graph and checks that invariance as a *metamorphic* test — an
oracle that needs no ground truth, only the relation the correct output must satisfy.
It also computes a **systematicity** proxy (depth of the higher-order reasoning DAG),
which is SME's selection principle for preferring deep, interconnected structure.
"""

from __future__ import annotations

import sys
from pathlib import Path

# reuse Epic B's canonical model + content-vector emitter (no drift)
_CG = Path(__file__).resolve().parents[3] / "concept_graph" / "src"
if str(_CG) not in sys.path:
    sys.path.insert(0, str(_CG))

from concept_graph.schema import ConceptGraph  # noqa: E402
from concept_graph.sme import content_vector  # noqa: E402


def relabel(g: ConceptGraph, mapping: dict[str, str]) -> ConceptGraph:
    """Apply a bijective id relabeling (entities renamed; predicates/attrs untouched)."""
    concepts = [c.model_copy(update={
        "id": mapping.get(c.id, c.id),
        "source_node": mapping.get(c.source_node, c.source_node),
    }) for c in g.concepts]
    relations = [r.model_copy(update={
        "subject": mapping.get(r.subject, r.subject),
        "object": mapping.get(r.object, r.object),
    }) for r in g.relations]
    return ConceptGraph(slug=g.slug + "#renamed", concepts=concepts, relations=relations)


def canonical_relabeling(g: ConceptGraph) -> dict[str, str]:
    """A deterministic bijection mapping every concept id to a fresh opaque token."""
    return {cid: f"E{i}" for i, cid in enumerate(sorted(c.id for c in g.concepts))}


def predicate_multiset(g: ConceptGraph) -> dict[str, int]:
    from collections import Counter
    return dict(Counter(r.predicate for r in g.relations))


def check_renaming_invariance(g: ConceptGraph) -> dict:
    """Metamorphic check: relabel entities => content vector & relation multiset unchanged."""
    g2 = relabel(g, canonical_relabeling(g))
    v1, v2 = content_vector(g), content_vector(g2)
    m1, m2 = predicate_multiset(g), predicate_multiset(g2)
    invariant = (v1 == v2) and (m1 == m2)
    return {
        "name": "renaming_invariance",
        "passed": invariant,
        "content_vector_invariant": v1 == v2,
        "relation_multiset_invariant": m1 == m2,
        "n_entities_renamed": len(g.concepts),
    }


def systematicity(g: ConceptGraph) -> dict:
    """SME systematicity proxy: size + longest path of the higher-order reasoning DAG."""
    adj: dict[str, list[str]] = {}
    for r in g.relations:
        if r.higher_order:
            adj.setdefault(r.subject, []).append(r.object)
    # longest path in a DAG via memoized DFS (graph is verified acyclic upstream)
    memo: dict[str, int] = {}

    def longest(u: str) -> int:
        if u in memo:
            return memo[u]
        memo[u] = 0
        best = 0
        for v in adj.get(u, []):
            best = max(best, 1 + longest(v))
        memo[u] = best
        return best

    depth = max((longest(u) for u in adj), default=0)
    n_ho = sum(len(v) for v in adj.values())
    return {
        "n_higher_order_relations": n_ho,
        "max_reasoning_depth": depth,
        "systematicity_score": round(n_ho * (1 + depth), 3),  # size x depth
    }

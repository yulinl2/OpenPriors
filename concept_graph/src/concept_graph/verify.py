"""Build-independent verification of the concept-graph lift.

Same doctrine as the decomposer's `verify/`: checks share no logic with `build.py`; each
is a machine-checkable predicate that can FAIL on a broken lift. Principles continue
P1-P4 (see docs/principles-continuity.md):
  * P1 conservation  -> every structural decomposer edge becomes a relation.
  * P3 schema        -> the graph validates against its declared schema.
  * P4 integrity     -> every relation endpoint resolves to a concept (or is logged
                        external); the reasoning DAG (proves/derives_from) is acyclic.
"""

from __future__ import annotations

from pydantic import BaseModel, ValidationError

from .schema import ConceptGraph


class CheckResult(BaseModel):
    name: str
    principle: str
    passed: bool
    metrics: dict = {}
    detail: str = ""


def check_schema_valid(g: ConceptGraph) -> CheckResult:
    try:
        ConceptGraph.model_validate(g.model_dump())
        return CheckResult(name="schema_valid", principle="P3", passed=True)
    except ValidationError as e:  # pragma: no cover
        return CheckResult(name="schema_valid", principle="P3", passed=False, detail=str(e))


def check_edge_conservation(g: ConceptGraph, decomposer_edges: list[dict]) -> CheckResult:
    """P1 — every cites/refers_to decomposer edge is represented by >=1 relation."""
    structural = [e for e in decomposer_edges if e["relation"] in ("cites", "refers_to")]
    provs = {r.provenance for r in g.relations}
    missing = [e["id"] for e in structural if e["id"] not in provs]
    return CheckResult(
        name="edge_conservation", principle="P1", passed=not missing,
        metrics={"n_decomposer_edges": len(structural),
                 "n_relations": len(g.relations), "n_missing": len(missing)},
        detail="" if not missing else f"unlifted edges: {missing[:8]}",
    )


def check_traceability(g: ConceptGraph) -> CheckResult:
    """P4 — every concept has a source node; every relation endpoint resolves/logged."""
    cids = g.concept_ids()
    bad_concept = [c.id for c in g.concepts if not c.source_node]
    dangling = []
    for r in g.relations:
        if r.subject not in cids:
            dangling.append((r.id, "subject", r.subject))
        if r.resolved and r.object not in cids:
            dangling.append((r.id, "object", r.object))
    ok = not bad_concept and not dangling
    return CheckResult(
        name="traceability", principle="P4", passed=ok,
        metrics={"n_concepts": len(g.concepts), "n_unsourced": len(bad_concept),
                 "n_dangling": len(dangling)},
        detail="" if ok else f"dangling: {dangling[:8]} unsourced: {bad_concept[:8]}",
    )


def check_reasoning_dag_acyclic(g: ConceptGraph) -> CheckResult:
    """P4 — the reasoning chain (proves/derives_from) is acyclic (a valid derivation)."""
    adj: dict[str, list[str]] = {}
    for r in g.relations:
        if r.predicate in ("proves", "derives_from"):
            adj.setdefault(r.subject, []).append(r.object)
    WHITE, GREY, BLACK = 0, 1, 2
    color: dict[str, int] = {}
    cycle = False

    def dfs(u: str) -> None:
        nonlocal cycle
        color[u] = GREY
        for v in adj.get(u, []):
            if color.get(v, WHITE) == GREY:
                cycle = True
            elif color.get(v, WHITE) == WHITE:
                dfs(v)
        color[u] = BLACK

    for n in list(adj):
        if color.get(n, WHITE) == WHITE:
            dfs(n)
    n_edges = sum(len(v) for v in adj.values())
    return CheckResult(
        name="reasoning_dag_acyclic", principle="P4", passed=not cycle,
        metrics={"n_reasoning_edges": n_edges, "cycle": cycle},
        detail="" if not cycle else "cycle in proves/derives_from chain",
    )


def run_all(g: ConceptGraph, decomposer_edges: list[dict]) -> list[CheckResult]:
    return [
        check_schema_valid(g),
        check_edge_conservation(g, decomposer_edges),
        check_traceability(g),
        check_reasoning_dag_acyclic(g),
    ]

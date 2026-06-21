"""Reusable, build-independent invariant checkers (独立检验 as library code).

Each check is a machine-checkable predicate derived from a principle (P1-P4 in
``docs/principles.md``). They share no code with the extractors, so a bug in an
extractor does not silently pass its own check. ``check_idempotent`` and the
differential check live closest to the build; ``check_character_coverage`` and
``check_reference_integrity`` are pure accounting over the *output* and are the
strongest independent oracles.
"""

from __future__ import annotations

from typing import Callable, Optional

from pydantic import BaseModel, Field, ValidationError

from ..schema import Decomposition, Node


class CheckResult(BaseModel):
    name: str
    principle: str
    passed: bool
    metrics: dict = Field(default_factory=dict)
    detail: str = ""


def check_schema_valid(decomp: Decomposition) -> CheckResult:
    """P3 — the bundle round-trips through its own declared schema."""
    try:
        Decomposition.model_validate(decomp.model_dump())
        return CheckResult(name="schema_valid", principle="P3", passed=True,
                           detail="bundle validates against Pydantic schema")
    except ValidationError as e:  # pragma: no cover - defensive
        return CheckResult(name="schema_valid", principle="P3", passed=False, detail=str(e))


def check_unique_ids(decomp: Decomposition) -> CheckResult:
    """P4 — node ids are unique (a precondition for well-defined edges)."""
    ids = [n.id for n in decomp.all_nodes()]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    return CheckResult(
        name="unique_ids", principle="P4", passed=not dupes,
        metrics={"n_nodes": len(ids), "n_duplicates": len(dupes)},
        detail="" if not dupes else f"duplicate ids: {dupes[:10]}",
    )


def check_acyclic_tree(decomp: Decomposition) -> CheckResult:
    """P4 — containment is a single-rooted tree: each node reached exactly once.

    Cycle-safe: a malformed tree containing a cycle is detected and reported as a
    failure rather than recursing forever (this is a gate, it must not crash).
    """
    visit_count: dict[int, int] = {}
    cycle = False

    def walk(n: Node, ancestors: frozenset) -> None:
        nonlocal cycle
        for c in n.children:
            cid = id(c)
            visit_count[cid] = visit_count.get(cid, 0) + 1
            if cid in ancestors:          # back-edge => cycle; do not recurse
                cycle = True
                continue
            walk(c, ancestors | {cid})

    walk(decomp.document, frozenset({id(decomp.document)}))
    multi = [k for k, v in visit_count.items() if v > 1]
    passed = not multi and not cycle
    detail = ""
    if cycle:
        detail = "containment cycle detected"
    elif multi:
        detail = f"{len(multi)} nodes reached more than once (DAG, not a tree)"
    return CheckResult(
        name="acyclic_tree", principle="P4", passed=passed,
        metrics={"n_edges": len(visit_count), "cycle": cycle}, detail=detail,
    )


def _leaf_spans(decomp: Decomposition) -> list[tuple[int, int, str]]:
    spans = []
    for n in decomp.all_nodes():
        if not n.children and n.span is not None:
            spans.append((n.span.start, n.span.end, n.id))
    return spans


def check_character_coverage(decomp: Decomposition, normalized_len: int,
                             min_ratio: float = 0.70) -> CheckResult:
    """P1 — every content character is attributed to exactly one leaf (a partition).

    Independent of *how* the document was parsed: it only audits the spans the build
    emitted against the length of the normalized source. Overlap => double-attribution
    (a real bug); the uncovered remainder is structural scaffolding (logged redundancy).
    """
    spans = sorted(_leaf_spans(decomp))
    covered = 0
    overlap = 0
    prev_end = 0
    for start, end, _ in spans:
        if end <= start:
            continue
        if start < prev_end:                       # overlap with previous leaf
            overlap += min(end, prev_end) - start
            start = prev_end
        if end > start:
            covered += end - start
            prev_end = max(prev_end, end)
    ratio = covered / normalized_len if normalized_len else 0.0
    passed = (overlap == 0) and (ratio >= min_ratio)
    return CheckResult(
        name="character_coverage", principle="P1", passed=passed,
        metrics={"normalized_len": normalized_len, "covered_chars": covered,
                 "coverage_ratio": round(ratio, 4), "overlap_chars": overlap,
                 "min_ratio": min_ratio, "n_leaf_spans": len(spans)},
        detail="" if passed else (
            f"overlap={overlap} (must be 0), coverage={ratio:.3f} (min {min_ratio})"),
    )


def check_reference_integrity(decomp: Decomposition) -> CheckResult:
    """P4 — every internal cross-ref/citation edge resolves to a node id."""
    node_ids = {n.id for n in decomp.all_nodes()}
    labels = {n.label for n in decomp.all_nodes() if n.label}
    dangling = []
    external = 0
    for e in decomp.edges:
        if e.relation in ("contains", "in_bibliography", "has_label"):
            continue
        if e.attrs.get("external"):
            external += 1
            continue
        if e.target not in node_ids and e.target not in labels:
            dangling.append((e.id, e.relation, e.target))
    return CheckResult(
        name="reference_integrity", principle="P4", passed=not dangling,
        metrics={"n_edges": len(decomp.edges), "n_dangling": len(dangling),
                 "n_external": external},
        detail="" if not dangling else f"dangling refs: {dangling[:10]}",
    )


def check_idempotent(normalize: Callable[[str], str], raw: str) -> CheckResult:
    """P2 — normalization is a fixpoint: ``normalize(normalize(x)) == normalize(x)``."""
    once = normalize(raw)
    twice = normalize(once)
    return CheckResult(
        name="idempotent_normalization", principle="P2", passed=(once == twice),
        metrics={"len_once": len(once), "len_twice": len(twice)},
        detail="" if once == twice else "second pass changed the output",
    )


def run_all(decomp: Decomposition, normalized_len: int,
            min_coverage: float = 0.70,
            normalize: Optional[Callable[[str], str]] = None,
            raw: Optional[str] = None) -> list[CheckResult]:
    results = [
        check_schema_valid(decomp),
        check_unique_ids(decomp),
        check_acyclic_tree(decomp),
        check_character_coverage(decomp, normalized_len, min_coverage),
        check_reference_integrity(decomp),
    ]
    if normalize is not None and raw is not None:
        results.append(check_idempotent(normalize, raw))
    return results

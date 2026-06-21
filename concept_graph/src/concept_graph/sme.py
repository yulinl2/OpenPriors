"""SME / MAC-FAC bridge: emit the structures a structure-mapping matcher consumes.

Per `docs/lit-review-oar-kg.md` §3, our (object, attribute, relation) graph is a direct
serialization of SME *dgroups* (entities + 1-place attributes + n-ary relations +
higher-order relations), and MAC/FAC's stage-1 filter is a **content vector** = a
bag-of-predicate-labels. These emitters give Epic C its input with zero remodeling.
"""

from __future__ import annotations

from collections import Counter

from .schema import ConceptGraph


def to_dgroup(graph: ConceptGraph) -> dict:
    """An SME description group: entities, attributes, relations, higher-order relations."""
    entities = [c.id for c in graph.concepts]
    # attributes = 1-place predicates over a concept (kind/role and salient flags)
    attributes = []
    for c in graph.concepts:
        attributes.append({"pred": c.kind, "arg": c.id})            # e.g. (theorem thm.1)
        attributes.append({"pred": f"role:{c.role}", "arg": c.id})
        if c.attributes.get("x_kind"):
            attributes.append({"pred": str(c.attributes["x_kind"]), "arg": c.id})
    relations, higher = [], []
    for r in graph.relations:
        rec = {"pred": r.predicate, "args": [r.subject, r.object]}
        (higher if r.higher_order else relations).append(rec)
    return {
        "slug": graph.slug,
        "entities": entities,
        "attributes": attributes,
        "relations": relations,
        "higher_order": higher,
    }


def content_vector(graph: ConceptGraph) -> dict[str, int]:
    """MAC stage-1 content vector: bag of predicate labels (attributes + relations)."""
    vec: Counter = Counter()
    for c in graph.concepts:
        vec[f"attr:{c.kind}"] += 1
        vec[f"role:{c.role}"] += 1
    for r in graph.relations:
        vec[f"rel:{r.predicate}"] += 1
    return dict(vec)


def to_ntriples(graph: ConceptGraph, base: str = "op:") -> str:
    """Export relations as N-Triples lines (interop / SHACL); deterministic ordering."""
    def uri(x: str) -> str:
        return f"<{base}{x}>"
    lines = []
    for c in sorted(graph.concepts, key=lambda c: c.id):
        lines.append(f"{uri(c.id)} <{base}kind> \"{c.kind}\" .")
        lines.append(f"{uri(c.id)} <{base}role> \"{c.role}\" .")
    for r in sorted(graph.relations, key=lambda r: (r.subject, r.predicate, r.object)):
        obj = uri(r.object) if r.resolved else f"\"{r.object}\""
        lines.append(f"{uri(r.subject)} <{base}{r.predicate}> {obj} .")
    return "\n".join(lines) + "\n"

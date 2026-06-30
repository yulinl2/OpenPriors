"""Analogical inference transfer (Epic P): use an analogy to *generate conjectures*.

Finding an analogy is not the payoff — *using* it is. In structure-mapping (Gentner 1983) the
power of an analogy is its **candidate inferences**: structure present in the base but not yet
in the target is *projected* across the correspondence as a prediction. This module turns a
discovered cross-domain analogy into named, provenance-tracked **conjectures** about the
target field.

Example: under the analogy ``banach_contraction ~~ weighted_conformal`` (calibration data ↔
contraction map), Banach's ``BANACH_FIXEDPOINT(the_map, the_fixedpoint)`` has no conformal
counterpart, so it projects to the conjecture ``BANACH_FIXEDPOINT(cal_test, ?)`` — *"the
conformal calibration procedure has a fixed point"* — a structural hypothesis no one stated,
produced purely from the analogy. An invented (``skolem:``) entity marks the predicted object
that the target domain has no name for yet.

A conjecture is **confirmed** if its projection already matches a fact the target asserts (the
analogy recovered known structure — a soundness check), else **novel** (a genuine, falsifiable
prediction). Each is scored by how anchored it is to matched structure and how many invented
entities it needs, so the strongest predictions surface first.
"""

from __future__ import annotations

from analogy.align import _funcs_match, _project, _subfacts, align, fmt_expr
from analogy.predicates import Dgroup, args, functor, is_entity

from .model import Edge, Graph, Node


def _is_skolem(e) -> bool:
    return is_entity(e) and str(e).startswith("skolem:")


def _confirms(projection, target_fact, ascension: dict | None) -> bool:
    """Does ``projection`` match an existing ``target_fact``, treating invented (skolem)
    entities as wildcards and functors under the role ascension?"""
    if is_entity(projection):
        # an entity (incl. an invented skolem) can only correspond to a target ENTITY, never
        # to a whole predicate sub-tree -- so a skolem wildcards over entities, not structure
        if not is_entity(target_fact):
            return False
        return _is_skolem(projection) or projection == target_fact
    if isinstance(projection, tuple) and isinstance(target_fact, tuple):
        if not _funcs_match(functor(projection), functor(target_fact), ascension) \
                or len(projection) != len(target_fact):
            return False
        return all(_confirms(p, t, ascension) for p, t in zip(args(projection), args(target_fact)))
    return False


def transfer(base: Dgroup, target: Dgroup, ascension: dict | None = None) -> list[dict]:
    """Project the base's unmatched-but-anchored structure onto the target as conjectures."""
    g = align(base, target, ascension=ascension)
    mapping = g.correspondences
    matched = {repr(e) for e in g.matched_base}

    conjectures = []
    for fact in base.facts:
        if repr(fact) in matched:
            continue
        anchored = sum(1 for s in _subfacts(fact) if repr(s) in matched)
        ent_overlap = len([e for e in _entities(fact) if e in mapping])
        if anchored == 0 and ent_overlap == 0:
            continue                                    # nothing ties it to the analogy
        projection = _project(fact, mapping)
        n_skolems = sum(1 for e in _entities(projection) if _is_skolem(e))
        confirmed = any(_confirms(projection, tf, ascension) for tf in target.facts)
        conjectures.append({
            "base_fact": fmt_expr(fact),
            "projection": fmt_expr(projection),
            "anchored": anchored,
            "entity_overlap": ent_overlap,
            "n_skolems": n_skolems,
            "confidence": round(anchored * 2.0 + ent_overlap - n_skolems, 3),
            "status": "confirmed" if confirmed else "novel",
        })
    return sorted(conjectures, key=lambda c: (-c["confidence"], c["projection"]))


def _entities(e):
    from analogy.predicates import entities
    return entities(e)


def add_conjectures(g: Graph, base: str, target: str, conjectures: list[dict]) -> None:
    """Add each conjecture as a node, linked from the target result by a ``conjectures`` edge
    annotated with the analogy it came from."""
    for i, c in enumerate(conjectures):
        cid = f"conjecture::{target}<~{base}::{i}"
        g.add_node(Node(cid, "conjecture", c["projection"],
                        attrs={"projection": c["projection"], "from_base_fact": c["base_fact"],
                               "source_base": base, "anchored": c["anchored"],
                               "n_skolems": c["n_skolems"], "confidence": c["confidence"],
                               "status": c["status"]},
                        provenance=f"transfer::{base}->{target}"))
        tgt = f"result::{target}"
        if tgt in g.nodes:
            g.add_edge(Edge(tgt, cid, "conjectures",
                            attrs={"source_analogy": base, "status": c["status"],
                                   "confidence": c["confidence"]},
                            provenance=f"transfer::{base}->{target}"))

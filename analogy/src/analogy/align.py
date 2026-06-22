"""SME-style structural alignment (Falkenhainer, Forbus & Gentner 1989, simplified).

Pipeline (see `Imports/structure mapping notes.md` §2):
  1. **Match hypotheses (MHs):** pair a base expression with a target expression when they
     are structurally identical under *identicality* (same functor, same arity, recursively)
     — entity leaves induce *correspondences*.
  2. **Structural consistency:** two MHs conflict if their correspondences violate
     one-to-one (a base entity to two targets, or vice versa).
  3. **Greedy merge:** add MHs deepest-first into a maximal consistent **Gmap**, scoring by
     order (systematicity: deep, interconnected structure scores more).
  4. **Candidate inferences:** unmatched base facts whose sub-structure *is* matched get
     projected onto the target (the trace of "target = base machinery on relabeled objects").

No backtracking, like SME's greedy variant. The result is a global mapping + a structural
evaluation score + scored candidate inferences.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .predicates import Dgroup, args, functor, is_entity, order


@dataclass
class MatchHypothesis:
    base: object
    target: object
    corrs: frozenset  # frozenset[(base_entity, target_entity)]
    order: int


def _match(be, te) -> set | None:
    """Return entity correspondences if be/te are identical under identicality, else None."""
    if is_entity(be) and is_entity(te):
        return {(be, te)}
    if isinstance(be, tuple) and isinstance(te, tuple):
        if functor(be) != functor(te) or len(be) != len(te):
            return None
        corrs: set = set()
        for ba, ta in zip(args(be), args(te)):
            sub = _match(ba, ta)
            if sub is None:
                return None
            corrs |= sub
        return corrs
    return None  # entity vs predicate => incompatible (identicality)


def match_hypotheses(base: Dgroup, target: Dgroup) -> list[MatchHypothesis]:
    mhs = []
    for be in base.facts:
        for te in target.facts:
            corrs = _match(be, te)
            if corrs is not None:
                mhs.append(MatchHypothesis(be, te, frozenset(corrs), order(be)))
    return mhs


def _consistent(corrs: set, new: frozenset) -> bool:
    b2t = {b: t for b, t in corrs}
    t2b = {t: b for b, t in corrs}
    for b, t in new:
        if b in b2t and b2t[b] != t:
            return False
        if t in t2b and t2b[t] != b:
            return False
    return True


@dataclass
class Gmap:
    correspondences: dict          # base_entity -> target_entity
    matched_base: list             # matched base expressions
    matched_target: list           # matched target expressions
    score: float
    candidate_inferences: list = field(default_factory=list)


def _project(expr, mapping: dict):
    """Substitute base entities by their target images; unmapped -> skolem:<name>."""
    if is_entity(expr):
        return mapping.get(expr, f"skolem:{expr}")
    return (functor(expr),) + tuple(_project(a, mapping) for a in args(expr))


def align(base: Dgroup, target: Dgroup) -> Gmap:
    mhs = sorted(match_hypotheses(base, target), key=lambda m: -m.order)  # deep first
    corrs: set = set()
    matched_b, matched_t, score = [], [], 0.0
    for mh in mhs:
        if _consistent(corrs, mh.corrs):
            corrs |= set(mh.corrs)
            matched_b.append(mh.base)
            matched_t.append(mh.target)
            score += 1.0 + mh.order            # systematicity weight: deeper => more
    mapping = {b: t for b, t in corrs}

    # candidate inferences: unmatched base facts anchored to the matched structure
    matched_set = {repr(e) for e in matched_b}
    inferences = []
    for fact in base.facts:
        if repr(fact) in matched_set:
            continue
        anchored = sum(1 for s in _subfacts(fact) if repr(s) in matched_set)
        ent_overlap = len([e for e in _ent(fact) if e in mapping])
        if anchored > 0 or ent_overlap > 0:
            inferences.append({
                "base_fact": _fmt(fact),
                "projection": _fmt(_project(fact, mapping)),
                "anchored_submatches": anchored,
                "entity_overlap": ent_overlap,
                "score": round(anchored * 2.0 + ent_overlap, 3),
            })
    inferences.sort(key=lambda d: -d["score"])
    return Gmap(mapping, matched_b, matched_t, round(score, 3), inferences)


def _subfacts(e):
    from .predicates import subexprs
    return [s for s in subexprs(e) if isinstance(s, tuple) and s is not e]


def _ent(e):
    from .predicates import entities
    return entities(e)


def fmt_expr(e) -> str:
    """Public, human-readable formatter for a predicate-calculus expression."""
    if is_entity(e):
        return e
    return f"{functor(e)}(" + ", ".join(fmt_expr(a) for a in args(e)) + ")"


_fmt = fmt_expr  # internal alias (kept for existing call sites)

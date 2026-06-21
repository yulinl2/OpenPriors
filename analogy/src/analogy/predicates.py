"""Typed predicate-calculus expressions for structure mapping (SME's input form).

An **expression** is either:
  * an **entity** — a ``str`` (e.g. ``"sun"``), order 0; or
  * a **predicate application** — a ``tuple`` ``(functor, arg1, ...)`` whose args are
    themselves expressions. 1-place predicates are *attributes*, n-place are *relations*,
    and predicates whose args are predicates are *higher-order relations* (e.g. ``CAUSE``).

The **order** of an expression is ``1 + max(order(arg))`` (entities = 0); higher order =
deeper relational structure, which is what SME's systematicity principle rewards.

A :class:`Dgroup` (description group) is a named set of top-level expressions — the unit
SME aligns. This mirrors ``concept_graph.sme.to_dgroup`` so corpus graphs feed in directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

Expr = object  # str (entity) | tuple(functor, *Expr)


def is_entity(e: Expr) -> bool:
    return isinstance(e, str)


def functor(e: Expr) -> str | None:
    return e[0] if isinstance(e, tuple) else None


def args(e: Expr) -> tuple:
    return e[1:] if isinstance(e, tuple) else ()


def order(e: Expr) -> int:
    if is_entity(e):
        return 0
    return 1 + max((order(a) for a in args(e)), default=0)


def entities(e: Expr) -> set[str]:
    if is_entity(e):
        return {e}
    out: set[str] = set()
    for a in args(e):
        out |= entities(a)
    return out


def subexprs(e: Expr) -> list[Expr]:
    """All sub-expressions (including ``e`` itself), predicates only at depth>0 too."""
    out = [e]
    for a in args(e):
        if isinstance(a, tuple):
            out.extend(subexprs(a))
    return out


@dataclass
class Dgroup:
    name: str
    facts: list  # list[Expr] top-level expressions

    def all_exprs(self) -> list:
        out: list = []
        for f in self.facts:
            out.extend(subexprs(f))
        return out

    def entities(self) -> set[str]:
        out: set[str] = set()
        for f in self.facts:
            out |= entities(f)
        return out

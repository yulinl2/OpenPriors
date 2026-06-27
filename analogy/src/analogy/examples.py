"""Classic structure-mapping fixtures + a loader from concept_graph dgroups.

The solar-system -> atom analogy (Gentner 1983) is the canonical SME test with a *known*
correct mapping (sun->nucleus, planet->electron), so it serves as ground truth for the
aligner's verification.
"""

from __future__ import annotations

import json
from pathlib import Path

from .predicates import Dgroup


def solar_system() -> Dgroup:
    return Dgroup("solar-system", [
        ("GREATER", ("MASS", "sun"), ("MASS", "planet")),
        ("ATTRACTS", "sun", "planet"),
        ("REVOLVES", "planet", "sun"),
        ("CAUSE",
         ("AND",
          ("GREATER", ("MASS", "sun"), ("MASS", "planet")),
          ("ATTRACTS", "sun", "planet")),
         ("REVOLVES", "planet", "sun")),
        ("GREATER", ("TEMPERATURE", "sun"), ("TEMPERATURE", "planet")),  # distractor
    ])


def atom() -> Dgroup:
    return Dgroup("rutherford-atom", [
        ("GREATER", ("MASS", "nucleus"), ("MASS", "electron")),
        ("ATTRACTS", "nucleus", "electron"),
        ("REVOLVES", "electron", "nucleus"),
    ])


# --------------------------------------------------------------------------- #
# Minimal-ascension demo: near-synonym predicates align via a type lattice.    #
# --------------------------------------------------------------------------- #
DEFAULT_ASCENSION = {
    # objective operators
    "MINIMIZE": "OBJECTIVE_OP", "MAXIMIZE": "OBJECTIVE_OP", "OPTIMIZE": "OBJECTIVE_OP",
    # monotone changes
    "DECREASES": "MONOTONE", "INCREASES": "MONOTONE", "CHANGES": "MONOTONE",
}


def synonym_base() -> Dgroup:
    """An optimizer description phrased with MINIMIZE / DECREASES."""
    return Dgroup("optimizer-A", [
        ("OBJECTIVE", "loss"),
        ("MINIMIZE", "agent", "loss"),
        ("CAUSE", ("MINIMIZE", "agent", "loss"), ("DECREASES", "loss", "time")),
    ])


def synonym_target() -> Dgroup:
    """The same structure phrased with the near-synonyms OPTIMIZE / CHANGES."""
    return Dgroup("optimizer-B", [
        ("OBJECTIVE", "cost"),
        ("OPTIMIZE", "system", "cost"),
        ("CAUSE", ("OPTIMIZE", "system", "cost"), ("CHANGES", "cost", "step")),
    ])


# --------------------------------------------------------------------------- #
# Trickle-down systematicity demo: a deep relational web vs the same relations  #
# in isolation. Trickle-down evidence should reward the former disproportionately.
# --------------------------------------------------------------------------- #
def _orbit(a: str, b: str, with_cause: bool):
    facts = [
        ("GREATER", ("MASS", a), ("MASS", b)),
        ("ATTRACTS", a, b),
        ("REVOLVES", b, a),
    ]
    if with_cause:
        facts.append(("CAUSE",
                      ("AND", ("GREATER", ("MASS", a), ("MASS", b)), ("ATTRACTS", a, b)),
                      ("REVOLVES", b, a)))
    return facts


def systematic_pair():
    """Base & target share a deep CAUSE over the relations (a systematic web)."""
    return (Dgroup("sys-A", _orbit("a", "b", with_cause=True)),
            Dgroup("sys-B", _orbit("c", "d", with_cause=True)))


def flat_pair():
    """The same relations with NO higher-order CAUSE tying them together."""
    return (Dgroup("flat-A", _orbit("a", "b", with_cause=False)),
            Dgroup("flat-B", _orbit("c", "d", with_cause=False)))


def from_concept_dgroup(path: str | Path) -> Dgroup:
    """Build a Dgroup from a concept_graph ``dgroup.json``.

    Faithfully includes all three predicate kinds the SME bridge emits: 1-place
    ``attributes``, and ``relations`` / ``higher_order`` of arbitrary arity.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    facts: list = []
    for a in data.get("attributes", []):           # 1-place predicates
        facts.append((a["pred"], a["arg"]))
    for r in data.get("relations", []) + data.get("higher_order", []):
        facts.append((r["pred"], *r.get("args", [])))  # arbitrary arity
    return Dgroup(data.get("slug", "dgroup"), facts)

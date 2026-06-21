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

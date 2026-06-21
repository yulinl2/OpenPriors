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
    """Build a Dgroup from a concept_graph ``dgroup.json`` (relations + higher_order)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    facts = []
    for r in data.get("relations", []) + data.get("higher_order", []):
        a = r.get("args", [])
        if len(a) == 2:
            facts.append((r["pred"], a[0], a[1]))
    return Dgroup(data.get("slug", "dgroup"), facts)

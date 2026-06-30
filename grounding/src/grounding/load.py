"""Load grounded prose dgroups (sub-agent output) into analogy ``Dgroup`` objects.

The sub-agent produced the JSON in ``grounding/dgroups/``; this module is the deterministic
side: it parses that JSON, so CI exercises the loader + grounding check + solver without any
LLM call. ``analogy`` must be importable (wire ``PYTHONPATH=grounding/src:analogy/src``).
"""

from __future__ import annotations

import json
from pathlib import Path

from analogy.predicates import Dgroup


def expr_from_json(node):
    """JSON nested array -> predicate-calculus expression (entity str | tuple)."""
    if isinstance(node, str):
        return node
    if isinstance(node, list) and node:
        return (node[0],) + tuple(expr_from_json(x) for x in node[1:])
    raise ValueError(f"bad expression node: {node!r}")


def entities_in_facts(facts) -> set[str]:
    """Leaf entities (args), excluding functors (the first element of each application)."""
    out: set[str] = set()

    def walk(node, is_functor_pos=False):
        if isinstance(node, str):
            if not is_functor_pos:
                out.add(node)
            return
        if isinstance(node, list) and node:
            for i, x in enumerate(node):
                walk(x, is_functor_pos=(i == 0))

    for f in facts:
        walk(f, is_functor_pos=False)
    return out


def load_riddles(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out = {}
    for key, r in data.items():
        if key.startswith("_"):
            continue
        out[key] = {
            "source": Dgroup(f"{key}-source", [expr_from_json(f) for f in r["source"]["facts"]]),
            "target": Dgroup(f"{key}-target", [expr_from_json(f) for f in r["target"]["facts"]]),
            "raw": r,
        }
    return out

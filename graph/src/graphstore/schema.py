"""A formal schema for the unified graph (Epic X): make the end-goal artifact rigorous.

The decomposer emits a JSON Schema for its outputs (a project doctrine: reproducible,
externally auditable, machine-checkable). The unified graph — the end-goal package — should
too. This module is the contract for ``nodes.jsonl`` + ``edges.jsonl``:

  * ``json_schema()`` returns a draft-2020-12 JSON Schema document (for external consumers /
    ``jsonschema``); ``emit`` writes it to ``graph/schema/``;
  * ``validate(graph)`` is the in-repo, dependency-free checker. It enforces everything the
    JSON Schema does (node kinds, required per-kind attrs, the relation vocabulary) PLUS the
    two things a per-record JSON Schema cannot express: **referential integrity** (every edge
    endpoint is a real node) and **arg-edge well-formedness** (a fact's ``arg:i`` edges are a
    contiguous 0..n-1 with no gaps), so a graph that validates is genuinely well-formed.

Like ``grounding.verify``, the validator is unit-tested to FAIL on broken input, so the
contract can't silently rot.
"""

from __future__ import annotations

import json
import re

NODE_KINDS = ("entity", "fact", "functor", "result", "conjecture")
# required attribute keys per node kind (others are allowed/optional)
REQUIRED_ATTRS = {
    "entity": {"grounding": str},
    "fact": {"functor": str, "arity": int},
    "functor": {},
    "result": {"text": str, "n_facts": int},
    "conjecture": {"projection": str, "source_base": str, "status": str},
}
NAMED_RELATIONS = ("instance_of", "asserts", "in", "extends", "analogous_to", "conjectures")
_ARG_RE = re.compile(r"^arg:(\d+)$")


def _relation_ok(rel: str) -> bool:
    return rel in NAMED_RELATIONS or bool(_ARG_RE.match(rel))


def validate(graph) -> dict:
    """Structural + referential validation. Returns {'ok': bool, 'errors': [...]}.

    A validator must never crash on the malformed input it exists to catch, so every field is
    type-checked defensively before use. Integer fields use a strict check that rejects
    booleans, matching the emitted schema's ``type: integer`` (JSON has no bool-is-int)."""
    errors: list[str] = []

    def _is_int(v) -> bool:
        return isinstance(v, int) and not isinstance(v, bool)

    for nid, n in graph.nodes.items():
        if n.kind not in NODE_KINDS:
            errors.append(f"node {nid!r}: unknown kind {n.kind!r}")
        if not isinstance(n.label, str) or not n.label:
            errors.append(f"node {nid!r}: label must be a non-empty string")
        if not isinstance(n.provenance, str):
            errors.append(f"node {nid!r}: provenance must be a string")
        if not isinstance(n.attrs, dict):
            errors.append(f"node {nid!r}: attrs must be an object")
        else:
            for key, typ in REQUIRED_ATTRS.get(n.kind, {}).items():
                if key not in n.attrs:
                    errors.append(f"node {nid!r} ({n.kind}): missing required attr {key!r}")
                elif not (_is_int(n.attrs[key]) if typ is int else isinstance(n.attrs[key], typ)):
                    errors.append(f"node {nid!r}: attr {key!r} must be {typ.__name__}")

    for e in graph.edges:
        if not isinstance(e.relation, str) or not _relation_ok(e.relation):
            errors.append(f"edge {e.key()}: unknown or non-string relation {e.relation!r}")
        if not isinstance(e.attrs, dict):
            errors.append(f"edge {e.key()}: attrs must be an object")
        if not isinstance(e.provenance, str):
            errors.append(f"edge {e.key()}: provenance must be a string")
        if e.src not in graph.nodes:
            errors.append(f"edge {e.key()}: src {e.src!r} is not a node")        # referential
        if e.dst not in graph.nodes:
            errors.append(f"edge {e.key()}: dst {e.dst!r} is not a node")        # integrity

    # arg-edge well-formedness: a fact's arg:i indices must be exactly 0..arity-1 (the declared
    # arity). Falls back to a contiguity check only when arity itself is invalid (already flagged).
    for nid, n in graph.nodes.items():
        if n.kind != "fact":
            continue
        idxs = sorted(int(m.group(1)) for e in graph.out_edges(nid)
                      if isinstance(e.relation, str) and (m := _ARG_RE.match(e.relation)))
        arity = n.attrs.get("arity") if isinstance(n.attrs, dict) else None
        if _is_int(arity):
            if idxs != list(range(arity)):
                errors.append(f"fact {nid!r}: arg indices {idxs} != 0..{arity - 1} (declared arity)")
        elif idxs and idxs != list(range(len(idxs))):
            errors.append(f"fact {nid!r}: arg indices not contiguous from 0: {idxs}")

    return {"ok": not errors, "errors": errors, "n_nodes": len(graph.nodes),
            "n_edges": len(graph.edges)}


def json_schema() -> dict:
    """A draft-2020-12 JSON Schema for a single node or edge record (one JSONL line)."""
    node_branches = []
    for kind in NODE_KINDS:
        req = REQUIRED_ATTRS[kind]
        node_branches.append({
            "properties": {
                "kind": {"const": kind},
                "attrs": {
                    "type": "object",
                    "required": sorted(req),
                    "properties": {k: {"type": {int: "integer", str: "string"}[t]}
                                   for k, t in req.items()},
                },
            },
        })
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "OpenPriors unified-graph record",
        "oneOf": [
            {
                "title": "node",
                "type": "object",
                "required": ["id", "kind", "label", "attrs", "provenance"],
                "properties": {
                    "id": {"type": "string"},
                    "kind": {"enum": list(NODE_KINDS)},
                    "label": {"type": "string", "minLength": 1},
                    "attrs": {"type": "object"},
                    "provenance": {"type": "string"},
                },
                "allOf": [{"if": {"properties": {"kind": {"const": k}}},
                           "then": b} for (k, b) in zip(NODE_KINDS, node_branches)],
            },
            {
                "title": "edge",
                "type": "object",
                "required": ["src", "dst", "relation", "attrs", "provenance"],
                "properties": {
                    "src": {"type": "string"},
                    "dst": {"type": "string"},
                    "relation": {"oneOf": [{"enum": list(NAMED_RELATIONS)},
                                           {"pattern": r"^arg:\d+$"}], "type": "string"},
                    "attrs": {"type": "object"},
                    "provenance": {"type": "string"},
                },
            },
        ],
    }


def emit(schema_dir) -> None:
    schema_dir.mkdir(parents=True, exist_ok=True)
    (schema_dir / "graph.schema.json").write_text(
        json.dumps(json_schema(), sort_keys=True, indent=2) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    from pathlib import Path

    from .pipeline import run_pipeline

    here = Path(__file__).resolve().parents[2]
    repo = here.parent
    g = run_pipeline(repo)["graph"]
    emit(here / "schema")
    res = validate(g)

    print(f"unified-graph schema: emitted graph/schema/graph.schema.json")
    print(f"  validated the capstone graph: {res['n_nodes']} nodes, {res['n_edges']} edges "
          f"-> {'OK' if res['ok'] else 'INVALID'}")
    if not res["ok"]:
        for e in res["errors"][:10]:
            print(f"    - {e}")

    # the emitted schema must not drift from the validator's required-attrs (CI gate, -O safe)
    branch = {b["title"]: b for b in json_schema()["oneOf"]}
    node_ifthen = branch["node"]["allOf"]
    schema_req = {clause["if"]["properties"]["kind"]["const"]:
                  set(clause["then"]["properties"]["attrs"]["required"]) for clause in node_ifthen}
    drift = {k for k in REQUIRED_ATTRS if set(REQUIRED_ATTRS[k]) != schema_req.get(k, set())}
    if not res["ok"]:
        raise SystemExit(f"capstone graph does not satisfy its own schema: {res['errors'][:5]}")
    if drift:
        raise SystemExit(f"emitted JSON Schema drifted from the validator for kinds: {drift}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

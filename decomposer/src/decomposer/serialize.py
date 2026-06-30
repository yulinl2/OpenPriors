"""Canonical, diff-friendly serialization (the "易audit" property).

Emits three synchronized views of one :class:`Decomposition`:

* ``document.json``  — the nested **tree** (source of truth for humans).
* ``nodes.jsonl``    — the flat **node** stream (one object per line).
* ``edges.jsonl``    — the flat **edge** stream (one relation per line).

All output uses sorted keys, ``ensure_ascii=False`` and ``\\n`` line endings so that
re-running the pipeline on unchanged input yields a byte-identical file => minimal,
meaningful git diffs.
"""

from __future__ import annotations

import json
from pathlib import Path

from .schema import Decomposition, Edge, Node


def canonical_json(obj) -> str:
    """RFC-8785-flavoured canonical JSON (sorted keys, compact-but-readable)."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=2)


def _node_payload(node: Node) -> dict:
    """Flat dict for a node (children dropped); ``None``/empty fields pruned."""
    d = node.flat().model_dump(exclude_none=True)
    d.pop("children", None)
    return d


def write_bundle(decomp: Decomposition, out_dir: str | Path) -> dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # 1. nested tree
    doc_json = canonical_json(decomp.model_dump(exclude_none=True))
    (out / "document.json").write_text(doc_json + "\n", encoding="utf-8")

    # 2. flat node stream (stable order: pre-order DFS == reading order)
    nodes = decomp.all_nodes()
    with (out / "nodes.jsonl").open("w", encoding="utf-8") as fh:
        for n in nodes:
            fh.write(json.dumps(_node_payload(n), sort_keys=True, ensure_ascii=False) + "\n")

    # 3. flat edge stream
    with (out / "edges.jsonl").open("w", encoding="utf-8") as fh:
        for e in decomp.edges:
            fh.write(json.dumps(e.model_dump(exclude_none=True), sort_keys=True, ensure_ascii=False) + "\n")

    # 4. metrics sidecar
    (out / "metrics.json").write_text(canonical_json(decomp.metrics) + "\n", encoding="utf-8")

    return {
        "document": str(out / "document.json"),
        "nodes": str(out / "nodes.jsonl"),
        "edges": str(out / "edges.jsonl"),
        "metrics": str(out / "metrics.json"),
    }


def write_json_schema(out_path: str | Path) -> str:
    """Emit the JSON Schema of the whole bundle for external audit."""
    schema = Decomposition.model_json_schema()
    Path(out_path).write_text(canonical_json(schema) + "\n", encoding="utf-8")
    return str(out_path)


def load_bundle(path: str | Path) -> Decomposition:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Decomposition.model_validate(data)

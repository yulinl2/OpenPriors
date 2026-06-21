"""CLI: build concept graphs from the decomposer's run outputs.

Reads ``decomposer/runs/<slug>/step-30-structure/{nodes,edges}.jsonl`` (the on-disk
contract between Epic A and Epic B) and writes, per document, the OAR graph in several
synchronized views + an independent verification report.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import sme, verify
from .build import _load_jsonl, build_from_run


def _canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=2)


def _jsonl(path: Path, rows) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")


def build_one(slug: str, structure_dir: Path, out_dir: Path) -> dict:
    g = build_from_run(structure_dir, slug)
    edges = _load_jsonl(structure_dir / "edges.jsonl")
    results = verify.run_all(g, edges)
    report = {"checks": [r.model_dump() for r in results],
              "all_passed": all(r.passed for r in results)}

    out_dir.mkdir(parents=True, exist_ok=True)
    _jsonl(out_dir / "concepts.jsonl", (c.model_dump(exclude_none=True) for c in g.concepts))
    _jsonl(out_dir / "relations.jsonl", (r.model_dump(exclude_none=True) for r in g.relations))
    _jsonl(out_dir / "triples.jsonl", (t.model_dump() for t in g.triples()))
    (out_dir / "graph.json").write_text(_canon(g.model_dump(exclude_none=True)) + "\n", encoding="utf-8")
    (out_dir / "dgroup.json").write_text(_canon(sme.to_dgroup(g)) + "\n", encoding="utf-8")
    (out_dir / "content_vector.json").write_text(_canon(sme.content_vector(g)) + "\n", encoding="utf-8")
    (out_dir / "graph.nt").write_text(sme.to_ntriples(g), encoding="utf-8")
    (out_dir / "metrics.json").write_text(_canon(g.metrics) + "\n", encoding="utf-8")
    (out_dir / "verification.json").write_text(_canon(report) + "\n", encoding="utf-8")
    g.metrics["verification"] = {"all_passed": report["all_passed"],
                                 "checks": {r.name: r.passed for r in results}}
    return g.metrics


def main(argv=None) -> int:
    here = Path(__file__).resolve().parents[2]
    repo = here.parent
    ap = argparse.ArgumentParser(prog="concept-graph", description=__doc__)
    ap.add_argument("--runs", default=str(repo / "decomposer" / "runs"),
                    help="decomposer runs dir")
    ap.add_argument("--out", default=str(here / "graphs"))
    args = ap.parse_args(argv)

    runs = Path(args.runs)
    out_root = Path(args.out)
    summary, ok = {}, True
    for struct in sorted(runs.glob("*/step-30-structure")):
        slug = struct.parent.name
        m = build_one(slug, struct, out_root / slug)
        summary[slug] = m
        v = m["verification"]["all_passed"]
        ok = ok and v
        print(f"[{'✓' if v else '✗'}] {slug}: {m['n_concepts']} concepts, "
              f"{m['n_relations']} relations ({m['n_reasoning_edges']} reasoning), "
              f"verify={'PASS' if v else 'FAIL'}")
    (out_root / "summary.json").write_text(_canon(summary) + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

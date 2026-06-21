"""CLI: ``decompose`` — run the workflow over the corpus and emit the JSON Schema."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .pipeline import run_all_docs
from .serialize import write_json_schema


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="decompose", description=__doc__)
    here = Path(__file__).resolve().parents[2]
    ap.add_argument("--corpus", default=str(here / "corpus"))
    ap.add_argument("--runs", default=str(here / "runs"))
    ap.add_argument("--schema", default=str(here / "docs" / "schema.json"))
    args = ap.parse_args(argv)

    write_json_schema(args.schema)
    summary = run_all_docs(Path(args.corpus), Path(args.runs))
    ok = True
    for slug, m in summary.items():
        v = m.get("verification", {}).get("all_passed")
        ok = ok and bool(v)
        print(f"[{ '✓' if v else '✗' }] {slug}: {m['n_nodes']} nodes, "
              f"{m['n_edges']} edges, classified={m['classified_ratio']}, "
              f"verification={'PASS' if v else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

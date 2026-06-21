"""CLI: MAC retrieval + renaming-invariance + systematicity over the concept graphs.

Reads ``concept_graph/graphs/<slug>/graph.json`` (the Epic B output), then writes a
similarity matrix, per-document invariance reports, and systematicity scores.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from concept_graph.schema import ConceptGraph

from . import invariance, mac


def _canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=2)


def load_graphs(graphs_dir: Path) -> dict[str, ConceptGraph]:
    out = {}
    for gj in sorted(graphs_dir.glob("*/graph.json")):
        data = json.loads(gj.read_text(encoding="utf-8"))
        out[data["slug"]] = ConceptGraph.model_validate(data)
    return out


def main(argv=None) -> int:
    here = Path(__file__).resolve().parents[2]
    repo = here.parent
    ap = argparse.ArgumentParser(prog="matcher", description=__doc__)
    ap.add_argument("--graphs", default=str(repo / "concept_graph" / "graphs"))
    ap.add_argument("--out", default=str(here / "results"))
    args = ap.parse_args(argv)

    graphs = load_graphs(Path(args.graphs))
    if not graphs:
        print("no concept graphs found; run concept_graph first", file=sys.stderr)
        return 2
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    from concept_graph.sme import content_vector
    vectors = {slug: content_vector(g) for slug, g in graphs.items()}
    sim = mac.similarity_matrix(vectors)
    (out / "similarity_matrix.json").write_text(_canon(sim) + "\n", encoding="utf-8")

    inv = {slug: invariance.check_renaming_invariance(g) for slug, g in graphs.items()}
    (out / "invariance.json").write_text(_canon(inv) + "\n", encoding="utf-8")

    syst = {slug: invariance.systematicity(g) for slug, g in graphs.items()}
    (out / "systematicity.json").write_text(_canon(syst) + "\n", encoding="utf-8")

    all_invariant = all(v["passed"] for v in inv.values())
    for slug in sorted(graphs):
        s = syst[slug]
        print(f"[{'✓' if inv[slug]['passed'] else '✗'}] {slug}: "
              f"renaming-invariant={inv[slug]['passed']}, "
              f"systematicity={s['systematicity_score']} "
              f"(depth {s['max_reasoning_depth']}, {s['n_higher_order_relations']} HO rels)")
    print("renaming-invariance holds for all graphs:", all_invariant)
    return 0 if all_invariant else 1


if __name__ == "__main__":
    sys.exit(main())

"""CLI: run the SME aligner on the classic solar->atom analogy and (optionally) on a pair
of corpus concept-graph dgroups."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import examples, novelty
from .align import align


def _canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=2)


def run_classic() -> dict:
    base, target = examples.solar_system(), examples.atom()
    g = align(base, target)
    rep = novelty.novelty_report(base, target, g)
    return {
        "base": base.name, "target": target.name,
        "mapping": g.correspondences,
        "structural_score": g.score,
        "candidate_inferences": g.candidate_inferences,
        "novelty": rep,
    }


def main(argv=None) -> int:
    here = Path(__file__).resolve().parents[2]
    repo = here.parent
    ap = argparse.ArgumentParser(prog="analogy", description=__doc__)
    ap.add_argument("--base", help="path to a concept_graph dgroup.json (base)")
    ap.add_argument("--target", help="path to a concept_graph dgroup.json (target)")
    ap.add_argument("--out", default=str(here / "results"))
    args = ap.parse_args(argv)

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    classic = run_classic()
    (out / "solar_atom.json").write_text(_canon(classic) + "\n", encoding="utf-8")
    print(f"[classic] solar-system -> atom: mapping={classic['mapping']}")
    print(f"          structural_score={classic['structural_score']}, "
          f"top_inference={classic['novelty']['top_inference']}")
    print(f"          target_coverage={classic['novelty']['target_coverage']}, "
          f"novelty={classic['novelty']['novelty_score']}, "
          f"shortcut={classic['novelty']['shortcut_signal']}")

    if args.base and args.target:
        b = examples.from_concept_dgroup(args.base)
        t = examples.from_concept_dgroup(args.target)
        g = align(b, t)
        rep = novelty.novelty_report(b, t, g)
        corpus = {"base": b.name, "target": t.name, "mapping_size": len(g.correspondences),
                  "structural_score": g.score, "novelty": rep}
        (out / "corpus_pair.json").write_text(_canon(corpus) + "\n", encoding="utf-8")
        print(f"[corpus] {b.name} -> {t.name}: mapping_size={len(g.correspondences)}, "
              f"score={g.score}, coverage={rep['target_coverage']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

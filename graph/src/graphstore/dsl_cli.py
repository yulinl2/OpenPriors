"""Demonstrate the query DSL over the unified pipeline graph (Epic S)."""

from __future__ import annotations

from pathlib import Path

from .dsl import (conjectures_with_verdicts, explain_analogy, fmt_path, find,
                  shared_ancestor, shortest_path)
from .pipeline import run_pipeline


def main(argv=None) -> int:
    here = Path(__file__).resolve().parents[2]
    repo = here.parent
    g = run_pipeline(repo)["graph"]

    print("Q: how is the conformal base theorem connected to a learning-theory result?")
    p = shortest_path(g, "result::split_conformal", "result::vc_generalization")
    print(f"   {fmt_path(p)}")
    print("   -> a lineage edge into an analogy edge: the literatures are concretely linked\n")

    print("Q: what is the shared ancestor of the arXiv paper and split conformal?")
    print(f"   {shared_ancestor(g, 'arxiv-2006.06138-main', 'split_conformal')}\n")

    print("Q: why are weighted conformal and Banach contraction analogous?")
    ex = explain_analogy(g, "weighted_conformal", "banach_contraction")
    print(f"   score {ex['score']}; correspondence {ex['correspondences']}\n")

    print("Q: what did the weighted-conformal analogies predict, and how were they judged?")
    for c in conjectures_with_verdicts(g, "banach_contraction")[:4]:
        v = c["verdict"] or "(unjudged)"
        print(f"   [{v:11s}] {c['projection']}  (from {c['from_base']})")
    print()

    print("Q: find every node mentioning 'fixed' (the conjectured fixed points)")
    for nid in find(g, "FIXEDPOINT"):
        print(f"   {nid}")

    # invariants (CI gate; explicit raise so it holds under `python -O`)
    checks = [
        (p and p[-1]["to"] == "result::vc_generalization" and any(
            s["relation"] == "analogous_to" for s in p),
         "the cross-literature path must traverse an analogy edge"),
        (shared_ancestor(g, "arxiv-2006.06138-main", "split_conformal") == "split_conformal",
         "split_conformal must be the shared ancestor on the conformal lineage"),
        (explain_analogy(g, "weighted_conformal", "banach_contraction")["correspondences"].get(
            "cal_test") == "the_map",
         "the analogy explanation must expose the cal_test <-> the_map correspondence"),
        (any(c["verdict"] == "plausible" for c in conjectures_with_verdicts(g, "weighted_conformal")),
         "weighted_conformal must carry a plausible-judged conjecture"),
        (shortest_path(g, "result::split_conformal", "missing::x") is None,
         "a path to a non-existent node is None, not an error"),
    ]
    for ok, msg in checks:
        if not ok:
            raise SystemExit(f"dsl invariant violated: {msg}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

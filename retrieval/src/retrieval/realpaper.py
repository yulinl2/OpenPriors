"""Real published paper, end-to-end (Epic K): the full pipeline on arXiv 2006.06138.

Runs the whole retrieval stack against a genuine published result — Lei & Candes,
*Conformal Inference of Counterfactuals and Individual Treatment Effects* (arXiv 2006.06138)
— whose main theorem has been lifted from prose into a grounded dgroup
(``grounding/dgroups/arxiv_2006_06138_main.json``).

  1. MAC ranks the conformal-prediction library and short-lists the nearest prior;
  2. FAC aligns the paper against each and quantifies reuse vs novelty;
  3. set-cover decomposition explains the paper as {weighted_conformal} + a residual.

The residual — COUNTERFACTUAL + NESTED — is exactly the paper's contribution over weighted
conformal prediction: applying it to counterfactual outcomes and the individual treatment
effect. The system isolates that novel content from the borrowed machinery, automatically.
"""

from __future__ import annotations

import json
from pathlib import Path

from analogy.predicates import Dgroup

from .decompose import decompose
from .engine import expr_from_json, load_library, retrieve


def run(argv=None) -> dict:
    here = Path(__file__).resolve().parents[2]
    repo = here.parent
    library = load_library(here / "library" / "conformal_theorems.json")
    paper_data = json.loads(
        (repo / "grounding" / "dgroups" / "arxiv_2006_06138_main.json").read_text()
    )["target"]
    paper = Dgroup(paper_data["name"], [expr_from_json(f) for f in paper_data["facts"]])

    ret = retrieve(paper, library, mac_k=len(library))
    dec = decompose(paper, library)
    return {"retrieve": ret, "decompose": dec}


def main(argv=None) -> int:
    res = run(argv)
    ret, dec = res["retrieve"], res["decompose"]
    here = Path(__file__).resolve().parents[2]
    out = here / "results"
    out.mkdir(parents=True, exist_ok=True)
    (out / "real_paper.json").write_text(
        json.dumps(res, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    mac = ", ".join(f"{n} {round(s, 3)}" for n, s in ret["mac_ranking"])
    print(f"paper '{dec['target']}' ({dec['n_facts']} facts) — arXiv 2006.06138")
    print(f"  MAC ranking: {mac}")
    print(f"  nearest prior: {ret['nearest_prior']} (novelty {ret['nearest_novelty']})")
    print(f"  verdict: {ret['verdict']}")
    print(f"  = composition of known theorems: {', '.join(dec['covering_priors'])}")
    print(f"  covered {dec['covered_facts']}/{dec['n_facts']} ({dec['coverage_fraction']})")
    print(f"  novel contributions (residual): {', '.join(dec['novel_contributions'])}")

    # sanity: the residual must be the paper's actual contribution, not borrowed machinery.
    # Explicit raise (not assert) so the CI gate holds even under `python -O`.
    novel = dec["novel_contributions"]
    for ok, msg in [
        (ret["nearest_prior"] == "weighted_conformal", f"nearest prior is {ret['nearest_prior']}"),
        (any(s.startswith("COUNTERFACTUAL") for s in novel), f"no COUNTERFACTUAL residual: {novel}"),
        (any(s.startswith("NESTED") for s in novel), f"no NESTED residual: {novel}"),
    ]:
        if not ok:
            raise SystemExit(f"real-paper invariant violated: {msg}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

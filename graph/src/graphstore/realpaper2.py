"""Second real paper end-to-end (Epic V): Nesterov's accelerated gradient method.

Parallels Epic K (arXiv 2006.06138) in a different field — optimization — to show the
real-paper pipeline is not curated to one example. Nesterov's main result (Nesterov 1983) is
lifted from prose into a grounded dgroup by an in-session sub-agent, then:

  1. **decomposed** (set cover) against the optimization priors it builds on
     (``retrieval/library/nesterov_priors.json``) — the residual is the paper's contribution;
  2. **situated cross-domain** — its structural property (the momentum step) is discovered to
     play the same ``PC/2`` role as contraction / weighted-exchangeability / etc., so the
     paper joins the four-literature analogy web.

The residual after covering is ``OPTIMAL_RATE`` (the optimal, quadratically-faster rate) — the
genuine contribution over plain gradient descent — while the estimate-sequence machinery that
builds the momentum is read as borrowed. And *"Nesterov's momentum is to its accelerated
convergence as a contraction is to linear convergence"* falls out automatically.
"""

from __future__ import annotations

import json
from pathlib import Path

from analogy.predicates import Dgroup
from retrieval.decompose import decompose
from retrieval.engine import expr_from_json, load_library

from .crossdomain import _load_corpus, cross_domain_analogies, discover_role_ascension


def run(repo: Path) -> dict:
    paper = json.loads(
        (repo / "grounding" / "dgroups" / "nesterov_paper.json").read_text())["target"]
    target = Dgroup(paper["name"], [expr_from_json(f) for f in paper["facts"]])

    priors = load_library(repo / "retrieval" / "library" / "nesterov_priors.json")
    dec = decompose(target, priors)

    # cross-domain: does Nesterov's structural property join the analogy web?
    conf, _, _ = _load_corpus(repo / "retrieval" / "library" / "conformal_theorems.json")
    opt, _, _ = _load_corpus(repo / "grounding" / "dgroups" / "optimization_corpus.json")
    nest = {paper["name"]: target}
    ascension = discover_role_ascension(conf, opt, nest)
    analogies = cross_domain_analogies(nest, opt, ascension=ascension)
    return {"decompose": dec, "ascension": ascension, "analogies": analogies}


def main(argv=None) -> int:
    here = Path(__file__).resolve().parents[2]
    repo = here.parent
    res = run(repo)
    dec, asc, analogies = res["decompose"], res["ascension"], res["analogies"]

    print(f"paper '{dec['target']}' ({dec['n_facts']} facts) — Nesterov 1983, accelerated gradient")
    print(f"  = composition of known priors: {', '.join(dec['covering_priors'])}")
    print(f"  covered {dec['covered_facts']}/{dec['n_facts']} ({dec['coverage_fraction']})")
    print(f"  novel contribution (residual): {', '.join(dec['novel_contributions'])}")
    print(f"\n  the momentum step plays role {asc.get('MOMENTUM')} (same as contraction / "
          f"weighted-exchangeability), so the paper joins the cross-domain analogy web:")
    for a in analogies[:2]:
        print(f"    {a['a']} ~~ {a['b']} (score {a['score']}; method <-> {a['correspondences'].get('method')})")

    # invariants (CI gate; explicit raise so it holds under `python -O`)
    checks = [
        (dec["covering_priors"] == ["estimate_sequence"],
         "Nesterov must be covered by the estimate-sequence prior"),
        (any(s.startswith("OPTIMAL_RATE") for s in dec["novel_contributions"]),
         "the novel residual must be the OPTIMAL (accelerated) rate"),
        (0.0 < dec["coverage_fraction"] < 1.0,
         "the paper is a real contribution: partial reuse, non-empty residual"),
        (asc.get("MOMENTUM") == asc.get("CONTRACTION"),
         "Nesterov's momentum must be discovered as the same structural-property role"),
        (any(a["a"] == "nesterov_acceleration" and a["b"] == "banach_contraction"
             and a["correspondences"].get("method") == "the_map" for a in analogies),
         "Nesterov must be cross-domain analogous to a contraction result"),
    ]
    for ok, msg in checks:
        if not ok:
            raise SystemExit(f"realpaper2 invariant violated: {msg}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

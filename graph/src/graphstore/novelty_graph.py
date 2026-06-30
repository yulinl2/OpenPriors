"""Per-result novelty scoring across the unified graph (Epic W).

The project began as a novelty detector; this closes that thread at graph scale. Every result
in the unified graph gets a precise **novelty score** — the IP-judge / MDL framing — measured
against the most-covering known prior:

    novelty(R) = 1 - max over priors P (P != R, |P| <= |R|) of coverage(P -> R)

where coverage(P -> R) is the fraction of R's facts that P explains (exact-functor SME, so a
prior only covers same-field structure), capped by multiplicity. The constraint |P| <= |R|
keeps a *larger* descendant from spuriously "covering" a smaller ancestor — a prior must be at
least as general. A result with no covering prior (a field's base result) scores novelty 1.0;
a near-copy of a known result scores ~0. The uncovered remainder is the result's genuine
**residual** — its contribution over the nearest prior.

Scores are written onto the result nodes, so the one graph also carries, for every result, how
novel it is and what it builds on — the same signal the riddles / Banach / real-paper cases
validated, now assigned to every node automatically.
"""

from __future__ import annotations

from collections import Counter

from analogy.align import align, fmt_expr
from analogy.predicates import Dgroup

from .model import Node


def coverage_of(prior: Dgroup, result: Dgroup) -> float:
    """Fraction of ``result``'s facts explained by ``prior`` (exact-functor SME, multiplicity
    capped so duplicate facts can't push it past 1.0)."""
    if not result.facts:
        return 0.0
    matched = Counter(repr(e) for e in align(prior, result).matched_target)
    rmult = Counter(repr(f) for f in result.facts)
    covered = sum(min(matched[k], rmult[k]) for k in rmult)
    return covered / len(result.facts)


def result_novelty(results: dict[str, Dgroup]) -> dict[str, dict]:
    """Per-result novelty + nearest prior + residual over the pooled result set."""
    out = {}
    for name, R in results.items():
        best, best_cov = None, 0.0
        for pn, P in results.items():
            if pn == name or len(P.facts) > len(R.facts):
                continue
            c = coverage_of(P, R)
            if c > best_cov:
                best, best_cov = pn, c
        # residual = R's facts not covered by the nearest prior (all of them if it's a root)
        if best is None:
            residual = [fmt_expr(f) for f in R.facts]
        else:
            matched = Counter(repr(e) for e in align(results[best], R).matched_target)
            residual = []
            for f in R.facts:
                k = repr(f)
                if matched.get(k, 0) > 0:
                    matched[k] -= 1
                else:
                    residual.append(fmt_expr(f))
        novel_leaves = sorted(r for r in residual if not r.startswith("CAUSE("))
        out[name] = {
            "novelty": round(1 - best_cov, 4),
            "nearest_prior": best,
            "coverage": round(best_cov, 4),
            "residual": sorted(residual),
            "novel_contributions": novel_leaves,
        }
    return out


def annotate_novelty(g, scores: dict[str, dict]) -> int:
    """Write each result's novelty + nearest prior onto its result node. Returns the count."""
    n = 0
    for name, sc in scores.items():
        nid = f"result::{name}"
        if nid in g.nodes:
            node = g.nodes[nid]
            g.add_node(Node(nid, node.kind, node.label,
                            {"novelty": sc["novelty"], "nearest_prior": sc["nearest_prior"]},
                            node.provenance))
            n += 1
    return n

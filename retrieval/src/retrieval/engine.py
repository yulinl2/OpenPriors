"""Library-scale novelty retrieval (MAC/FAC, Forbus-Gentner-Law 1995).

The project's answer to the "indexing burden over millions of sources" (structure mapping
notes §3): you cannot run expensive SME against every prior, so

  1. **MAC stage** — cheap content-vector (bag-of-functors) cosine ranks the library and
     short-lists the top-k candidate theorems;
  2. **FAC stage** — full SME structural alignment of the target against each short-listed
     theorem yields a novelty score; the nearest prior is the lowest-novelty match.

So "is this result novel?" becomes "what known theorem is it an instance of, and how much
of it does that theorem already explain?" — the IP-judge framing, at library scale.
"""

from __future__ import annotations

import json
from collections import Counter
from math import sqrt
from pathlib import Path

from analogy.align import align
from analogy.predicates import Dgroup, functor, subexprs


# ---- content vector (MAC) ----
def functor_vector(dg: Dgroup) -> dict[str, int]:
    c: Counter = Counter()
    for fact in dg.facts:
        for s in subexprs(fact):
            fn = functor(s)
            if fn:
                c[fn] += 1
    return dict(c)


def cosine(v1: dict[str, int], v2: dict[str, int]) -> float:
    n1 = sqrt(sum(x * x for x in v1.values()))
    n2 = sqrt(sum(x * x for x in v2.values()))
    dot = sum(v1[k] * v2[k] for k in set(v1) & set(v2))
    return dot / (n1 * n2) if n1 and n2 else 0.0


# ---- loading ----
def expr_from_json(node):
    if isinstance(node, str):
        return node
    if isinstance(node, list) and node:
        return (node[0],) + tuple(expr_from_json(x) for x in node[1:])
    raise ValueError(f"bad expression node: {node!r}")


def load_library(path: str | Path) -> dict[str, Dgroup]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {k: Dgroup(v["name"], [expr_from_json(f) for f in v["facts"]])
            for k, v in data.items() if not k.startswith("_")}


# ---- retrieval (MAC -> FAC) ----
def _verdict(novelty: float, coverage: float, prior: str) -> str:
    if coverage == 0:
        return "no structural prior in the library (novel relative to the library)"
    if novelty <= 0.15:
        return f"INSTANCE of {prior} (known machinery on relabeled objects)"
    if novelty <= 0.6:
        return f"extends {prior} with new structure (partial reuse)"
    return f"largely novel — reuses only the skeleton of {prior}"


def _raw_coverage(target: Dgroup, gmap) -> float:
    """Fraction of the target's facts explained by the prior — UNROUNDED (for sort/verdict)."""
    matched = {repr(e) for e in gmap.matched_target}
    n = len(target.facts)
    return (sum(1 for f in target.facts if repr(f) in matched) / n) if n else 0.0


def retrieve(target: Dgroup, library: dict[str, Dgroup], mac_k: int = 2) -> dict:
    tv = functor_vector(target)
    # MAC: rank on RAW cosine (rounding only for the reported ranking).
    raw = sorted(((name, cosine(tv, functor_vector(dg))) for name, dg in library.items()),
                 key=lambda kv: -kv[1])
    raw_lookup = dict(raw)
    mac_ranking = [(name, round(s, 4)) for name, s in raw]
    shortlist = [name for name, _ in raw[:mac_k]]

    fac = []
    for name in shortlist:
        prior = library[name]
        g = align(prior, target)                       # base = known theorem
        cov = _raw_coverage(target, g)                  # raw coverage of target by the prior
        nov = 1.0 - cov
        fac.append({
            "prior": name,
            "mac_cosine": round(raw_lookup[name], 4),
            "mapping_size": len(g.correspondences),
            "structural_score": g.score,
            "target_coverage": round(cov, 4),
            "novelty_score": round(nov, 4),
            "_cov": cov, "_nov": nov,                    # raw, for sort/verdict
        })
    fac.sort(key=lambda r: r["_nov"])                    # nearest prior = lowest novelty (raw)
    best = fac[0] if fac else None
    verdict = _verdict(best["_nov"], best["_cov"], best["prior"]) if best else None
    for r in fac:                                        # drop raw helpers from the output
        r.pop("_cov"); r.pop("_nov")
    return {
        "target": target.name,
        "mac_ranking": mac_ranking,
        "fac": fac,
        "nearest_prior": best["prior"] if best else None,
        "nearest_novelty": best["novelty_score"] if best else None,
        "verdict": verdict,
    }

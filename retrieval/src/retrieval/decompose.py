"""Multi-prior decomposition: explain a full proof as a COMPOSITION of known theorems.

Generalizes single-prior retrieval (engine.retrieve) to a greedy **set cover** — the MDL
framing from `Imports/structure mapping notes.md` §6 (a short description = the known
theorems it reuses + a small residual). Each known theorem, aligned against the proof by
SME, "covers" the proof facts that match its statement; we greedily pick the theorem
covering the most still-uncovered facts until none adds coverage. What remains uncovered is
the proof's genuine **novel residual** (e.g. a bespoke assumption or a new derivation).
"""

from __future__ import annotations

from analogy.align import align, fmt_expr
from analogy.predicates import Dgroup

from .engine import load_library


def decompose(target: Dgroup, library: dict[str, Dgroup]) -> dict:
    facts = list(target.facts)
    key = {id(f): repr(f) for f in facts}
    by_key = {repr(f): f for f in facts}
    uncovered = set(by_key)

    # which proof facts each prior covers (matched by SME, base = the theorem)
    covers_by_prior = {}
    for name, prior in library.items():
        matched = {repr(e) for e in align(prior, target).matched_target}
        covers_by_prior[name] = (set(by_key) & matched)

    covering = []
    while True:
        best, best_new = None, set()
        for name, covered in covers_by_prior.items():
            new = covered & uncovered
            if len(new) > len(best_new):
                best, best_new = name, new
        if not best_new:
            break
        covering.append({"prior": best, "covers_n": len(best_new),
                         "covers": sorted(fmt_expr(by_key[k]) for k in best_new)})
        uncovered -= best_new

    n = len(facts)
    residual = sorted(fmt_expr(by_key[k]) for k in uncovered)
    # the substantive residual = non-CAUSE leaves (CAUSE facts are composition glue)
    novel_leaves = [r for r in residual if not r.startswith("CAUSE(")]
    return {
        "target": target.name,
        "n_facts": n,
        "covering_priors": [c["prior"] for c in covering],
        "covering_detail": covering,
        "covered_facts": n - len(uncovered),
        "coverage_fraction": round((n - len(uncovered)) / n, 4) if n else 0.0,
        "residual_facts": residual,
        "novel_contributions": novel_leaves,
    }


def main(argv=None) -> int:
    import json
    from pathlib import Path

    from .engine import expr_from_json

    here = Path(__file__).resolve().parents[2]
    repo = here.parent
    library = load_library(here / "library" / "proof_theorems.json")
    proof_data = json.loads((repo / "grounding" / "dgroups" / "q1_full_proof.json").read_text())["target"]
    proof = Dgroup(proof_data["name"], [expr_from_json(f) for f in proof_data["facts"]])

    rep = decompose(proof, library)
    out = here / "results"; out.mkdir(parents=True, exist_ok=True)
    (out / "decomposition.json").write_text(
        json.dumps(rep, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"proof '{rep['target']}' ({rep['n_facts']} facts)")
    print(f"  = composition of known theorems: {rep['covering_priors']}")
    print(f"  covered {rep['covered_facts']}/{rep['n_facts']} ({rep['coverage_fraction']})")
    print(f"  novel contributions (uncovered leaves): {rep['novel_contributions']}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

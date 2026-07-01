"""Assemble the compact data model the visual demo renders, from the live system output.

Everything the dashboard shows is computed here from the same code paths the pipeline uses, so
the demo can never drift from what OpenPriors actually produces. Kept separate from the HTML
builder so the model is testable on its own.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# a friendly identity per literature: colour + emoji, for the kid-facing views
DOMAINS = {
    "conformal":     {"color": "#3b82f6", "emoji": "🎯", "nice": "Conformal prediction",
                      "kid": "How sure is a prediction?"},
    "optimization":  {"color": "#22c55e", "emoji": "⛰️", "nice": "Optimization",
                      "kid": "Rolling downhill to the best answer"},
    "learning":      {"color": "#a855f7", "emoji": "🧠", "nice": "Learning theory",
                      "kid": "When does studying examples actually work?"},
    "concentration": {"color": "#f59e0b", "emoji": "🎲", "nice": "Concentration",
                      "kid": "Lots of small randomness averages out"},
}


def build_model() -> dict:
    import sys
    for p in ("graph/src", "retrieval/src", "analogy/src", "grounding/src"):
        sp = str(REPO / p)
        if sp not in sys.path:                          # idempotent: don't grow sys.path per call
            sys.path.insert(0, sp)

    from graphstore.multidomain import build_multidomain_graph
    from graphstore.novelty_graph import result_novelty
    from graphstore.query import extends_chain
    from graphstore.experiment_c2 import run_experiment

    g, domains, ascension, analogies = build_multidomain_graph(REPO)
    pooled = {}
    for corpus, texts, _ in domains.values():
        for name, dg in corpus.items():
            pooled[name] = dg
    texts_by_name = {}
    for _, texts, _ in domains.values():
        texts_by_name.update(texts)
    novelty = result_novelty(pooled)

    # which domain each result belongs to + its lineage parent (from the graph)
    domain_of, parent_of = {}, {}
    for dname, (corpus, _, _) in domains.items():
        for name in corpus:
            domain_of[name] = dname
            chain = extends_chain(g, name)
            parent_of[name] = chain[1] if len(chain) > 1 else None

    results = []
    for name in pooled:
        sc = novelty[name]
        results.append({
            "name": name, "domain": domain_of[name], "n_facts": len(pooled[name].facts),
            "novelty": sc["novelty"], "nearest_prior": sc["nearest_prior"],
            "parent": parent_of[name],
            "text": (texts_by_name.get(name, "") or "")[:240],
            "novel_bits": sc["novel_contributions"][:4],
        })

    # cross-domain analogies -> undirected pairs with the SME correspondence
    seen, edges = set(), []
    for a in analogies:
        key = tuple(sorted((a["a"], a["b"])))
        if key in seen:
            continue
        seen.add(key)
        edges.append({"a": a["a"], "b": a["b"], "score": a["score"],
                      "corr": a["correspondences"]})

    # the discovered roles (which relation plays which structural role)
    roles = dict(sorted(ascension.items()))

    evals = json.loads((REPO / "graph" / "evaluations" / "conjecture_evaluations.json").read_text())
    directions = json.loads((REPO / "graph" / "evaluations" / "research_directions.json").read_text())
    exp = run_experiment(seed=0)
    exp_points = exp["trials"][0]["points"]

    return {
        "domains": DOMAINS,
        "results": sorted(results, key=lambda r: (r["domain"], r["n_facts"])),
        "analogies": edges,
        "roles": roles,
        "conjectures": [
            {"id": e["id"], "statement": e["statement"], "verdict": e["verdict"],
             "reasoning": e["reasoning"], "related": e["related_known_work"],
             "projection": e["projection"], "base": e["source_base"], "target": e["source_target"]}
            for e in evals["evaluations"]],
        "directions": [
            {"id": d["id"], "precise": d["precise_statement"], "established": d["whats_established"],
             "open": d["open_question"], "next": d["next_step"], "scope": d["scope_verdict"]}
            for d in directions["directions"]],
        "experiment": {"gamma": exp["gamma"], "n_states": exp["n_states"],
                       "points": [{"chi2": round(p["chi2"], 4), "modulus": round(p["modulus"], 4)}
                                  for p in exp_points]},
        "stats": g.stats(),
        "counts": {"literatures": len(domains), "results": len(results),
                   "analogies": len(edges), "conjectures": len(evals["evaluations"]),
                   "directions": len(directions["directions"])},
    }


if __name__ == "__main__":
    print(json.dumps(build_model(), indent=2, ensure_ascii=False)[:2000])

"""Reasoning lineage: reconstruct a literature's *extends* DAG from grounded structure.

Epic K answered "what known prior is this one paper an instance of?" against a fixed library.
Epic L generalizes to a **corpus of results that are each other's priors**: every result is
both a potential ancestor and a potential descendant. By measuring, for each ordered pair,
how much of one result's structure is reused inside another (SME coverage), we recover the
literature's **reasoning lineage** — a DAG whose edges are *X extends Y*, each justified by
the residual structure X adds over Y.

This is the project's ultimate target shape made concrete at the level of whole results: an
(object, attribute, relation) graph where **objects = results**, the **relation = extends**,
and the edge **attributes = the novel residual + a novelty fraction**. The backbone is the
transitive reduction (each node's *direct* parent = its most specific ancestor), so the chain
reads as the actual line of development rather than every transitive reuse.
"""

from __future__ import annotations

from collections import Counter

from analogy.align import align, fmt_expr
from analogy.predicates import Dgroup


def _coverage(base: Dgroup, target: Dgroup) -> float:
    """Fraction of ``base``'s facts that appear as a substructure of ``target`` (by SME).

    High coverage of A inside B means B reuses A's machinery — A is structurally contained
    in B. This is asymmetric: c(A,B) != c(B,A), and that asymmetry gives the lineage its
    direction (the more general, fewer-fact result is the ancestor).

    ``align`` enforces consistency over entity correspondences, not 1-1 over expressions, so
    ``matched_base`` can repeat a base fact when the target holds duplicate matches. We count
    matches with multiplicity capped by each base fact's own multiplicity, so the result is
    always in [0, 1] and duplicate facts can't inflate it past full coverage.
    """
    if not base.facts:
        return 0.0
    matched = Counter(repr(e) for e in align(base, target).matched_base)
    base_mult = Counter(repr(f) for f in base.facts)
    covered = sum(min(matched[k], base_mult[k]) for k in base_mult)
    return covered / len(base.facts)


def lineage(corpus: dict[str, Dgroup], tau: float = 0.5) -> dict:
    names = list(corpus)
    nfacts = {a: len(corpus[a].facts) for a in names}
    # cov[a][b] = how much of result a is reused inside result b
    cov = {a: {b: _coverage(corpus[a], corpus[b]) for b in names if b != a} for a in names}

    nodes, edges, parents = [], [], {}
    for p in names:
        # ancestors = strictly more general results (fewer facts) whose structure p largely
        # reuses (coverage >= tau). Equal-size results can't be ordered, so they're excluded.
        ancestors = sorted(
            (a for a in names if a != p and nfacts[a] < nfacts[p] and cov[a][p] >= tau),
            key=lambda a: (-nfacts[a], -cov[a][p], a),
        )
        parent = ancestors[0] if ancestors else None
        parents[p] = parent
        nodes.append({"result": p, "n_facts": nfacts[p],
                      "ancestors": ancestors, "is_root": parent is None})
        if parent is None:
            continue
        # residual = p's facts not covered by its direct parent = p's contribution over it.
        # Consume matched-target occurrences with multiplicity (a Counter, not a set) so that
        # if p legitimately repeats a fact, one parent match doesn't drop every duplicate.
        # Cap each fact's matches by the PARENT's own multiplicity: a parent that states a
        # fact once can explain at most one occurrence of it in p, even if SME matched it
        # against several duplicates in p.
        raw = Counter(repr(e) for e in align(corpus[parent], corpus[p]).matched_target)
        parent_mult = Counter(repr(f) for f in corpus[parent].facts)
        matched = Counter({k: min(raw[k], parent_mult[k]) for k in raw})
        residual = []
        for f in corpus[p].facts:
            r = repr(f)
            if matched.get(r, 0) > 0:
                matched[r] -= 1
            else:
                residual.append(fmt_expr(f))
        residual = sorted(residual)
        novel = [r for r in residual if not r.startswith("CAUSE(")]
        edges.append({
            "child": p,
            "parent": parent,
            "relation": "extends",
            "parent_reuse": round(cov[parent][p], 4),       # how much of parent p contains
            "novelty": round(len(residual) / nfacts[p], 4),  # fraction of p that is new
            "residual": residual,
            "novel_contributions": novel,
        })

    roots = [n["result"] for n in nodes if n["is_root"]]
    return {"nodes": nodes, "edges": edges, "roots": roots, "parents": parents, "tau": tau}


def _order(parents: dict) -> list[str]:
    """Topological order (roots first) for a tidy printout."""
    depth = {}

    def d(n):
        if n not in depth:
            depth[n] = 0 if parents[n] is None else 1 + d(parents[n])
        return depth[n]

    return sorted(parents, key=lambda n: (d(n), n))


def _load_corpus(repo, here) -> dict[str, Dgroup]:
    import json

    from .engine import expr_from_json, load_library

    corpus = dict(load_library(here / "library" / "conformal_theorems.json"))
    paper = json.loads(
        (repo / "grounding" / "dgroups" / "arxiv_2006_06138_main.json").read_text())["target"]
    corpus[paper["name"]] = Dgroup(
        paper["name"], [expr_from_json(f) for f in paper["facts"]])
    return corpus


def main(argv=None) -> int:
    import json
    from pathlib import Path

    here = Path(__file__).resolve().parents[2]
    repo = here.parent
    corpus = _load_corpus(repo, here)
    rep = lineage(corpus)

    out = here / "results"
    out.mkdir(parents=True, exist_ok=True)
    (out / "lineage.json").write_text(
        json.dumps(rep, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    parent_of = rep["parents"]
    edge_of = {e["child"]: e for e in rep["edges"]}

    def _depth(n):
        return 0 if parent_of[n] is None else 1 + _depth(parent_of[n])

    print(f"reasoning lineage over {len(rep['nodes'])} results (tau={rep['tau']}):")
    for n in _order(parent_of):
        pad = "  " * (_depth(n) + 1)
        if parent_of[n] is None:
            print(f"{pad}{n}  [root]")
        else:
            e = edge_of[n]
            print(f"{pad}-> {n}  extends {e['parent']} "
                  f"(novelty {e['novelty']}; adds {', '.join(e['novel_contributions'])})")

    # invariant: the conformal chain must come out split -> weighted -> paper, with the
    # paper's contribution isolated to COUNTERFACTUAL + NESTED. Explicit raise (CI gate).
    paper_edge = edge_of.get("arxiv-2006.06138-main")
    checks = [
        (parent_of.get("weighted_conformal") == "split_conformal",
         "weighted_conformal should extend split_conformal"),
        (paper_edge and paper_edge["parent"] == "weighted_conformal",
         "the paper should extend weighted_conformal"),
        (paper_edge and any(s.startswith("COUNTERFACTUAL") for s in paper_edge["novel_contributions"]),
         "paper residual must contain COUNTERFACTUAL"),
        (paper_edge and any(s.startswith("NESTED") for s in paper_edge["novel_contributions"]),
         "paper residual must contain NESTED"),
    ]
    for ok, msg in checks:
        if not ok:
            raise SystemExit(f"lineage invariant violated: {msg}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

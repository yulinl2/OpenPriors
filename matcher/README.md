# OpenPriors · matcher (Epic C foundation)

The structure-mapping retrieval layer. Consumes the [`concept_graph`](../concept_graph)
output and provides the machinery a novelty detector needs:

1. **MAC stage** (`mac.py`) — cheap **content-vector** retrieval (MAC/FAC, Forbus-Gentner-Law
   1995) over the bag-of-predicates emitted by `concept_graph.sme.content_vector`. The
   retrieval short-list (`rank_against`) ranks by the **dot-product** MAC score, which is an
   *upper bound* on the full SME structural score — hence a sound pre-filter for
   "renaming-invariant retrieval at scale". `cosine` is provided only as a length-normalized
   *similarity view* (the human-readable matrix) and does not carry the upper-bound guarantee.
2. **Renaming-invariance** (`invariance.py`) — the project's linchpin property, as a
   **metamorphic test**: relabel every entity id and assert the content vector, the relation
   multiset, and hence every MAC score are unchanged. This operationalizes "isomorphism under
   renaming, not lexical overlap" (`Imports/structure mapping notes.md` §1).
3. **Systematicity** (`invariance.py`) — SME's selection principle as a proxy: size × depth of
   the higher-order reasoning DAG (deeper, more interconnected structure is preferred).

## Results (over the four corpus graphs)

- **Renaming-invariance holds for all graphs** ✅ (the foundational guarantee).
- MAC similarity matrix (`results/similarity_matrix.json`): the two formalize-heavy proof
  documents (arXiv 2006.06138 ↔ problem_07) are the most similar cross-document pair (**0.91**),
  the metadata form the least — a sensible content-vector retrieval signal.
- Systematicity: arXiv = 34 (depth 1, 17 higher-order relations); the prose/form documents = 0,
  honestly reflecting that their reasoning chains are still implicit (the sub-agent frontier
  in `concept_graph/docs/principles-continuity.md`).

## Run

`matcher` imports `concept_graph.*`, so put both on `PYTHONPATH` (this repo wires
dependencies via `PYTHONPATH`, consistent with the other epics; or `pip install -e
concept_graph`):

```bash
PYTHONPATH=matcher/src:concept_graph/src decomposer/.venv/bin/python -m matcher.cli
PYTHONPATH=matcher/src:concept_graph/src decomposer/.venv/bin/python -m pytest matcher/tests -q
```

## Where this is going (Epic C)

This is the MAC half of MAC/FAC. The FAC half — full SME structural alignment (greedy
match-hypothesis merge) and **candidate-inference / "shortcut" detection** (the novelty
signal: coverage of a target by source-projected inferences ÷ mapping description length) —
builds on these same `dgroup`/content-vector inputs. The renaming-invariance guarantee here is
the precondition that makes that alignment meaningful. See `ROADMAP.md` Epic C.

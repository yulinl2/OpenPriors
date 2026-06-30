# OpenPriors · analogy (Epic C / FAC — the novelty detector core)

The **structure-mapping engine**: given two predicate-calculus description groups (a *base*
and a *target*), it finds the best structure-preserving alignment, projects **candidate
inferences**, and computes the **candidate-inference "shortcut" / novelty signal** — the
mechanism OpenPriors exists to build (`Imports/structure mapping notes.md` §2, §6).

This is the **FAC** half of MAC/FAC; the [`matcher`](../matcher) MAC stage is the cheap
pre-filter that feeds it.

## What it does

1. **Match hypotheses** — pair base/target expressions identical under *identicality*
   (same functor, same arity, recursively); entity leaves induce correspondences.
2. **Greedy merge** (no backtracking) into a maximal consistent global mapping (**Gmap**),
   scoring by order so **systematicity** (deep, interconnected structure) wins.
3. **Candidate inferences** — unmatched base structure anchored to the matched system is
   projected onto the target (unmapped args become skolems).
4. **Novelty / shortcut signal** — `target_coverage`, `novelty = 1 − coverage`, and a
   description-length-normalized shortcut score.

## Verified against ground truth

The canonical **solar-system → atom** analogy (Gentner 1983) has a *known* correct mapping,
so it is the test oracle:

```
mapping            : {sun → nucleus, planet → electron}      ✅ (the textbook answer)
top inference      : CAUSE(AND(GREATER(MASS(nucleus),MASS(electron)), ATTRACTS(nucleus,electron)),
                            REVOLVES(electron,nucleus))      ← projected onto the atom
inference ranking  : CAUSE (systematic) ranked above the GREATER(TEMPERATURE…) distractor  ✅
novelty            : coverage 1.0 → novelty 0.0  (the atom *is* the solar system relabeled)
```

7 tests, incl. identicality semantics, the known mapping, systematic-beats-distractor
inference ranking, and an unrelated-target control (coverage 0 → novelty 1).

It also runs on the real corpus: `from_concept_dgroup()` loads any `concept_graph`
`dgroup.json`, so e.g. `arxiv-2006.06138 → problem_07` aligns on shared relational structure.

## Run

```bash
PYTHONPATH=analogy/src decomposer/.venv/bin/python -m analogy.cli
# optional corpus pair:
PYTHONPATH=analogy/src decomposer/.venv/bin/python -m analogy.cli \
  --base concept_graph/graphs/arxiv-2006.06138/dgroup.json \
  --target concept_graph/graphs/problem_07/dgroup.json
PYTHONPATH=analogy/src decomposer/.venv/bin/python -m pytest analogy/tests -q
```

## Deeper engine (Epic G)

Two refinements toward the full SME, both opt-in / backward-compatible:

- **Minimal ascension** (notes §1, §7) — SME's strict identicality is brittle: `MINIMIZE` and
  `OPTIMIZE` never match. `align(base, target, ascension=...)` relaxes this: two functors also
  match if they share a parent in a type lattice (`examples.DEFAULT_ASCENSION`). On a
  near-synonym pair, strict matching recovers only the identical predicate (`{loss:cost}`)
  while ascension recovers the full mapping (`{loss:cost, agent:system, time:step}`).
- **Trickle-down systematicity** (notes §2) — `align(..., trickle=γ)` adds
  `γ·(1 + order(sub))` for each matched sub-relation that is also nested inside another
  matched expression, so structure deep inside a systematic web scores more than the same
  relations in isolation: a CAUSE-over-relations pair gains (`12 → 15.5` at γ=0.5) while
  three isolated relations gain nothing (`7 → 7`). Default `0.0` keeps scores
  backward-compatible. This mechanizes SME's selection principle (prefer deep, interconnected
  structure).
- **Skolem-penalized candidate inferences** (notes §6) — projecting a base fact whose argument
  has no target image invents a new ("skolem") entity, a weaker inference. `n_skolems` is always
  reported, but the score subtracts it only under the opt-in `align(..., skolem_penalty=γ)`
  (default `0.0` keeps scores backward-compatible): `2·anchored + overlap − γ·skolems`.

## Where this sits

This closes the core loop from `Imports/structure mapping notes.md`: decomposer (encode) →
concept_graph (relational graph + dgroups) → matcher (MAC retrieval, renaming-invariant) →
**analogy (SME alignment + candidate-inference novelty signal)**. The natural next step is
the LLM-based front end that lifts *prose* statements into rich predicate-calculus dgroups
(the documented sub-agent frontier), which turns the riddles' source↔target pairs and full
paper proofs into inputs this engine can align end-to-end.

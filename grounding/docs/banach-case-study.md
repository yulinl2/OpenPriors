# Case study — the novelty detector on real mathematics

*Does the OpenPriors pipeline recognize, on actual proof text, that a result is "known
machinery on relabeled objects"? Yes.*

## Setup

- **BASE** = the abstract **Banach Fixed-Point Theorem** (complete space, contraction → unique
  fixed point + linear-rate convergence).
- **TARGET** = **Question 1 of `problem_07`** (from the test corpus): it proves the retraining
  map `T(w) = argmin L(θ; w)` is a κ-contraction and applies Banach to get a unique `θ*` with
  `‖θ_t − θ*‖ ≤ κ^t‖θ_0 − θ*‖`, then derives the iteration count.

A sub-agent lifted each proof's prose into a grounded predicate-calculus dgroup
(`grounding/dgroups/banach_case.json`); every symbol is a verbatim source substring, checked
deterministically by `grounding/verify.py`. The full novelty detector (`analogy` SME +
candidate-inference signal) then runs via `grounding/casestudy.py`.

## Result

```
mapping        : {the_map → the_map, k → kappa, the_space → theta_space,
                  x_star → theta_star, the_seq → theta_seq}
target_coverage: 0.91     novelty_score: 0.09     structural_score: 22.0
novel (unmatched target) fact: ITERATION_COMPLEXITY(theta_seq, iter_count)
VERDICT        : INSTANCE of the base theorem (known machinery on relabeled objects) — low novelty
```

## Reading

The detector recovers the renaming that *is* the analogy — the abstract map/constant/fixed
point/sequence align onto the retraining map `T`, `κ`, `θ*`, `{θ_t}` (and `T` maps to `T`
identically). It judges Q1 to be **~91% the Banach theorem**, with the single genuinely new
piece — the explicit **iteration-complexity bound** `t ≥ ln(‖θ_0−θ*‖/δ)/ln(1/κ)` — surfaced
as the *only* unmatched target fact. That is precisely the OpenPriors objective from
`Imports/structure mapping notes.md` §6: *"a short projection from a deep mapping = exposed
shortcut,"* and *conceptual distance = 1 − normalized structural score*. The novel content is
isolated from the reused machinery, automatically, on real proof text.

## Why this matters

It validates the whole stack end-to-end on genuine mathematics (not a textbook toy): prose →
grounded dgroups → structure mapping → a faithful novelty verdict that an "intellectual-property
judge" could act on. The same path generalizes to any two technical artifacts whose prose the
front end can lift.

Run it: `PYTHONPATH=grounding/src:analogy/src decomposer/.venv/bin/python -m grounding.casestudy`

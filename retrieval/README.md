# OpenPriors · retrieval (Epic E — library-scale MAC/FAC novelty retrieval)

The project's answer to the *indexing burden* (`Imports/structure mapping notes.md` §3,
*"Many Are Called, Few Are Chosen"*): you cannot run expensive SME against every known prior,
so retrieval is two-stage —

1. **MAC** — a cheap **content-vector** (bag-of-functors) cosine ranks a theorem **library**
   and short-lists the top-k candidate priors;
2. **FAC** — full SME structural alignment of the target against each short-listed prior
   yields a **novelty score**; the nearest prior is the lowest-novelty match.

So "is this result novel?" becomes **"which known theorem is it an instance of, and how much
of it does that theorem already explain?"** — the IP-judge framing, at library scale.

## Result (over a 3-theorem library: Banach, M-estimator CLT, Cauchy–Schwarz)

```
problem_07-Q1  MAC top: banach_fixed_point (0.98)  -> nearest prior = banach_fixed_point
               novelty 0.09 :: INSTANCE of banach_fixed_point (known machinery, relabeled)

problem_07-Q2  MAC top: m_estimator_clt (0.55)     -> nearest prior = m_estimator_clt
               novelty 0.70 :: largely novel — reuses only the skeleton of m_estimator_clt
```

Both targets retrieve the **correct** prior (MAC never picks the Cauchy–Schwarz distractor),
and FAC **quantifies** the reuse: Q1 is a pure instance of Banach (91% explained); Q2 is a
genuinely novel result that reuses only the CLT *skeleton* (30% explained) and adds the
recursive-variance / tower-property machinery. That graded signal — not a binary —
is the "conceptual distance" the project wants.

## Run

```bash
PYTHONPATH=retrieval/src:analogy/src decomposer/.venv/bin/python -m retrieval.cli
PYTHONPATH=retrieval/src:analogy/src:grounding/src decomposer/.venv/bin/python -m pytest retrieval/tests -q
```

## Depth: multi-prior decomposition of a full proof (`retrieval.decompose`)

Single-prior retrieval finds the *nearest* prior; the decomposer explains an **entire proof
as a composition of known theorems** via greedy **set cover** (the MDL framing, notes §6):
each known theorem covers the proof facts that match its statement; pick the theorem covering
the most still-uncovered facts until none adds coverage. The uncovered remainder is the
proof's genuine **novel residual**.

On the full `problem_07` Q1 proof (14 facts) against a library of the theorems it invokes:

```
problem_07-q1-full = composition of: banach_fixed_point + strong_convexity + kantorovich_rubinstein
covered 5/14
novel contributions (uncovered leaves): SENSITIVITY(...), ITERATION_COMPLEXITY(...), OPTIMALITY(...)
```

The proof reuses three textbook theorems; what's left — the **ε-sensitivity assumption** (linking
distribution shift to parameter distance) and the **iteration-complexity bound** — is exactly the
paper's specific contribution over standard contraction theory. The system *isolates the novel
content from the borrowed machinery*, automatically.

```bash
PYTHONPATH=retrieval/src:analogy/src decomposer/.venv/bin/python -m retrieval.decompose
```

## Scale: ANN index for the MAC stage (`retrieval.index`)

The MAC content-vector scan is O(N) over the whole library — the "indexing burden over
millions of sources" (notes §3). `MacIndex` is a pure-Python (no FAISS, deterministic,
auditable) **SimHash LSH**: K fixed random hyperplanes give each content vector a K-bit
signature, so similar vectors land in nearby Hamming buckets and a query only exact-scores
the candidates in those buckets.

On a library scaled to ~1000 priors, querying for `problem_07` Q1:

```
ANN nearest: ('banach_fixed_point', 0.98)   (== the exact linear nearest)
candidates examined: 7 (0.7% of the library)
```

It finds the true nearest prior while exact-scoring **<1%** of the library — the sub-linear
MAC pre-filter that lets the SME/FAC stage stay expensive but rarely-invoked. Recall is
tunable via `max_hamming`.

```bash
PYTHONPATH=retrieval/src:analogy/src decomposer/.venv/bin/python -m retrieval.index
```

## End-to-end on a real published paper (`retrieval.realpaper`)

The whole stack, run against a **genuine published result** rather than a constructed case:
**Lei & Candès, *Conformal Inference of Counterfactuals and Individual Treatment Effects***
([arXiv 2006.06138](https://arxiv.org/abs/2006.06138)). The paper's main theorem is lifted
from its prose into a grounded dgroup (`grounding/dgroups/arxiv_2006_06138_main.json` — every
symbol traced to a verbatim substring of the statement, checked by `grounding.verify`) and
decomposed against a library of the conformal-prediction theorems it builds on
(`library/conformal_theorems.json`: split conformal, **weighted conformal under covariate
shift**, importance weighting).

```
paper 'arxiv-2006.06138-main' (9 facts) — arXiv 2006.06138
  MAC ranking: [('weighted_conformal', 0.959), ('split_conformal', 0.443), ('importance_weighting', 0.4)]
  nearest prior: weighted_conformal (novelty 0.2222)
  verdict: extends weighted_conformal with new structure (partial reuse)
  = composition of known theorems: ['weighted_conformal']
  covered 7/9 (0.7778)
  novel contributions (residual): COUNTERFACTUAL(the_interval, the_counterfactual), NESTED(the_interval, the_ite)
```

MAC retrieves the **correct** prior — weighted conformal prediction (Tibshirani, Barber,
Candès & Ramdas 2019) — far above the split-conformal and importance-weighting distractors.
FAC quantifies the reuse at 78%, and set-cover isolates the residual: `COUNTERFACTUAL` and
`NESTED`. That residual is **exactly the paper's stated contribution** — it takes weighted
conformal prediction and applies it to *counterfactual* outcomes (under unconfoundedness, the
likelihood-ratio weights are the inverse propensity score) and then *nests* the construction
to get intervals for the individual treatment effect. The system reads the borrowed machinery
as borrowed and points at the genuinely new structure — on a real paper, automatically.

```bash
PYTHONPATH=retrieval/src:analogy/src:grounding/src decomposer/.venv/bin/python -m retrieval.realpaper
```

## Extend

Add a theorem to `library/theorems.json` (a grounded dgroup — symbols traced to its
statement, checked by `grounding.verify`) and it becomes a retrievable prior. Add a target by
lifting any proof's prose into a dgroup (the `grounding` front end). The MAC stage scales to a
large library cheaply; only the top-k survive to the expensive FAC stage — exactly MAC/FAC.

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

## Extend

Add a theorem to `library/theorems.json` (a grounded dgroup — symbols traced to its
statement, checked by `grounding.verify`) and it becomes a retrievable prior. Add a target by
lifting any proof's prose into a dgroup (the `grounding` front end). The MAC stage scales to a
large library cheaply; only the top-k survive to the expensive FAC stage — exactly MAC/FAC.

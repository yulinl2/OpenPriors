# OpenPriors · grounding (Iteration 5 — the prose→dgroup front end)

The piece that makes the whole loop run on **raw text**: a sub-agent lifts natural-language
statements into predicate-calculus **description groups**, a **deterministic grounding check**
gates the extraction, and the [`analogy`](../analogy) engine solves by structure mapping.

This closes the OpenPriors thesis end-to-end on prose:
**decomposer → concept_graph → matcher → analogy**, now fed directly from text.

## The demonstration (the four riddles)

`decomposer/corpus/sample-text-riddles/sample-text-riddles.md` contains four analogy riddles
with *near-identical surface wording* but *different relational structure*. A sub-agent
extracted grounded dgroups (`dgroups/riddles.json`); the engine then solves each:

| Riddle | framing | defining relation | structural answer |
|---|---|---|---|
| 1 | "each person spent ___" | `DIVIDES(total, people, each)` | **1 hour** (3h ÷ 3) |
| 2 | "it took each person ___ to finish the job" | `DIVIDES` | **1 hour** |
| 3 | "…to finish the **same** job" | `EQUALS(each, total)` | **3 hours** (the whole total) |
| 4 | "it took **one** person ___ to finish the same job" | `EQUALS` | **3 hours** |

Same words, **two different answers** — recovered purely from relational structure. This is
the lexical < structural distinction OpenPriors is built to make, demonstrated end-to-end on
raw prose.

## The deterministic gate (why we can trust the LLM step)

Per the project doctrine, the sub-agent does the irreducible NL work but its output is
admitted only if a deterministic check passes (`verify.py`): **every symbol must be grounded
in a verbatim substring of the source text**, and every entity used in a fact must be
grounded. Hallucinated symbols fail the gate. The committed dgroups pass; CI re-checks them
(no LLM call in CI).

## Run

```bash
PYTHONPATH=grounding/src:analogy/src decomposer/.venv/bin/python -m grounding.cli
PYTHONPATH=grounding/src:analogy/src decomposer/.venv/bin/python -m pytest grounding/tests -q
```

## How it generalizes

The pattern — *sub-agent extracts a grounded structured artifact → deterministic check gates
it → downstream engine consumes it* — is the same one used to discover data classes in the
decomposer (Epic A). Here it lifts prose into SME dgroups; the next documents (full paper
proofs, theorem statements) plug into the identical loader/verifier/solver path.

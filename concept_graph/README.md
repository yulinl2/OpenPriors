# OpenPriors · concept_graph (Epic B)

Lifts the [`decomposer`](../decomposer) output (nodes + edges) into OpenPriors' target
**(object, attribute, relation)** representation — concepts (objects with attributes),
typed relations, and a **reasoning-chain DAG** — and emits the exact structures a
structure-mapping matcher (Epic C) consumes. Deterministic, independently verified, $0 cost.

## What it produces, per document

| Document | Concepts | Relations | Reasoning edges (`proves`/`derives_from`) | Verify |
|---|---:|---:|---:|:--:|
| arXiv 2006.06138 | 443 | 626 | 17 | ✅ |
| problem_07 | 134 | 133 | 0* | ✅ |
| problem_04_review | 57 | 56 | 0* | ✅ |
| sample-text-riddles | 13 | 12 | 0* | ✅ |

\* honest signal: these have no explicit `\ref`/`\proof` structure — their reasoning chain
is implicit in prose, which is the documented **sub-agent frontier**
(`docs/principles-continuity.md`), not something to fabricate deterministically.

## Outputs (`graphs/<slug>/`)

```
concepts.jsonl      one object-with-attributes per line
relations.jsonl     one typed relation per line (contains/cites/refers_to/proves/derives_from)
triples.jsonl       flat (s, p, o) — the SME/MAC content unit
graph.json          canonical nested bundle
dgroup.json         SME description group: entities + attributes + relations + higher_order
content_vector.json MAC stage-1 bag-of-predicates
graph.nt            N-Triples export (interop / SHACL)
metrics.json, verification.json
```

## Run

```bash
# uses the decomposer's venv (pydantic only) and its runs/ outputs
cd /path/to/OpenPriors
decomposer/.venv/bin/python -c "import sys; sys.path.insert(0,'concept_graph/src'); from concept_graph import cli; raise SystemExit(cli.main([]))"
decomposer/.venv/bin/python -m pytest concept_graph/tests -q
```

## Design

A **property-graph model** in memory (concept = object + attribute properties; relation =
typed edge), persisted as **sorted JSONL** for diffability, with reasoning steps encoded as
**higher-order relations** (`higher_order: true`) — the AIF S-node / SME `CAUSE` pattern. The
lift is deterministic (a function of structure only); no NL inference happens here. The SME
bridge (`sme.py`) is the test that the representation is right: Epic C consumes `dgroup.json`
+ `content_vector.json` with zero remodeling. See `docs/lit-review-oar-kg.md` and
`docs/principles-continuity.md`.

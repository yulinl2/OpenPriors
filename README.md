# OpenPriors

> *Open-source your ideas, not just your code.*

OpenPriors is a **novelty detector** for ideas: it asks whether a "new" result is genuinely
novel, or just a known result running on relabeled objects. It does this with **structure
mapping** — comparing the *relational structure* of arguments, not their surface wording
("isomorphism under renaming, not lexical overlap"; see `Imports/structure mapping notes.md`).

This repo implements the full pipeline, from raw documents to a structural novelty signal,
as four independently-verified epics, each grounded in the same doctrine:
**论证 / 构建 / 独立检验** (Argue / Build / Independently-Verify), with deterministic code
wherever an invariant is machine-checkable and in-session sub-agents (no API) only where
natural-language understanding is irreducible.

## The pipeline

```
 raw document                                                        novelty signal
      │                                                                    ▲
      ▼                                                                    │
┌───────────────┐   ┌──────────────────┐   ┌──────────────┐   ┌────────────────────┐
│  decomposer   │──▶│  concept_graph   │──▶│   matcher    │──▶│      analogy       │
│   (Epic A)    │   │    (Epic B)      │   │  (Epic C·MAC)│   │   (Epic C·FAC)     │
│ clean nested  │   │ (object,         │   │ content-     │   │ SME alignment +    │
│ tree + node/  │   │  attribute,      │   │ vector       │   │ candidate-inference│
│ edge graph    │   │  relation) graph │   │ retrieval,   │   │ "shortcut" novelty │
│               │   │ + reasoning DAG  │   │ renaming-    │   │ detector           │
│               │   │ + SME bridge     │   │ invariant    │   │                    │
└───────────────┘   └──────────────────┘   └──────────────┘   └────────────────────┘
   #1 ✅ merged        #2 ✅ merged           #3 ✅ merged          #4 ✅ merged
```

| Epic | Dir | What it does | Verified by |
|---|---|---|---|
| **A** | [`decomposer/`](decomposer) | Generic, first-principles document decomposition: raw LaTeX/HTML/Markdown → clean **nested hierarchical** structure (tree + node/edge graph). De-redundancy, data-class classification, cross-reference resolution. | char-coverage conservation, schema, reference integrity, idempotence, **differential oracle vs LaTeXML HTML (0.85 recall)** |
| **B** | [`concept_graph/`](concept_graph) | Lifts that into the **(object, attribute, relation)** representation + a reasoning-chain DAG, plus an SME description-group / content-vector bridge. | edge conservation, traceability, reasoning-DAG acyclicity |
| **C·MAC** | [`matcher/`](matcher) | MAC content-vector retrieval (dot-product score upper-bounds SME) + the project's linchpin **renaming-invariance** guarantee + systematicity. | renaming-invariance metamorphic test (holds for all graphs), non-vacuity |
| **C·FAC** | [`analogy/`](analogy) | SME structural alignment + candidate-inference **novelty / "shortcut" detector** — the mechanism the project exists to build. | **textbook solar-system→atom mapping recovered**; systematic inference beats distractor |

## Run the whole thing

```bash
cd decomposer && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && cd ..
export SOURCE_DATE_EPOCH=1735689600   # reproducible artifacts
PYTHONPATH=decomposer/src     python -m decomposer.cli       # A: 4 docs -> runs/
PYTHONPATH=concept_graph/src  python -m concept_graph.cli    # B: -> concept_graph/graphs/
PYTHONPATH=matcher/src:concept_graph/src python -m matcher.cli   # C·MAC: retrieval + invariance
PYTHONPATH=analogy/src        python -m analogy.cli          # C·FAC: solar->atom + corpus pair
# all tests, all epics:
PYTHONPATH=decomposer/src:concept_graph/src:matcher/src:analogy/src \
  python -m pytest decomposer/tests concept_graph/tests matcher/tests analogy/tests -q
```

## How it's built (governance)

See [`ROADMAP.md`](ROADMAP.md): epic → iteration → step hierarchy, branch strategy, CI as
the supervision gate (4 workflows), and the backup/redundancy policy (push-after-iteration;
triple JSON/JSONL representations; provenance + content hashes; pinned deps + emitted JSON
Schema; reproducible outputs via `SOURCE_DATE_EPOCH`). Each epic's `docs/` holds its
lit-review (sub-agent produced), ADRs, and development log.

## Validation

The pipeline is exercised end-to-end on raw text, and the novelty signal is validated with
positive **and** negative controls that together span the lexical < structural distinction:

| Demonstration | What it shows | Result |
|---|---|---|
| **Riddles** (`grounding.cli`) | *identical surface, different structure* → different answer | riddles 1&2 → "1 hour" (`DIVIDES`); 3&4 → "3 hours" (`EQUALS`) |
| **Banach case** (`grounding.casestudy`) | *different surface, same structure* → an instance | problem_07 Q1 vs Banach: novelty **0.09**, "INSTANCE — known machinery, relabeled"; isolates `ITERATION_COMPLEXITY` as the lone novel fact |
| **Discrimination** (`grounding.discrimination`) | the detector is *not vacuous* | Banach vs Q1 = 0.09 (instance) **vs** Banach vs Q2 = 1.00 (distinct theorem); margin **0.91** |

So a result whose structure is a renamed copy of a known theorem scores ~0 novelty, while a
genuinely different theorem scores ~1 — exactly the "shortcut under fancy disguise" signal
from `Imports/structure mapping notes.md` §6, validated on real mathematics.

**53 tests · 7 CI workflows · all green · reproducible · $0 marginal API cost.**

## Frontier

The architecture is complete and validated; what remains is **breadth and scale** —
richer dgroup extraction on full paper proofs, novelty scans across a larger real corpus,
and more format adapters (HTML-native, PDF). Each plugs into the existing
loader / grounding-gate / aligner path without new design.

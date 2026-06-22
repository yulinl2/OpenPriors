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

## Status & frontier

34 tests, 4 CI workflows, all green; a complete vertical slice runs end-to-end on four
diverse test documents. The remaining frontier is the **LLM/sub-agent prose→dgroup front
end**: lifting natural-language statements (the riddles' source↔target pairs, full paper
proofs) into rich predicate-calculus description groups so the analogy engine runs end-to-end
on raw prose — gated, per the project doctrine, by a deterministic structural-grounding check.

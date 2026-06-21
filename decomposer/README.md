# OpenPriors · decomposer

**A generic, first-principles, independently-verified document-decomposition workflow.**
Raw documents (LaTeX papers, custom-macro exams, plain-prose riddles, metadata forms) →
clean, **nested, hierarchical** structured data — the upstream stage of OpenPriors'
`(object, attribute, relation)` concept/reasoning graph.

> Built to the brief: maximize performance & compute-efficiency while staying *easy to
> keep developing, easy to extend, easy to audit*. Every step is **论证 / 构建 / 独立检验**
> (Argue / Build / Independently-Verify), grounded in task principles, preceded by a
> literature review. NL-understanding steps use in-session Claude Code **sub-agents**
> (Max-plan, no API call). See [`docs/principles.md`](docs/principles.md).

## What it does, on four very different test cases

| Document | Format | Nodes | Key classes recovered | Coverage | Verify |
|---|---|---:|---|---:|:--:|
| **arXiv 2006.06138** (Lei & Candès) | multi-file LaTeX **+** ar5iv HTML | 443 | 34 sections, 112 equations, 10 theorems/lemmas/props, 88 bib refs, 167 cite/ref **edges** | 0.983 | ✅ |
| **problem_07** | custom-macro exam LaTeX | 134 | problem-statement / answer-key / grading-scheme / editor-notes, 26 equations, 13 metadata fields, 37 list items | 0.909 | ✅ |
| **sample-text-riddles** | plain-prose Markdown | 13 | 4 analogy **examples**, each a *source*↔*target* structure-mapping pair | 0.983 | ✅ |
| **problem_04_review** | Markdown metadata form | 57 | 12 sections, 27 form fields, code blocks | 0.911 | ✅ |

All four pass every invariant (schema, unique-ids, acyclic tree, **character-coverage
partition with zero overlap**, reference integrity, idempotent normalization). For the
paper, an **independent differential oracle** (our pure-Python skeleton vs. LaTeXML's
ar5iv HTML) agrees on **84.8%** of section titles. Total runtime: **~1.8 s for all four**
(incl. parsing the 4.3 MB HTML), **$0 marginal cost**.

## Quickstart

```bash
cd decomposer
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m decomposer.cli            # runs all 4 docs -> runs/ , prints PASS/FAIL
PYTHONPATH=src python -m pytest -q  # 12 tests incl. negative 'verify the verifier' cases
```

## Layout

```
decomposer/
  docs/
    principles.md            # the constitution: P1–P4, the 3-phase doctrine, the PEP
    lit-review/01,02,03.md   # tool / format / verification reviews (sub-agent produced)
    decisions/0001-*.md      # ADR: format, schema tool, toolchain + perf-vs-resource
    tool-guide.md            # distilled, reusable guide + cross-comparison of choices
    development-log.md       # trajectory, decisions, experience
    schema.json              # emitted JSON Schema of the whole bundle (audit)
  skills/                    # THE generic skills workflow (Claude Code Skills)
    decompose-overview/  extract-principles/  ingest-sources/
    normalize-deredundancy/  classify-data-classes/  hierarchical-split/
    independent-verify/  _template/
  src/decomposer/
    schema.py                # single source of truth: the data classes (P3)
    adapters/{latex,markdown}.py   # format adapters -> format-agnostic core
    verify/{invariants,differential}.py   # build-independent checks (独立检验)
    serialize.py  ids? pipeline.py  cli.py
  corpus/<slug>/...          # raw inputs (tex source + ar5iv HTML + local test cases)
  runs/<slug>/...            # per-doc artifacts: meta, trajectory, step.json, bundle, verification
  tests/
```

## Design in one paragraph

A **coarse role layer** (segment / assert / formalize / refer / exemplify / narrate /
meta) sits above a fine, JATS-inspired **node-type** vocabulary; adapters target *roles*,
which is why the same core handles LaTeX, Markdown, and prose, and why a new format means
"add an adapter", not "rewrite the core". The output is at once a **tree**
(`document.json`) and a **graph** (`nodes.jsonl` + `edges.jsonl`, one row per
(object, attribute, relation) record) — the bridge to the downstream OpenPriors graph.
Everything mechanical is deterministic Python (fast, free, diffable); sub-agents are
reserved for the one irreducibly natural-language judgment — discovering roles in an
unfamiliar format — and for additive spot-audits. Independent verification is library
code, unit-tested to fail on broken input.

See [`skills/decompose-overview/SKILL.md`](skills/decompose-overview/SKILL.md) to run the
workflow on a **new** document.

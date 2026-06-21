# Development log — trajectory, decisions, experience

Chronological record of how this workflow was built (the "同步记录开发过程，决策，经验"
requirement). Pairs with the per-run `runs/<slug>/trajectory.jsonl`.

## Session 1 — 2026-06-21 (autonomous build)

### Context established
- Read OpenPriors' existing notes: `Imports/structure mapping notes.md` (the project is a
  structure-mapping novelty detector; the end goal is an (object, attribute, relation)
  graph) and `Imports/Research Report.md` (lexical < conceptual < logical hierarchy;
  surface-biased embeddings). These fixed the *target*: a **faithful structural floor**
  the downstream graph can lift, invariant to surface renaming.
- Test cases inventoried: arXiv 2006.06138 (multi-file LaTeX paper + ar5iv HTML),
  `problem_07.tex` (custom exam macros), `sample-text-riddles.md` (prose analogies),
  `problem_04_review.md` (metadata form). Deliberately diverse → forces the
  generic-over-special design.

### Literature review (3 parallel sub-agents, no API)
Produced `docs/lit-review/01,02,03`. Key adopted findings:
- pylatexenc is the right deterministic pure-Python LaTeX engine; LaTeXML is gold-standard
  but heavy — **reuse ar5iv HTML as a free differential oracle** instead of installing it.
- JATS is the only standard covering all five element classes but lacks a theorem type →
  **role-based, JATS-inspired, extended** taxonomy.
- Pydantic v2 over msgspec (dev/audit velocity > serialization throughput at our scale).
- JSON + JSONL dual view (tree + node/edge) for diffability and the graph bridge.
- Verification must be **build-independent**: coverage conservation, round-trip,
  metamorphic, differential, idempotence, schema; LLM-as-judge only additive.

### Decisions (ADR 0001)
Format/schema/toolchain locked with a per-axis performance-vs-resource argument.

### Build order and what each stage taught
1. `docs/principles.md` first — the constitution (P1–P4, 3-phase doctrine, the PEP). Writing
   it first kept every later choice answerable to principles rather than improvised.
2. `schema.py` — single source of truth. The coarse `Role` layer was the highest-leverage
   decision: it is what lets one core serve four formats.
3. `serialize.py` + `verify/` — canonical output and invariants as **library code** so
   "独立检验" is reusable, not prose.
4. `adapters/latex.py` — built, then smoke-tested on the real files. Bugs found & fixed by
   running against ground truth (not by guessing):
   - `abstract` env mapped to `section` with no level → tree-builder crash → default level.
   - container/list children weren't tree-built or `\item`-split → recursion + `_list_items`.
   - custom `\problemsetup`/`\problemtags` macros (undefined here, defined in an absent
     `main.tex`) → a documented **case-by-case** META_MACROS rule (PEP-5) extracting fields.
   - synthetic metadata children shared a span → coverage overlap → span set to None.
5. `adapters/markdown.py` — headings/lists/quotes/code + two documented special rules:
   `Key: value` list items → form fields; divider-segmented heading-less docs → the
   source↔target **structure-mapping pairs** (directly OpenPriors-relevant).
6. `pipeline.py` + `cli.py` — staged run writing uniform `step.json` + `trajectory.jsonl`
   + verification report + canonical bundle.
7. Differential oracle bug worth recording: removing the ar5iv `ltx_tag` numbering span
   with `.remove()` also deletes its **tail** (the actual title). Fixed by computing visible
   text without mutating the tree → section-title recall jumped 0.06 → **0.85**. Lesson: an
   independent oracle is only as good as its own correctness; verify the verifier.

### Results (measured)
All four docs pass every invariant; coverage 0.909–0.983 with zero overlap; arXiv
citations 130/167 resolved (37 external, logged); differential section recall 0.85;
12/12 tests pass (incl. negative cases); ~1.8 s total; $0 marginal cost.

### Honest open issues / next increments
- **Differential theorem count** (ours 11 vs ar5iv `ltx_title_theorem` 4): ar5iv classes
  titled-vs-untitled theorems differently; our count is by environment kind. Soft signal,
  not a gate; reconcile by matching ar5iv `ltx_theorem` blocks, not just titled ones.
- **Equation canonicalization** (latex2sympy2 + sympy) is specced but not yet wired; it is
  the next lever for surface-invariant dedup and the (object, attribute, relation) lift.
- **Round-trip render** (a true inverse `serialize→render≈source`) is approximated today by
  character-coverage; a real renderer would upgrade P1 from conservation to losslessness.
- **`block` residual** (arXiv ~4.5%): figures/tables/algorithms not yet typed; enumerate +
  add adapter rules as needed (the residual is itemized, never silent).
- Generalization beyond LaTeX/Markdown: the role layer + PEP are format-agnostic, but only
  two adapters exist; HTML-native and PDF adapters are the obvious next coverage.

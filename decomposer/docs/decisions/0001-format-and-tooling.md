# ADR 0001 — Data format, schema tool, and parsing toolchain

- **Status:** Accepted (2026-06-21)
- **Deciders:** decomposer workflow (autonomous), grounded in `docs/lit-review/01,02,03`.
- **Context:** The brief demands a toolchain/format/process that *maximizes performance
  and compute-efficiency* while being *easy to keep developing, easy to extend, and
  easy to audit*. Inputs are arbitrary documents (LaTeX research papers, custom-macro
  exam files, plain-prose markdown, metadata forms). Output must be nested, hierarchical,
  and bridge to an `(object, attribute, relation)` graph.

## Decision

| Concern | Choice | Rejected alternatives |
|---|---|---|
| **Schema / data classes** | **Pydantic v2** (single source of truth; emits JSON Schema for audit; discriminated unions for heterogeneous node types) | msgspec (faster but our bottleneck is dev-velocity/audit, not throughput); attrs, raw dataclasses (weaker validation), bare JSON Schema (poor Python DX) |
| **On-disk format** | **Dual canonical view:** nested `document.json` (tree) **+** flat `nodes.jsonl` **+** `edges.jsonl` (one row = one (object,attribute,relation)-style record). Sorted keys, `\n`-terminated → minimal git diffs | YAML (ambiguous, slow), TOML (config-only, shallow), Parquet/SQLite (binary, not diffable — kept as an *optional derived* view) |
| **IDs** | **Hybrid:** stable path/logical id (primary key for cross-ref edges) **+** SHA-256 content-hash attribute (audit/dedup/change-detection); arXiv id as external key | bare content-hash IDs (change on every edit → unstable edges), ULIDs (random, non-reproducible) |
| **Element taxonomy** | **JATS-inspired, role-based, extended** with `Theorem/Definition/Proof/Problem/Example` (JATS lacks a theorem class) | Pandoc/CommonMark AST (flatten sections, no bib/xref semantics) |
| **LaTeX toolchain** | **PRIMARY:** pure-Python **pylatexenc** (deterministic, fast, auditable, extensible). **Differential oracle:** the already-downloaded **ar5iv HTML** *is* LaTeXML output → parse with **lxml** to cross-check, instead of running heavy LaTeXML ourselves | LaTeXML as primary (heavy Perl+TeX deps), Docling/nougat/marker/GROBID (PDF-first, neural, non-deterministic → un-auditable) |
| **Fallbacks** | TexSoup (best fault tolerance) / pandoc AST; skip-to-HTML if ar5iv exists; guarded latex2sympy2+sympy for math equivalence | — |
| **NL-understanding steps** | In-session Claude Code **sub-agents** (Max plan, no metered API), prompts+outputs saved as run artifacts; used **only** where a check is *not* machine-expressible | LLM API calls (metered); LLM-as-sole-judge (biased) |

## Performance-vs-resource justification (the brief's explicit requirement)

- **Compute & cost.** The dominant design move — *deterministic code wherever an
  invariant is machine-checkable, LLM sub-agents only for irreducible NL judgment* —
  drives marginal compute cost toward zero (no API spend; pure-Python parse of a paper
  is sub-second) while keeping output reproducible. This is both the cheapest and the
  most auditable option simultaneously; there is no perf/audit tradeoff to make here.
- **Pydantic over msgspec.** Measured throughput differences (msgspec ~2–5× faster
  encode/decode) are irrelevant at our data scale (documents are KB–MB, parsed once).
  The binding constraint is *human* time to extend/audit the schema, where Pydantic's
  ubiquity and validator ecosystem win. msgspec is recorded as a drop-in swap **iff**
  serialization ever becomes the hot path (the schema is isolated in `schema.py`, so the
  swap is local).
- **JSON/JSONL over binary.** We accept JSON's larger size and slower parse vs Parquet
  because *git-diffability and human-auditability* are first-class requirements; a
  derived Parquet/SQLite view can be generated on demand for analytics without
  compromising the source-of-truth's auditability.
- **ar5iv-as-oracle over running LaTeXML.** Reusing the already-fetched LaTeXML HTML for
  *differential verification* gives us the gold-standard skeleton at zero extra
  dependency weight or runtime — strictly dominating a local LaTeXML install.

## Consequences

- `schema.py` is the contract; `serialize.py` enforces canonical output; `verify/`
  holds reusable invariant checkers. Swapping the schema engine or adding a node type is
  a local change. Re-runs are reproducible and diff-clean, which is what makes the whole
  workflow auditable end-to-end.

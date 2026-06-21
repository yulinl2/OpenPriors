# Lit-review 02 — Schemas & formats for hierarchical scientific documents

*Produced by an in-session Claude Code sub-agent (no API call), 2026-06-21. Web-sourced; URLs inline.*
*Serves Steps 30 (classify) and 40 (hierarchical split). Decisions adopted in `docs/decisions/0001-format-and-tooling.md`.*

## 1. Document markup/interchange standards

| Standard | Sections | Theorem-like | Equations | Bib refs | Cross-refs |
|---|---|---|---|---|---|
| **JATS** (NISO Z39.96-2024) | `<sec>` nestable `@id` | `<statement>`/`<boxed-text>` (no native theorem) | `<disp-formula>`,`<inline-formula>` | `<ref-list>/<ref>/<element-citation>` | `<xref @rid @ref-type>` |
| **TEI P5** | `<div>` typed recursive | `<floatingText>` (no theorem) | `<formula>` | `<biblStruct>` | `<ref @target>`,`<ptr>` |
| **DocBook** | `<section>`/`<sect1..5>` | none; `<equation>` titled | `<equation>` | `<biblioentry>` | `<xref linkend>` |
| **Pandoc AST** (native JSON) | `Header` — **flat**, not nested | none | `Math Inline/Display` | citeproc `Cite` | `Link`/attr id |
| **CommonMark AST** | `heading` (flat) | none | none | none | none |
| **schema.org ScholarlyArticle** | `hasPart`/`articleSection` weak | none | none | `citation` | `@id` URIs |
| **OpenAlex/Crossref** | metadata only | — | — | `referenced_works` (DOI) | DOI |

**JATS** is the only widely-adopted standard canonicalizing all five classes with stable `@id`/`@rid` — but even it lacks a first-class *theorem/definition* type. Pandoc/CommonMark ASTs flatten sections and carry no bib/xref semantics. → Adopt **JATS-inspired taxonomy, extended with `Theorem`/`Definition`/`Proof`**.

## 2. Python schema/validation

| Tool | Speed | Emits JSON Schema | Discriminated unions | Validation | Ergonomics |
|---|---|---|---|---|---|
| **msgspec** | Fastest (C; ~2–5× pydantic v2) | `msgspec.json.schema()` | `Struct(tag=...)` | strong | lean |
| **Pydantic v2** | Fast (pydantic-core/Rust) | `model_json_schema()` | `Field(discriminator=...)` | richest (validators/coercion) | best DX/ecosystem |
| attrs / dataclasses+jsonschema / raw JSON Schema | varies | partial/manual | manual | weaker/external | verbose |

## 3. On-disk serialization (nested + graph-like)

| Format | Canonical/diffable | Streaming | Nesting | Flat node/edge |
|---|---|---|---|---|
| **JSON (JCS RFC 8785)** | excellent (sorted keys) | partial | native | derivable |
| **JSONL** | excellent (1 node/line → tiny diffs) | excellent | flat-per-line | **native** |
| YAML/TOML | ambiguous / config-only | weak/no | native/shallow | poor/no |
| Parquet | binary (not diffable) | excellent | Dremel nested | excellent (columnar) |
| SQLite | binary | query | tables | **native** |

Proven pattern: **dual representation** — canonical JSON/JSONL source-of-truth (auditable, diffable) + optional Parquet/SQLite derived query view.

## 4. Stable identifiers

| Scheme | Stable across re-runs | Edges | Notes |
|---|---|---|---|
| **Content-addressed (SHA-256/UUIDv5)** | yes if content fixed (changes on edit) | hash=dedup key | CID, deterministic UUIDv5 |
| **Path-based** (`doc/sec[2]/thm[1]`) | stable under edits, breaks on reorder | natural tree edges | human-readable |
| ULID | no (random) | needs registry | sortable; mint for *events* only |
| JATS @id / DOI / arXiv | authored/external | `@rid`→`@id`, DOI | publishing baseline |

Best practice: **stable path/logical ID (primary key for cross-ref edges) + SHA-256 content-hash attribute (audit/change-detection/dedup)**; external keys (arXiv/DOI) where present.

## Recommendation (adopted, with one deviation)

- **Schema tool: Pydantic v2** (not msgspec). Both are fast and emit JSON Schema + discriminated unions; our bottleneck is **developer velocity, validation richness, and auditability**, not serialization throughput on KB–MB documents. Pydantic is more widely known → easier to audit/extend/onboard. msgspec is noted as the drop-in optimization if throughput ever dominates. (See ADR for the perf-vs-resource argument.)
- **Element taxonomy: JATS-inspired, role-based, extended** with `Theorem`/`Definition`/`Proof`/`Problem`/`Example`.
- **On-disk: canonical nested JSON (`document.json`) + flat `nodes.jsonl` + `edges.jsonl`** (one row = one (object, attribute, relation)-style triple) → bridges the document tree to OpenPriors' eventual knowledge graph. Optional Parquet/SQLite view later.
- **IDs: hybrid path/logical ID + SHA-256 content hash**; arXiv id as external key.

**Sources:** [JATS tag library](https://jats.nlm.nih.gov/) · [NISO JATS](https://www.niso.org/standards-committees/jats) · [Pandoc AST](https://pandoc.org/MANUAL.html) · [TEI P5](https://www.tei-c.org/release/doc/tei-p5-doc/en/html/ST.html) · [schema.org ScholarlyArticle](https://schema.org/ScholarlyArticle) · [msgspec](https://github.com/msgspec/msgspec) · [Pydantic unions](https://docs.pydantic.dev/latest/concepts/unions/) · [msgspec vs pydantic benchmark](https://hrekov.com/blog/msgspec-vs-pydantic-v2-benchmark) · [JCS RFC 8785](https://jsonic.io/guides/json-canonicalization) · [Parquet nested](https://arxiv.org/pdf/2304.05028) · [multiformats CID](https://github.com/multiformats/cid) · [ULID spec](https://github.com/ulid/spec) · [UniqTag content IDs](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4447347/)

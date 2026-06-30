---
name: ingest-sources
description: >-
  Step 10 of the decompose workflow. Acquire every available representation of a document
  (e.g. arXiv LaTeX e-print source AND the ar5iv/LaTeXML HTML rendition) and record full
  provenance — content hashes, tool versions, external ids. Use when you need the raw
  inputs staged and fingerprinted before normalization. The second rendition doubles as
  an independent differential oracle later.
---

# 10 — Ingest sources & record provenance

## When to use
After principles are extracted; before normalization. Input: a document id/path/URL.
Output: staged raw files under `corpus/<slug>/` + provenance in the run's `step-10`.

## Principles served
P1 (faithfulness starts at acquisition): nothing is trusted that is not fingerprinted.

## 论证 / Argue
Prefer acquiring **multiple renditions** of the same content. For arXiv: the e-print
tarball (`https://arxiv.org/e-print/<id>`) gives authoritative LaTeX *source*; the ar5iv
HTML (`https://ar5iv.labs.arxiv.org/html/<id>`) gives the **LaTeXML** rendition — a
gold-standard structured skeleton we reuse for *free* as a differential oracle, instead
of installing heavy LaTeXML ourselves (see ADR 0001 / `docs/lit-review/01`).

## 构建 / Build
- Download source + HTML; extract the tarball; keep `.tex/.bib/.bbl/.cls/.sty` and the HTML.
- Compute `sha256` of every source file; capture tool versions (python, pydantic,
  pylatexenc) and external ids (arxiv/doi).
- Code: `decomposer.pipeline.run_document` builds `SourceProvenance` automatically from
  the corpus `manifest.json` entry.

**Determinism:** provenance is content-addressed; re-ingesting unchanged inputs yields
identical hashes.

## 独立检验 / Verify
- Hashes recomputed and stored; file list non-empty; declared `formats` all present on disk.
- (Acquisition integrity) the byte counts in provenance match the staged files.

## Sub-agent usage
None — fully deterministic (network + hashing).

## Outputs
`corpus/<slug>/...` (raw) and `runs/<slug>/step-10-ingest/step.json` (provenance + metrics).

# Tool guide: using, extending, and auditing the decomposer

A structured, reusable guide to the workflow itself — how to run it on new input, how to
extend it, and the **systematic cross-comparison** justifying each final decision on the
performance-vs-resource axis (re-validated against measured results).

---

## 1. Run it on a new document (5 steps)

1. **Stage the raw input** under `corpus/<slug>/` and add a `manifest.json` entry
   (`adapter`, `main`, optional `bbl`/`html`, `external_ids`, `min_coverage`).
2. **Extract principles** (`skills/extract-principles`): run the PEP — name the conserved
   quantity, the redundancy, the recurring roles, the reference structure. If the format
   is unfamiliar, delegate *role discovery* to a sub-agent.
3. **Pick/add an adapter.** If the format is LaTeX or Markdown, reuse the adapter. Else
   write `adapters/<fmt>.py` exposing `normalize()` and `extract()` against the same core.
4. **Run** `python -m decomposer.cli` (or `pipeline.run_document(cfg, ...)`).
5. **Read** `runs/<slug>/verification/report.json`. Green = done; red = the failing
   invariant localizes the bug.

## 2. Extend the taxonomy (new data class)

Adding a recurring type is a **three-line, migration-free** change:
1. add the literal to `NodeType` in `schema.py`;
2. add its `TYPE_ROLE` mapping (which of the 7 roles);
3. add one adapter rule that emits it.
The schema, serializer, and every invariant pick it up automatically. This is the
operational meaning of "易拓展".

## 3. Extend verification (new invariant)

Add a `check_*` to `verify/invariants.py` returning a `CheckResult`, include it in
`run_all`, and add a **negative test** (`tests/`) proving it fails on a violating input.
A check without a failing test is presumed vacuous.

## 4. The decision cross-comparison (performance vs resource), re-validated

Each "axis" is scored ✅ strong / ➖ neutral / ⚠️ weak. The brief asks the final choices be
justified from *many* angles; measured outcomes are in the last column.

### 4.1 Schema engine

| Option | Speed | Audit (JSON Schema) | Validation | Ubiquity / onboarding | Verdict |
|---|---|---|---|---|---|
| **Pydantic v2** ✅ | ✅ (Rust core) | ✅ `model_json_schema()` | ✅ richest | ✅ | **chosen** |
| msgspec | ✅✅ (C) | ✅ | ✅ | ➖ | runner-up (drop-in if serialization becomes hot path) |
| dataclasses+jsonschema | ➖ | ⚠️ hand-authored | ⚠️ external | ✅ | no |

*Re-validation:* data is KB–MB, parsed once → the msgspec speed edge is irrelevant; the
binding constraint is human extend/audit time, where Pydantic wins. `schema.py` isolates
the engine, so swapping later is a local change.

### 4.2 On-disk format

| Option | Diffable | Streaming | Tree | Node/edge graph | Verdict |
|---|---|---|---|---|---|
| **JSON + JSONL** ✅ | ✅ (canonical, sorted keys) | ✅ (JSONL) | ✅ | ✅ (one row = triple) | **chosen** |
| Parquet/SQLite | ⚠️ binary | ✅ | ➖ | ✅ | derived view only |
| YAML/TOML | ➖ | ⚠️ | ✅/➖ | ⚠️ | no |

*Re-validation:* output is git-committed and human-audited → diffability outranks
Parquet's size/parse win. Measured: 443-node paper bundle ≈ 0.5 MB text, diff-clean across
re-runs.

### 4.3 LaTeX toolchain

| Option | Determinism/audit | Deps | Macro expand | Verdict |
|---|---|---|---|---|
| **pylatexenc** ✅ | ✅ pure-Python | ✅ none | ✅ (we add fixpoint) | **chosen (primary)** |
| LaTeXML | ✅ rule-based | ⚠️ Perl+TeX | ✅ | **reused as HTML oracle, not installed** |
| Docling/nougat/marker | ⚠️ neural | ⚠️ heavy ML | n/a (PDF) | no |

*Re-validation:* the ar5iv HTML *is* LaTeXML output → we get the gold-standard skeleton
for differential verification at **zero** extra dependency/runtime. Measured: full paper
parse + 4.3 MB HTML diff in **<1 s**.

### 4.4 Where LLM vs deterministic code

| Task | Machine-checkable? | Mechanism | Cost |
|---|---|---|---|
| flatten / strip / expand / whitespace | yes | deterministic code | $0, <1 s |
| classify by role (known format) | yes | adapter rules | $0 |
| **discover roles (unknown format)** | no | **sub-agent** (Max plan) | $0 (no API) |
| all invariants | yes | `verify/` | $0 |
| cross-reader spot-audit | partial | sub-agent (additive only) | $0 |

*Re-validation:* the deterministic-first split makes marginal compute ≈ free **and**
maximally auditable simultaneously — there is no perf/audit tradeoff to trade here.

## 5. Total resource budget (measured)

- **Marginal API cost:** **$0** — all NL work is in-session Max-plan sub-agents.
- **Dependencies:** 3 pip packages (pydantic, pylatexenc, lxml), pure-wheel, in a venv.
- **Wall time:** ~1.8 s for the full 4-document corpus including the HTML oracle.
- **Output:** canonical JSON/JSONL, diff-clean, schema-validated; JSON Schema emitted to
  `docs/schema.json` for external audit.

All comfortably within the "<\$5 over the Max plan" envelope (actual added cost: $0).

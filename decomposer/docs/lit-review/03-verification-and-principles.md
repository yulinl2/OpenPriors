# Lit-review 03 — Verifiable pipelines & extracting a task's principles

*Produced by an in-session Claude Code sub-agent (no API call), 2026-06-21. Web-sourced; URLs inline.*
*Serves the three-phase doctrine (`docs/principles.md`) and every step's `verification.md`.*

A **build's own logic cannot validate itself**. A check is independent only if it can fail when the build is wrong *and* shares none of the build's failure modes. This is the **test-oracle problem**: lacking ground truth, manufacture an oracle from *relations* the correct output must satisfy.

## 1. Independent-verification menu → document decomposition

| Technique | Independent because… | Decomposition invariant (machine-checkable) |
|---|---|---|
| **Round-trip / inverse** | uses the inverse code path | lossless reconstruction: `render(decompose(doc)) ≈ doc` |
| **Metamorphic** | checks relations *between* outputs, no ground truth | reorder/insert a section → other nodes unchanged; append is monotone (only adds nodes); rename macro → tree invariant |
| **Property-based** (Hypothesis) | random inputs probe the spec | all nodes typed; all cross-refs resolve; schema-valid for all generated docs |
| **Conservation / accounting** | counting argument, ignores *how* | **character-coverage**: every source char → ≤1 leaf; union = whole doc (partition); token count conserved |
| **Idempotence** | algebraic law, model-free | `normalize(normalize(x)) == normalize(x)` |
| **Differential** | two independent builds rarely share bugs | two parsers (pylatexenc vs ar5iv-HTML) → diff skeletons |
| **Golden/snapshot** | frozen baseline | regression on curated corpus; scrub volatile fields |
| **Schema/structural metrics** | external grammar / tree distance | JSON-Schema validity; TEDS tree-edit distance |

**Concrete invariants:** lossless reconstruction · character-coverage conservation (partition, no overlap/loss) · reference resolvability · schema validity · normalization idempotence · ordering preservation (reading order = stable topological sort) · containment acyclicity (nesting is a tree/DAG).

## 2. First-principles objectives → measurable forms

- **MDL / Kolmogorov** — good decomposition = compression: `L(structure) + L(doc | structure)` minimized; idempotence ≈ redundancy removed. MDL = computable approximation of (uncomputable) Kolmogorov complexity. "Any regularity useful for prediction is useful for compression."
- **Information-theoretic faithfulness** — (near-)lossless: I(source; structure) ≈ H(source); operationalized as round-trip / char-coverage.
- **Structure-mapping (Gentner)** — relations over attributes; prefer systematic (interconnected) structure. For us: capture *relations* (contains, references, precedes), reward connected hierarchy. Measurable: relation-coverage, systematicity (depth/connectivity).
- **Compositionality, lexical < syntactic < semantic ladder** — verify each stratum separately; higher layers must not violate lower-layer conservation.

## 3. Reusable principle-extraction procedure (GQM + design-by-contract)

Run on *any* raw→structured decomposition, domain/format-independent:

1. **State the goal (GQM-G)** → derive Questions → Metrics; every metric traces to a goal.
2. **What must be conserved?** → conservation invariant (chars/tokens/content).
3. **What is redundant?** → MDL/compression objective + idempotence.
4. **Enumerate recurring types** → schema (node types, allowed nesting) → schema-validity check.
5. **Map the reference structure** → cross-links/containment → resolvability + acyclicity; *relations over attributes*.
6. **Specify the inverse** (`render`/`serialize`) → enables round-trip. No inverse ⇒ under-determined spec.
7. **Write the contract** — preconditions/postconditions/invariants, each an executable assertion.
8. **Choose metamorphic relations** — reorder/insert/duplicate → assert output relation.
9. **Pick a differential oracle** — a second implementation/prompt for disagreement detection.

(This is operationalized as the **Principle-Extraction Protocol (PEP)** in `docs/principles.md` §4.)

## 4. Agentic build+verify: where determinism must replace the LLM

Use propose→critique→revise and generator–verifier loops, but **gate on deterministic checks, not LLM judgment**, wherever an invariant is machine-checkable. **LLM-as-judge is biased** (position/verbosity/authority, prompt-order sensitivity, bandwagon; even "avoid position bias" instructions can worsen it). **Rule:** any check expressible as conservation/schema/round-trip/idempotence/reference-resolution is a *deterministic gate*; reserve the LLM only for genuinely semantic, non-checkable judgments — and prefer self-consistency voting over a single judge.

**Sources:** [Metamorphic survey](https://dl.acm.org/doi/10.1145/3143561) · [MR patterns 2025](https://onlinelibrary.wiley.com/doi/abs/10.1002/stvr.70003) · [Round-trip properties](https://www.cis.upenn.edu/~plclub/blog/2023-12-07-round-trip-properties/) · [Differential testing](https://en.wikipedia.org/wiki/Differential_testing) · [Golden tests](https://cs-syd.eu/posts/2023-12-21-golden-tests) · [MDL](https://en.wikipedia.org/wiki/Minimum_description_length) · [MDL/Kolmogorov intro (Grünwald)](https://arxiv.org/pdf/1005.2364) · [Structure-mapping (Gentner 1983)](https://groups.psych.northwestern.edu/gentner/papers/Gentner83.2b.pdf) · [GQM](https://www.geeksforgeeks.org/goal-question-metric-approach-in-software-quality/) · [Contracts in Practice](https://arxiv.org/pdf/1211.4775) · [Document parsing survey](https://arxiv.org/html/2410.21169v5) · [LLM-as-judge bias](https://arxiv.org/abs/2406.07791) · [Scoring bias](https://arxiv.org/html/2506.22316v1)

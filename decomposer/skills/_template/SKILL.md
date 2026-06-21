---
name: step-template
description: >-
  TEMPLATE ONLY — not an executable skill. Copy this to author a new workflow step.
  Every decomposer step is structured as Argue / Build / Verify, each grounded in
  the task principles P1–P4. Do not invoke directly.
---

# <step-id> — <step name>

> Copy this file to `skills/<new-step>/SKILL.md` and fill every section. A step with
> a missing phase is not "done".

## When to use
<one or two sentences: the trigger and the input/output contract.>

## Principles served
<which of P1–P4 (and any task-specific P5) this step serves, and the **measurable
target** it adopts from `docs/principles.md` §0.>

## 论证 / Argue
- **Lit/tool review:** <what exists; what we adopt/reject and why — link `docs/lit-review/*`.>
- **Decision + perf-vs-resource:** <the choice and its cost/throughput/auditability justification; link an ADR.>

## 构建 / Build
- **Mechanism:** <deterministic code path in `src/decomposer/...`, or — only if NL
  understanding is irreducible — the sub-agent prompt (saved as a run artifact).>
- **Determinism & canonical output:** <how output stays reproducible/diffable.>

## 独立检验 / Verify
- **Invariant(s):** <machine-checkable predicate(s) from `src/decomposer/verify/`.>
- **Independence argument:** <why a bug in Build would NOT also fool this check.>
- **Reported on:** <every corpus item, with pass/fail in `verification/report.json`.>

## Sub-agent usage (if any)
<exact role; why a deterministic check cannot replace it; where the prompt+output
are saved. If none, say "none — fully deterministic".>

## Outputs
<files written under `runs/<slug>/step-<id>-.../`, in the uniform format.>

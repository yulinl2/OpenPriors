---
name: extract-principles
description: >-
  Step 00 of the decompose workflow. Run the Principle-Extraction Protocol (PEP) on a
  NEW, possibly-unknown document/corpus to name its fundamental principles BEFORE any
  parsing: what must be conserved, what is redundant, which data classes recur, and the
  reference structure. This is the step that makes the workflow generalize across
  domains, formats, and task types. Use first, whenever decomposing unfamiliar input.
---

# 00 — Extract the task's fundamental principles (PEP)

## When to use
Always first, before touching a parser. Input: a sample of the target corpus. Output:
`runs/<slug>/step-00-principles/principles.json` mapping each principle to a measurable
target and a chosen verifier.

## Principles served
Meta-step: it *instantiates* P1–P4 (and any P5…) for the concrete corpus. See
`docs/principles.md` §4 for the protocol.

## 论证 / Argue
Surface markup is unbounded and idiosyncratic; **roles are few and stable**. So we
derive principles from *roles and conserved quantities*, not from the format's keywords.
Lit basis: GQM (goal→question→metric), design-by-contract, MDL, structure-mapping
(`docs/lit-review/03`).

## 构建 / Build — run the PEP
For the sampled corpus, answer and record:
1. **PEP-1 Conserved quantity (P1):** what must survive a transform for output to still
   be *about* the input? (usually source characters/tokens) → write the conservation predicate.
2. **PEP-2 Redundancy (P2):** what carries presentation/tooling info, not content?
   (comments, whitespace, presentation macros, boilerplate) → a logged, reversible rule each.
3. **PEP-3 Recurring types (P3):** which units recur and play a *segmenting/asserting/
   formalizing/referring/exemplifying/meta* role? Cluster by **role, not keyword**. → class inventory.
4. **PEP-4 Hierarchy & refs (P4):** what contains what (tree) and what points to what (graph)?
5. **PEP-5 Task-specific:** any extra conserved quantity (e.g. keep statement/answer-key
   separable; preserve form-field identity) → add only if P1–P4 miss it.

**Sub-agent:** PEP-3 is the one genuinely NL judgment ("same role, different surface").
Delegate to an in-session sub-agent: give it 1–2 raw samples, ask for a role-clustered
inventory with evidence. Save its prompt+output under the step dir. Everything else is
analyst bookkeeping.

## 独立检验 / Verify
Each PEP answer must yield a *verifier*; if it cannot, the principle is under-specified.
Check: (a) every target has a machine-checkable predicate downstream; (b) the inverse is
specified (so round-trip is possible); (c) the residual "unclassified" budget is set.

## Outputs
`step-00-principles/principles.json` — `{principle, question, conserved/target,
verifier, status}[]`; plus the sub-agent transcript for PEP-3.

# The Oracle Bottleneck

*A self-contained synthesis: why AI can golf proofs but not refactor them, why that gap recurs up an entire capability ladder, and why an MDL formulation is the right way in.*

*Built from a multi-turn dialogue (June 2026) + one full primary-source verification audit. Every empirical claim carries a source and a confidence mark; interpretive mappings are fenced off separately.*

---

## 0 · The one-sentence thesis

> **The bottleneck in this whole family of problems is never *search* and never *transformation* — it is the *oracle*: the evaluation / equivalence judgment.** Shortest-path is easy because it has an oracle. Proof refactoring is hard because verification *saturates* the oracle (everything compiles) and the quality oracle doesn't exist. The ladder from code → formal → scientific → memory/task reasoning is not a capability ladder; it is an **oracle-difficulty ladder, running the wrong way.** And MDL is the right entry point precisely because it **manufactures a gradient where the validity-oracle goes flat.**

Everything below is an unpacking of that sentence.

---

## 1 · The seed observation (Tao) — ✓ verified verbatim

The conversation started from a 量子位 screenshot: *"AI 能做局部优化，做不了全局重构."* The underlying claims are Terence Tao's own, not media embellishment.

| Claim | Status | Source |
|---|---|---|
| Autoformalization now finishes almost any task in hours, but produces **"bloated proofs, often hundreds of lines longer than what a human would choose, with a lot of redundancy, with many lemmas not stated at the natural level of abstraction"** | ✓ verbatim | Tao, Mathstodon `@tao`, thread accompanying his blog post dated **8 June 2026** (terrytao.wordpress.com) |
| **"Impedance mismatch"** between three stages: **proof generation, proof verification, proof digestion**; we are moving **"from an era of proof scarcity to an era of proof abundance"** | ✓ verbatim | Mathstodon posts `116477351524980995`, `116477353989159599` (Apr 2026) |
| AI can do **local "golfs"** that shave code size, but **"global refactoring decisions, such as noticing that a certain argument appears multiple times … and [abstracting it] into a lemma that may have broader applications"** are beyond current tools | ✓ verbatim — **Tao's own words**, not just the Chinese-media gloss | same 8 June 2026 thread |
| Project context: **"Prime Number Theorem and more" (PNT+)**, repo `AlexKontorovich/PrimeNumberTheoremAnd` | ✓ | Tao Mathstodon `111847680248482955` (Feb 2024) |
| ⚠️ The **"IEANTN"** acronym | ⚠️ **media artifact** — the real project is the **"Integrated Explicit Analytic Number Theory Network"** (Tao blog, 15 Jan 2026); "IEANTN" was coined by 36Kr/QbitAI, *not* Tao | flag when citing |
| Strong-PNT: a Jan-2024 Tao–Kontorovich challenge, **stuck ~18 months**, then completed by Math Inc.'s "Gauss" agent in **~3 weeks** (~25k lines Lean, >1000 theorems) | ✓ but **vendor-reported** | math.inc/gauss; `github.com/math-inc/strongpnt` |

**Why it matters:** Tao is describing, from the field's most authoritative vantage and only weeks before this conversation, a clean empirical instance of *valid ≠ short* at industrial scale.

---

## 2 · The question that drove everything: "isn't refactoring what agents are *best* at?"

The apparent paradox: Tao says AI can't refactor proofs; coding agents refactor code all day. **Resolution: the word "refactoring" silently names two different tasks.**

### 2.1 · Two "refactorings"

| | Agent-friendly refactoring | What Tao means by global refactoring |
|---|---|---|
| Task | behavior-preserving local transform | discover the right abstraction, lift a lemma |
| Transform source | a **finite catalog** (Extract Method, Inline…) — instantiation, not invention | **no catalog** — you must *invent* the lemma |
| Scope | local: a function / module | global: the whole development |
| Correctness oracle | tests + types — **cheap, automatic** | **none** |
| "Good" signal | linters, complexity, duplication detectors — **gradient exists** | mathematical taste + future-reuse — **no gradient** |
| Essence | search over **rewrites** | search over **compressions** |

### 2.2 · The etymological trap (your sharpest point)

"Refactoring" *did* come from code — but the concept, since Fowler, was **defined to cover only the half that has an oracle**:

1. The invariant is *observable behavior*, and behavior has a cheap oracle (**the green test suite**).
2. The moves come from a *bounded catalog* — each is pattern instantiation, **not invention**.

Crucially, **"finding the right abstraction" was never part of refactoring even in software.** Applying an abstraction you've already seen is refactoring; *realizing one should exist and inventing the right one* is **design**. The catalog mechanizes execution-after-deciding; it does not decide. So "agents are great at refactoring" = agents are great at *the catalog half*. The design half — the half you're pointing at — was always human, and was deliberately bracketed out of the discipline. The two only *feel* like one task because a skilled person fuses "see abstraction → apply move" in a single sitting.

> **Extra axis:** code's design feedback is *far* richer than a proof's — you can run it, profile it, ship it, watch it break, get it reviewed; abstraction quality shows up in hours. A lemma's quality only cashes out in *future cross-library reuse* — months/years, and never local.

---

## 3 · The crux: the oracle saturates (why Lean makes this *worse*, by design)

This is the technical heart. Coding-agent refactoring works because of a cheap automatic correctness oracle the agent can **hill-climb**: transform → run tests → keep if green. In the proof setting that loop collapses:

- **The oracle is saturated.** A bloated proof *already compiles.* The Lean kernel returns `PASS` for the 1000-line and the 50-line version alike. The green/red signal that drives refactoring is **constant-green** — no hill to climb.
- **"Right abstraction level" has no cheap oracle at all** — it depends on global structure + anticipated future reuse + taste, none checkable in-loop.
- It is **search over abstractions, not over behavior-preserving rewrites.** Finding the minimal generating structure = K-minimization, **uncomputable in general**; in practice it requires *inventing* the lemma.

### 3.1 · Lean's equality is mechanized — but it's the *wrong* equality, on purpose

You asked: shouldn't a formal language give equivalence for free? It gives *an* equality; just not the one refactoring needs.

| Notion of "equal" | Status | Why it's not what refactoring needs |
|---|---|---|
| **definitional / judgmental** (kernel auto-checks) | decidable *in practice* (⚠️ see 3.2) | captures only *computational* sameness; bloated and clean don't compute to each other |
| **propositional** (`Eq`, `a = b`) | *statable* for any terms; *proving* it is undecidable in general | it's about *objects* being equal, not about which *proof* is better |
| **what you actually want** — same theorem, one with better-abstracted/more-reusable lemmas | — | **not an equality at all** — a *preorder on presentations*; **no Lean type's inhabitant is "proofs ranked by quality"** |

**The killer is proof irrelevance.** Lean 4's kernel has **definitional proof irrelevance for `Prop`**: for any `P : Prop` and `h₁ h₂ : P`, the kernel treats `h₁` and `h₂` as *definitionally equal* (✓ Lean docs, *Theorem Proving in Lean 4*, "Propositions and Proofs"). Any theorem *is* a `Prop`. **So the bloated proof and the clean proof are literally the same object at the type level.** The dimension where bloat lives — the proof *as a written, reusable artifact* — is **erased by design.** Lean cannot even *state* "same theorem, but one is better"; at the level of "an inhabitant of this Prop" there is only one thing. The difference lives *before* the kernel (in elaboration, script → term); *after* the kernel, the term-of-a-Prop is irrelevant.

> **The cleanest inversion in the whole arc:** Lean's strength here *is* its blindness. A verifier that cared which proof you used would be a *worse* verifier (it would reject valid proofs on style). **Proof irrelevance is correct for *verification* and fatal for *quality assessment* — two sides of one coin.**

### 3.2 · A warranted hedge (✓ audit-confirmed)

The "decidable in practice" caveat is real, not hand-waving. Lean's kernel type theory is **not strongly normalizing**: Abel & Coquand (2020) gave a counterexample, and the Lean4Lean work (arXiv:2403.14064) notes it can affect definitional-equality checks even for regular types, arising from impredicativity + proof irrelevance + subsingleton elimination. The kernel stays terminating via engineering limits (timeouts, depth caps), **not** a clean decidability theorem.

---

## 4 · The same wall, four more times: the questions probing whether it generalizes

You then stress-tested the thesis from four directions. Each turned out to be the *same* oracle wall wearing different clothes.

### 4.1 · Is shortest-path isomorphic? — **No: navigation vs. cartography**

Isomorphic at the "navigation" layer (proof *search* over a given graph ≈ Dijkstra/A*), **broken** at three points, each the hard part:

1. **The graph isn't given — you must invent nodes.** Global refactoring *introduces a lemma not already in the graph.* That's not shortest-path; it's closer to **Steiner tree** (✓ NP-hard; the distinguishing power is exactly the freedom to *add auxiliary points* to lower total cost — Karp's 21, NP-hard even in the Euclidean plane). And it's *worse* than Steiner: the candidate auxiliary points (possible lemmas) form an infinite, unstructured, semantically-defined set you must **invent**, not enumerate.
2. **No admissible heuristic.** A* optimality needs `h(n) ≤` true cost-to-go (✓ Hart–Nilsson–Raphael 1968); there's no computable lower bound on "distance to clean proof" (K uncomputable).
3. **No goal-membership oracle.** Shortest-path has a named target; here the target is a *quality predicate over the whole structure* — back to the saturated oracle.

> **Maps onto your A/B fork:** Proposal A's bounded grammar 𝒢 *is* the move "make the graph finite & enumerable" — fixing 𝒢 pins the node set, turning it into genuine shortest-path-able program search (tractable, but front-loads structure). Proposal B *refuses* to fix the graph: R's distribution *is* a trajectory prior whose optimization is uncomputable; you optimize only the stopping time τ. So **A vs. B = whether or not you fix the graph.**

### 4.2 · Does HoTT apply? — **Right vocabulary, wrong granularity**

Tempting, because "when are two proofs the same?" is HoTT's native tongue (the identity type `Id_A(p,q)` is a space; refactoring ≈ finding a path/homotopy). But there's a fatal granularity mismatch: for **h-propositions** (mere propositions), *all proofs are equal* (✓ HoTT Book Ch. 3 — a mere prop is "a type in which all elements are equal"). Mathematical theorems are typically h-props. **So HoTT, like Lean's `Prop`, is *designed* to ignore the very dimension where bloat lives** — it operates *above* the level where representation/normalization cost is defined. *(This last sentence is interpretive — see §6 — but the underlying type-theory facts are ✓ verified.)*

The genuinely on-target theory is **proof complexity**, with a beautiful inversion:

- **Cut-elimination runs *opposite* to good refactoring.** Elegance = introducing a well-chosen **cut** (= a **lemma**); **normalization eliminates cuts → inlines lemmas → bloats the proof.** And the cost is enormous: in **first-order** logic, cut-free proofs can be **non-elementarily** (tower-of-exponentials) larger than proofs with cut (✓ Statman 1979; Orevkov 1979/82; Pudlák, *The Lengths of Proofs*, Handbook of Proof Theory 1998, Thm 5.2.3). **This is the rigorous form of "a well-chosen lemma can super-exponentially compress a proof."** (Via Curry–Howard: cut ≈ a `let`/composition = named abstraction; cut-elimination ≈ β-normalization.)
  - ⚠️ **The one qualifier the audit insisted on:** this is **first-order**. In *propositional* logic the cut gap is only **exponential**, not non-elementary (brute-force search over the finite subformula space). **Always say "in first-order logic."** This is the single most important guard against overstating the strongest claim.
- **Extended Frege vs. Frege** is the formal version of "abbreviation shortens proofs" (EF's extension rule lets a big formula be named by one new variable — i.e., EF reasons with *circuits*, not formulas). ✓ And whether EF is *strictly* stronger than Frege is **OPEN, not a proven separation** — proving *any* super-polynomial EF lower bound is itself a major open problem (✓ Cook–Reckhow; Krajíček–Pudlák 1989).

### 4.3 · The capability ladder — **each rung's invariant is false in the same place**

The proposed ladder: do code refactoring → formal-reasoning refactoring → scientific-reasoning refactoring → memory-preserving / task-lossless refactoring. The implication is false at *every* rung, and always for the same reason — it swaps *transformation capability* for *whole-task capability*, dropping the oracle term, **and the oracle gets strictly harder going up.**

| Rung | Validity oracle | Why the implication breaks |
|---|---|---|
| Code refactoring | tests + types — cheap, automatic ✓ | — (the **only** rung with a cheap oracle) |
| Formal-reasoning refactoring | exists but **saturated** (all compile) | no quality gradient to climb |
| Scientific-reasoning refactoring | **no crisp oracle** (empirical, defeasible) | even "valid" isn't a clean predicate |
| Memory-preserving / task-lossless | = **semantic equivalence / sufficiency** — hardest | the needed equivalence oracle doesn't exist |

Going up, the checking machinery is stripped one layer at a time: behavioral oracle → saturated validity → no crisp validity → needed semantic-equivalence judgment. **It's an oracle-difficulty ladder pointing the wrong way.** Coding agents look strong only because they happen to stand on the one rung with a cheap oracle; remove it and the same model wilts — proof-bloat is exactly "same model, oracle removed, quality dimension collapses."

> **Honest steelman (kept in):** transformation *primitives* may well transfer; as oracles improve (better LLM-judges, autoformalization shrinking the empirical→formal gap), higher rungs become gradually tractable. So the implication isn't logically empty — it's missing a hidden premise *"AND the next rung's oracle exists,"* which currently fails at every rung. **This is precisely why OpenPriors matters: it is an attempt to *manufacture the missing oracle*** — to supply a gradient in the regime where compile-pass says nothing.

### 4.4 · Why isn't MCTS enough for high-quality AI scientific research? — **it amplifies reward, it can't create it**

MCTS needs four things; open-ended science breaks all four, and the fourth is the killer:

| MCTS needs | Go / Lean | Open-ended science |
|---|---|---|
| enumerable action space | legal moves / tactics ✓ | hypotheses/abstractions must be **invented** (the "invent nodes" problem again) |
| cheap rollout to terminal | seconds ✓ | "push a direction to its end" = months / real experiments — **no fast forward model** |
| **terminal reward** | win/loss; proved/not (Lean kernel) ✓ | **"is this good / a real contribution / actually novel"** has no cheap unambiguous signal |
| many cheap iterations | millions of playouts | each playout = compute/experiments — **scale mismatch** |

Row 3 is decisive. AlphaProof is strong *because* Lean hands it a clean terminal oracle to climb — and AlphaZero can even *bootstrap a value network* from terminal rewards (✓ AlphaProof: LM + AlphaZero RL with Lean as verifier, ~80M auto-formalized statements, **silver at IMO 2024, 28/42** — Nature, 12 Nov 2025; DeepMind blog). Science has no self-play loop with a built-in terminal truth — **you can't even *learn* the evaluator the way AlphaZero does.** Feed MCTS a noisy/gameable proxy and it will faithfully **Goodhart** it — producing things that *look* novel and *sound* rigorous rather than *being* so. So **MCTS isn't a solution to scientific research; it presupposes the solved version of it (the oracle).** Same sentence as the coding-agent case, restated.

---

## 5 · Is MDL the right entry point? — qualified yes

**As an *objective*: yes — probably the only right one. As a *method*: necessary but not sufficient.**

✅ **Why it's right:**
- Stripped to the core, the problem *is* compression: "how much of T is redundant given Σ" = conditional description length. Bloat *literally is* "won't compress" = high L. MDL is not a metaphor here; it's the native form.
- **The strongest reason:** MDL is **the quantity that stays discriminative after the validity-oracle saturates.** `compile = PASS` is constant; description length still varies. L_π supplies a continuous signal exactly where the oracle goes flat. This is the through-line of the entire conversation.
- Separating costs (L_R vs. L_π) maps onto two distinct kinds of legitimate labor (curation vs. reasoning) — structure a flat similarity score can't express.

⚠️ **Two constraints that must be made explicit:**
1. **MDL is the scoreboard, not the player.** It *scores* (clean is shorter), but doesn't *tell you how to find* the short proof — that's the "invent the lemma / worse-than-Steiner" search of §4.1. The complete entry point = **MDL objective + a search/generation half** (A's grammar to bound the space, or B's R as generator). Your A/B fork already supplies that half, so the *whole* system is well-posed; but "the MDL formulation" *alone* is the right objective + an incomplete method.
2. **The coding scheme / 𝒢 must be closed under abstraction-introduction.** Because a lemma = a cut = potentially non-elementary compression (§4.2), description length **must be measured in a system that permits naming/abstraction** — otherwise you literally cannot represent the good short proof, and MDL systematically misjudges (treats the inlined version as "the proof," blind to the cut that would compress it). **The model class must be able to express the very abstractions whose presence you're trying to measure.** This is also why L_π must be read on the *script / abstraction-bearing term*, never on the proof-irrelevant `Prop` inhabitant (§3.1) — the latter has only one element.

🤔 **One hedge + one alternative (kept for even-handedness):**
- The whole thing rests on **L approximating K** — an empirical bet (your own open problem). MDL is solid as a *principle*, fully model-class-relative as a *number* ("MDL is a principle, not a number"). The formulation's correctness is *mortgaged* to proxy quality.
- **Alternative for the formal-proof special case:** do it as **proof complexity** directly — there you get *lower-bound theorems* ("this proof must be long in system S") that MDL + an LLM-proxy can't give. Trade-off: proof complexity has hard theorems but only in a narrow formal setting; MDL generalizes to science/memory but only via noisy proxies. **Choosing MDL = choosing breadth-with-proxies over depth-with-theorems** — defensible for your cross-domain ambition, but it should be a *conscious* choice.

---

## 6 · Epistemic ledger (three tiers, kept separate)

**Tier 1 — verified against primary sources (✓):** All Tao quotes (§1, his Mathstodon/8-Jun-2026 blog); TacMiner's numbers (26% size reduction, 3× tactics vs. Peano — OOPSLA 2025 / arXiv:2503.24036); APOLLO's figures (65.6% / 362 samples; 3–7%→40% — arXiv:2505.05758); Lean definitional proof irrelevance (Lean docs); Lean non-strong-normalization hedge (arXiv:2403.14064; Abel–Coquand 2020); first-order non-elementary cut-elimination (Statman/Orevkov/Pudlák); Extended-Frege-vs-Frege open (Cook–Reckhow; Krajíček–Pudlák); HoTT h-prop proof irrelevance (HoTT Book Ch. 3); Kolmogorov uncomputability (Li–Vitányi); Levin Kt; Steiner NP-hardness; A* admissibility (Hart–Nilsson–Raphael 1968); AlphaProof silver IMO 2024, 28/42 (Nature, 12 Nov 2025).

**Tier 1 with required qualifiers (⚠️):** "non-elementary cut blowup" is **first-order only** (propositional = exponential). "IEANTN" is a **media coinage**; real name = Integrated Explicit Analytic Number Theory Network. Strong-PNT "3 weeks / stuck 18 months" is **vendor-reported** (Math Inc.). Seed-Prover IMO 2025 = **in-contest silver 30/42**, IMO-certified; the "5/6" and Seed-Prover-1.5 "gold-cutoff 35/42" are **post-contest / later-version**. APOLLO "84.9% sub-8B" is **"as of Aug 2025," a later revision** (v1 said 75.0% at 7B).

**Tier 2 — defensible interpretive mappings (mine, not a source's):** cut-elimination ↔ "refactoring in reverse"; Lean `Prop` / HoTT h-props "operate above where bloat lives"; the A/B fork ↔ "fix the graph or not"; Steiner-worse-than-Steiner as the model for lemma invention; the ladder as an inverted oracle-difficulty ladder; "MCTS presupposes the solved problem." Each is grounded in ✓ facts but is an argument, not a citation.

**Tier 3 — the organizing thesis (§0):** that *the oracle is the universal bottleneck and MDL's value is manufacturing a gradient where the validity-oracle saturates* — a synthesis claim this note advances, not an established result.

---

## 7 · Carry-forward hooks for OpenPriors

- **A naturally-occurring Part III test pair.** Tao's PNT+ / explicit-analytic-number-theory corpus contains *the same theorem proved two ways* — an AI-bloated version and a human-refactored Mathlib-quality version. That's a ready-made **L_π calibration pair** (long-trivial vs. short-conceptual). ⚠️ It is an **L_π calibration case, not a novelty/concealment case** — both bridges hit the *same* target, conceptual distance ≈ 0.
- **Measure L_π in conceptual commitments, not raw length.** Bloated proofs are long in *tokens*, short in *genuine steps*. Token-level surprisal would **over-count** L_π; step-boundary first-token surprisal (the ASAP route) would correctly read "short bridge in a long coat." Direct empirical support for your "count commitments, not length" stance — and for why the three-term objective beats a constrained two-term one (residual ⊥ bridge-length is exactly what proof-bloat demonstrates).
- **The single correction to propagate into v1/v2:** wherever the cut-compression argument appears, **pin it to first-order logic** (propositional = merely exponential). It's the one place the strongest claim could otherwise be technically overstated.

---

*Sources to cite directly (not via aggregators): Tao's Mathstodon `@tao` and terrytao.wordpress.com (not 36Kr/QbitAI/Phemex); Pudlák, "The Lengths of Proofs" (Handbook of Proof Theory, 1998); arXiv:2503.24036 (TacMiner); arXiv:2505.05758 (APOLLO); Lean 4 docs (proof irrelevance); arXiv:2403.14064 (Lean4Lean); the HoTT Book (h-props); Li–Vitányi (Kolmogorov); Hart–Nilsson–Raphael 1968 (A*); Nature 12 Nov 2025 (AlphaProof). Mid-2026 Mathstodon post IDs/dates should be confirmed on the live feed before any external publication.*

# Structure-Mapping & Analogy Models — Research Notes

*Reference document for **OpenPriors** — a novelty detector.*
*Compiled May 3, 2026.*

-----

## Table of Contents

1. [Structure-Mapping Theory (Gentner 1983)](#1-structure-mapping-theory-smt)
1. [The Structure-Mapping Engine (SME)](#2-the-structure-mapping-engine-sme)
1. [MAC/FAC — retrieval at scale](#3-macfac--retrieval-at-scale)
1. [ACME — analogical mapping by constraint satisfaction](#4-acme--analogical-mapping-by-constraint-satisfaction)
1. [LRME — analogy from text corpora alone](#5-lrme--analogy-from-text-corpora-alone)
1. [Candidate inference scoring — the “shortcut detector”](#6-candidate-inference-scoring--the-shortcut-detector)
1. [Synthesis: pipeline mapping for OpenPriors](#7-synthesis-pipeline-mapping-for-openpriors)
1. [Primary sources](#8-primary-sources)

-----

## 1. Structure-Mapping Theory (SMT)

> 📚 **Refs**
> • Gentner, D. (1983) “Structure-mapping: A theoretical framework for analogy,” *Cognitive Science* 7(2):155–170. [PDF](https://groups.psych.northwestern.edu/gentner/papers/Gentner83.2b.pdf)
> • Gentner, D. & Markman, A. B. (1997) “Structure mapping in analogy and similarity,” *American Psychologist* 52:45–56.
> • Gentner, D. & Maravilla, F. (2018) “Analogical reasoning,” in *International Handbook of Thinking and Reasoning*. [PDF](https://groups.psych.northwestern.edu/gentner/papers/GentnerMaravilla_2018-Handbook.pdf)

### 🧭 One-line intuition

**Analogy = aligning *relations*, not *attributes*.** “Atom is like the solar system” works not because atoms and suns share color/temperature, but because both instantiate the *same relational system* (smaller things orbit a central attractor under inverse-square force). SMT formalizes this by saying: a good analogy is a **structure-preserving partial map** between two representations, scored by how much *higher-order relational structure* it preserves.

This is *exactly* the engine a novelty detector needs: it’s about **isomorphism under renaming**, not lexical overlap.

### 🎯 Motivation (what problem it solves)

Pre-1983, “similarity” was a mush — feature overlap (Tversky), holistic gestalt, vibes. Gentner’s move: **separate two kinds of similarity**:

|Kind                  |Shares attributes|Shares relations|Example            |
|----------------------|-----------------|----------------|-------------------|
|**Literal similarity**|✅                |✅               |sparrow ↔ robin    |
|**Analogy**           |❌                |✅               |atom ↔ solar system|
|**Mere appearance**   |✅                |❌               |sun ↔ orange       |
|**Anomaly**           |❌                |❌               |atom ↔ haircut     |

The **target phenomenon** to model: humans systematically prefer the analogy interpretation over the appearance one when the relational match is deep, even when surface features align poorly.

### 🧱 Representational assumptions (the price of admission)

SMT assumes inputs are **typed predicate-calculus expressions**, not raw text. Each domain is a set of:

- **Entities / objects** — `sun, planet, nucleus, electron`
- **Attributes** (1-place predicates) — `YELLOW(sun)`, `MASSIVE(sun)`
- **Functions** — map entities to values: `MASS(sun)`, `TEMPERATURE(sun)`
- **Relations** (n-place predicates) — `GREATER(MASS(sun), MASS(planet))`, `ATTRACTS(sun, planet)`
- **Higher-order relations** — relations *over* relations, esp. `CAUSE`:
  `CAUSE( AND(GREATER(MASS(sun), MASS(planet)), ATTRACTS(sun, planet)), REVOLVES(planet, sun) )`

The **order** of a predicate = 1 + max order of its arguments (objects = order 0). Higher-order = deeper.

> ⚠️ This structured-representation requirement is SMT’s biggest liability for the paper-analysis use case — papers come as text, not predicate calculus. Modern extensions (e.g., Forbus’s Companion architecture and CogSketch) try to bridge this; LRME (§5) tries another route.

### 📜 The three structural principles + selection principle

A candidate analogy is a partial mapping `M : Base → Target` — it sends each Base entity to a Target entity, and each Base predicate to a Target predicate. `M` is structurally consistent iff:

**1. Identicality of predicates.** When `M` matches a Base predicate `R_B` to a Target predicate `R_T`, the two must be the *same symbol* (`R_B = R_T`). Later “minimal ascension” variants relax this: matches are also allowed when `R_B` and `R_T` share a parent in a predicate type hierarchy (e.g., `MINIMIZE` and `OPTIMIZE` both inherit from `OBJECTIVE-OPERATOR`).

**2. Parallel connectivity.** If `M` aligns `R_B ↔ R_T`, the arguments of the two predicates must align in the *same positions*. Writing the arguments of `R_B` as `x_1, ..., x_n`:
$$M(R_B(x_1, \ldots, x_n)) = R_T(M(x_1), \ldots, M(x_n))$$

**3. One-to-one correspondence.** `M` is a partial bijection on entities: no Base entity maps to two Target entities, and no Target entity is the image of two Base entities.

**4. Systematicity (the selection principle).** Among mappings satisfying 1–3, *prefer the one preserving the most deeply nested, mutually-constraining relational structure* — especially `CAUSE` and other higher-order relations. A predicate connected to a big interconnected web is much more “mappable” than an isolated one.

> 🎯 *Systematicity* is the formal version of the intuition that we want to find a **minimal generating backbone** — the deeply-nested causal scaffolding — rather than a bag of surface features.

-----

## 2. The Structure-Mapping Engine (SME)

> 📚 **Refs**
> • Falkenhainer, B., Forbus, K. D. & Gentner, D. (1989) “The structure-mapping engine: Algorithm and examples,” *Artificial Intelligence* 41:1–63. [PDF](https://groups.psych.northwestern.edu/gentner/papers/FalkenhainerForbusGentner89.pdf)
> • Forbus, K. D., Ferguson, R. W., Lovett, A. & Gentner, D. (2017) “Extending SME to handle large-scale cognitive modeling,” *Cognitive Science* 41(5):1152–1201. [Wiley](https://onlinelibrary.wiley.com/doi/10.1111/cogs.12377) · [PDF](https://groups.psych.northwestern.edu/gentner/papers/ForbusFergusonLovett&Gentner_inPress.pdf)
> • [SME-clj](https://github.com/svdm/SME-clj) (open-source Clojure implementation) · [QRG software](https://www.qrg.northwestern.edu/software/software_index.html) (Forbus group)

The canonical computational realization of SMT.

**Input:** two structured descriptions (Base + Target).
**Output:** 1–3 “Gmaps” (global mappings), each with object/predicate correspondences, a **structural evaluation score**, and **candidate inferences**.

### 🔄 Pipeline

```
[Base] [Target]
   ↓     ↓
(1) Local Match Construction → all (b_i, t_j) where predicates compatible → Match Hypotheses (MHs)
                              ↓
(2) Compute structural-consistency relations between MHs (require/conflict)
                              ↓
(3) Trickle-down evidence: each MH gets a score; parent MHs pass score down to children
                              ↓
(4) Greedy merge of MHs into maximal consistent sets → Gmaps (no backtracking!)
                              ↓
(5) For each Gmap: compute candidate inferences (base structure connected to mapped part
                   but with no target counterpart → projected as new hypothesis about target)
```

### 🧮 The scoring core

Each MH gets local evidence based on match type (function vs. relation, same vs. different functor, predicate order). Then evidence **propagates downward** via *trickle-down*: an MH gets a fraction of the score of every parent MH that requires it. Net effect:

> **An MH inside a deep, well-connected relational web accumulates much more score than an isolated one.** This is how “systematicity” is mechanized.

Evidence combination uses Dempster’s rule (the standard formula in Dempster–Shafer evidence theory for fusing independent positive/negative evidence sources into a single belief score in [0,1]).

### ⏱️ Complexity

Most steps are **O(N²)** in description size; the merge step is the expensive part but tractable in practice via greedy heuristics.

### 🌟 Candidate inferences = the transplant detector

If Base contains `CAUSE(P, Q)` and `P` maps to Target’s `P'` but `Q` has no counterpart in Target — SME projects `Q'` as a **predicted but not-yet-stated property of the Target**. This is precisely the formal trace of *“this target work is just running the source’s machinery on relabeled objects.”*

### 🧬 Important successors

|Model                      |Year |What it adds                                                    |
|---------------------------|-----|----------------------------------------------------------------|
|**MAC/FAC**                |1995 |Two-stage retrieval: cheap content-vector filter → expensive SME|
|**SAGE / SEQL**            |2000s|Generalization across multiple analogs → schema induction       |
|**SME 4 / large-scale SME**|2017 |Greedy variant scaling to 10⁴+ items                            |
|**ACME**                   |1989 |Rival: constraint-satisfaction network instead of symbolic      |
|**LRME**                   |2008 |Removes hand-coded representation requirement                   |

-----

## 3. MAC/FAC — retrieval at scale

> 📚 **Refs**
> • Forbus, K. D., Gentner, D. & Law, K. (1995) “MAC/FAC: A model of similarity-based retrieval,” *Cognitive Science* 19(2):141–205. [PDF](https://groups.psych.northwestern.edu/gentner/papers/ForbusGentnerLaw94.2b.pdf) · [Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1207/s15516709cog1902_1)
> • Law, K., Forbus, K. D. & Gentner, D. (1994) “Simulating similarity-based retrieval: A comparison of ARCS and MAC/FAC,” *Proceedings of CogSci 1994*.
> • [eScholarship summary](https://escholarship.org/uc/item/1gb7n02g)

### 🧭 One-line intuition

**“Many Are Called, Few Are Chosen.”** You can’t run expensive structural matching against every paper in arXiv. So do a **cheap surface filter first** to short-list ~10 candidates, then run SME on those.

This *is* the formal answer to the “indexing burden” worry.

### 🎯 The motivation paradox it solves

Three empirical findings about human memory that look contradictory:

1. **Comparison** is dominated by *structural* similarity (when items are side-by-side in working memory).
1. **Retrieval** is dominated by *surface* similarity (you get reminded of stories with similar characters, not similar plots).
1. Yet **purely structural remindings** — the rare “Aha!” moment — really do happen.

A unified mechanism has to explain why surface dominates retrieval *but isn’t all there is*.

### 🧱 The model

```
                    Probe (current target description)
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │   MAC stage: cheap content vector   │   ← O(N) over all of LTM (long-term memory)
        │   dot products vs every memory item │
        └─────────────────────────────────────┘
                          │ top-k (≈1–3 items)
                          ▼
        ┌─────────────────────────────────────┐
        │   FAC stage: full SME structural    │   ← O(N²) on small set
        │   match on the survivors            │
        └─────────────────────────────────────┘
                          │
                          ▼
                Best matches + candidate inferences
```

### 🧮 The mathematical trick: **content vectors**

You can build a **flat bag-of-predicates vector** from a structured representation that approximates what SME would compute, *cheaply*.

Given a structured description $D$ with predicates ${P_1, P_2, \ldots}$:

$$\mathbf{v}(D)_i = \text{count of predicate type } i \text{ in } D$$

Then surface similarity is:
$$\text{MAC-score}(D_1, D_2) = \mathbf{v}(D_1) \cdot \mathbf{v}(D_2)$$

**Key property** (informal): the dot product of content vectors is an *upper bound* on the SME structural score. Items that score low on MAC *cannot* score high on FAC, so filtering is sound.

### 🔌 Project relevance

This is **literally the architecture for “renaming-invariant retrieval at scale.”** Modern reformulation: replace MAC’s content vectors with **dense neural embeddings of relational tuples** (e.g., embed (subject, relation, object) triples), keep FAC’s structural verifier. This is essentially what dense retrieval + reranking does in modern IR, with the twist that the reranker should be doing structural alignment, not just cross-encoder semantic similarity (a cross-encoder = a transformer that scores the (query, candidate) pair *jointly* in one forward pass, capturing token-level interactions but ignoring relational structure).

-----

## 4. ACME — analogical mapping by constraint satisfaction

> 📚 **Refs**
> • Holyoak, K. J. & Thagard, P. (1989) “Analogical mapping by constraint satisfaction,” *Cognitive Science* 13(3):295–355. [Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1207/s15516709cog1303_1) · [PDF](https://studylib.net/doc/14538441/analogical-mapping-by-constraint-satisfaction-j.-thagard-...)
> • Holyoak, K. J., Novick, L. R. & Melz, E. R. (1994) “Component processes in analogical transfer: mapping, pattern completion, and adaptation” — extension of ACME to inference projection.
> • Thagard, P., Holyoak, K. J., Nelson, G. & Gochfeld, D. (1990) “Analog retrieval by constraint satisfaction” — ARCS, the sister system that handles retrieval (the ACME family’s analog of MAC/FAC).
> • Eliasmith, C. & Thagard, P. (2001) “Integrating structure and meaning: a distributed model of analogical mapping,” *Cognitive Science* 25(2):245–286 — distributed-representation successor (DRAMA).

### 🧭 One-line intuition

**Don’t make analogy a hard symbolic search; make it a soft optimization.** Cast every potential correspondence as a node in a neural-style network where supporting correspondences excite each other and conflicting ones inhibit, then let activation settle to find a coherent mapping.

### 🎯 Motivation: SME’s three blind spots (per Holyoak & Thagard)

1. **No semantics**: SME’s strict identicality means `MINIMIZE` and `OPTIMIZE` can’t match, even though they’re near-synonyms.
1. **No pragmatics**: SME ignores the *purpose* of the analogy.
1. **All-or-nothing structural consistency**: SME enforces 1-1 and parallel connectivity as hard constraints, but humans gracefully tolerate small violations.

ACME (Analogical Constraint Mapping Engine) makes all three **soft, simultaneous constraints**.

### 🧱 The three constraints (the multiconstraint theory)

|Constraint                  |What it favors                                    |Hard or soft?|
|----------------------------|--------------------------------------------------|-------------|
|**Structural (isomorphism)**|1-1 correspondences, parallel connectivity        |Soft pressure|
|**Semantic**                |Mappings between predicates with similar *meaning*|Soft         |
|**Pragmatic**               |Mappings involving elements important to the goal |Soft         |

The analogy is the **joint optimum** of all three.

### 🧮 The algorithm: parallel constraint satisfaction

Build a **localist connectionist network**:

- **Units** = candidate match hypotheses, e.g., a unit for “$\text{Saddam} \leftrightarrow \text{Hitler}$”.
- **Excitatory links** between mutually supporting hypotheses.
- **Inhibitory links** between competing hypotheses (Saddam→Hitler inhibits Saddam→Stalin).
- **Special “semantic” unit** linked to each hypothesis with weights given by predicate similarity.
- **Special “pragmatic” unit** linked to flagged-important hypotheses.

Run a standard localist activation update until the network settles. Each unit $j$ — corresponding to one match-hypothesis like `Saddam ↔ Hitler` — has an activation $a_j(t) \in [-1, +1]$ at discrete step $t$, updated by combining a decayed prior activation with a contribution from its weighted input:

$$a_j(t+1) = a_j(t)(1-d) + \text{net}_j(t) \cdot \begin{cases} 1 - a_j(t) & \text{if } \text{net}_j(t) > 0 \ a_j(t) + 1 & \text{otherwise} \end{cases}$$

Here $d \in (0, 1)$ is a decay constant pulling activations toward 0; $\text{net}*j(t) = \sum_i w*{ij}, a_i(t)$ is the total weighted input from neighboring units; and $w_{ij}$ is the weight on the link from unit $i$ to unit $j$ — positive for excitatory pairs (mutually supporting hypotheses), negative for inhibitory ones (competing hypotheses). The piecewise factor squashes the contribution so activations stay within $[-1, +1]$. Iterate to convergence; units with positive asymptotic activation form the accepted mapping.

### ⚖️ SME vs. ACME — the deep dispute

|                           |**SME** (Gentner)                                  |**ACME** (Holyoak/Thagard)                    |
|---------------------------|---------------------------------------------------|----------------------------------------------|
|Identicality               |Hard — must match                                  |Soft — semantic similarity in [0,1]           |
|1-1 / parallel connectivity|Hard structural constraints                        |Soft (inhibitory pressure only)               |
|Goal/pragmatics            |Outside the mapping process (affects encoding only)|First-class constraint inside the mapping     |
|Backbone                   |Higher-order causal/relational systematicity       |Coherence over all three constraint types     |
|Substrate                  |Symbolic search + greedy merge                     |Localist neural-net relaxation                |
|Output                     |Few discrete Gmaps with candidate inferences       |Continuous activations → one preferred mapping|


> 🔌 **Project relevance:** ACME’s soft semantics is what’s needed for the “MINIMIZE ≈ OPTIMIZE” problem. SME’s systematicity is what’s needed for “minimal causal-derivation backbone.” A hybrid — SME’s structural rigor + ACME’s soft predicate matching via embeddings — is essentially what modern neural-symbolic analogy systems aim at.

-----

## 5. LRME — analogy from text corpora alone

> 📚 **Refs**
> • Turney, P. D. (2008) “The Latent Relation Mapping Engine: Algorithm and experiments,” *JAIR* 33:615–655. [arXiv](https://arxiv.org/abs/0812.4446) · [JAIR](https://jair.org/index.php/jair/article/view/10583)
> • Turney, P. D. (2006) “Similarity of semantic relations,” *Computational Linguistics* 32(3):379–416 — the LRA framework that LRME builds on.
> • Turney, P. D. (2005) “Measuring semantic similarity by latent relational analysis,” *IJCAI-05*, pp. 1136–1141 — the original LRA paper.

### 🧭 One-line intuition

**SME’s biggest weakness is that someone has to hand-code the predicate-calculus representations. LRME (Turney 2008) replaces that with statistics over a large text corpus.** No hand-coded knowledge — just word lists.

### 🎯 Why this is the most relevant model for OpenPriors

The input is “scientific papers.” Nobody is going to hand-write `CAUSE(GRADIENT(LOSS), MINIMIZATION(THETA))` for every paper. LRME shows you can get a long way without it.

### 🧱 The setup

Inputs:

- A **base term list** $B = {b_1, \ldots, b_m}$ — e.g., `{solar system, sun, planet, mass, gravity}`
- A **target term list** $T = {t_1, \ldots, t_m}$ — e.g., `{atom, nucleus, electron, charge, electrostatic}`

Goal: a bijection $M : B \to T$ that maximizes total relational coherence.

### 🧮 The mathematical core: latent relational vectors

The key move from Turney’s Latent Relational Analysis (LRA): represent the **relation between two words** as a vector in a corpus-derived space.

For an ordered pair $(x, y)$, scan a giant corpus for sentences containing both $x$ and $y$ within a window. The vector is:
$$\mathbf{r}(x, y)_p = \text{frequency of pattern } p \text{ between } x \text{ and } y$$

where patterns are short strings like “$x$ orbits $y$”, “$x$ attracts $y$”, “$x$ is part of $y$”. The vector is dimensionality-reduced via SVD (singular value decomposition — collapses synonymous patterns into shared dimensions).

The **relational similarity** between two pairs:
$$\text{relsim}((b_i, b_j), (t_i, t_j)) = \cos(\mathbf{r}(b_i, b_j), \mathbf{r}(t_i, t_j))$$

This implements an SMT-style relational match without ever naming the relation.

### 🔍 The mapping algorithm

LRME’s mapping objective:
$$M^* = \arg\max_{M : B \to T} \sum_{i \neq j} \text{relsim}\big((b_i, b_j), (M(b_i), M(b_j))\big)$$

This is an **assignment problem** (bipartite matching, max-weight) — solved with the Hungarian algorithm in polynomial time.

### 🎯 Result

On 20 analogy problems (10 scientific analogies, 10 common metaphors — e.g., solar-system→atom, water-flow→heat-flow), LRME reaches **human-level performance** without any hand-coded knowledge — only a corpus.

### ⚠️ Limitations to know

- **Bijective only**: $|B| = |T|$. For OpenPriors, sources and targets won’t have the same cardinality, so an extension is needed (greedy, or unbalanced optimal transport).
- **No higher-order structure**: it captures pairwise relations beautifully but doesn’t natively encode `CAUSE(R_1, R_2)`. Loses the systematicity backbone.
- **Corpus-bias**: a novel paper introducing a relation never seen in the corpus can’t be represented.

> 🔌 **Project relevance:** LRME is the missing link between SME-style alignment and modern LLM-based extraction. The 2026 reformulation: replace pattern vectors with **dense embeddings of relational tuples extracted by an LLM**, keep the assignment-problem formulation. Combine with SME post-hoc to recover higher-order systematicity.

-----

## 6. Candidate inference scoring — the “shortcut detector”

> 📚 **Refs**
> • Falkenhainer, B., Forbus, K. D. & Gentner, D. (1989) §3.4–3.5 — original SME formalization of candidate inferences. [PDF](https://groups.psych.northwestern.edu/gentner/papers/FalkenhainerForbusGentner89.pdf)
> • Forbus, K. D., Ferguson, R. W., Lovett, A. & Gentner, D. (2017) — modern formalization including skolem handling and inference scoring. [PDF](https://groups.psych.northwestern.edu/gentner/papers/ForbusFergusonLovett&Gentner_inPress.pdf)
> • Clement, C. A. & Gentner, D. (1991) “Systematicity as a selection constraint in analogical mapping,” *Cognitive Science* 15(1):89–132 — empirical evidence humans prefer systematicity-anchored inferences. [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/036402139180014V)
> • Markman, A. B. (1997) “Constraints on Analogical Inference” — argument-mapping constraints on which inferences get projected. [Cogprints archive](https://web-archive.southampton.ac.uk/cogprints.org/628/1/markman.html)
> • Bowdle, B. F. & Gentner, D. (1997) “Informativity and asymmetry in comparisons,” *Cognitive Psychology* 34(3):244–286 — directional asymmetry in inference projection.

This is the part of SME that **directly implements** the intuition about “revealing the hidden shortcut under fancy disguise.”

### 🧭 One-line intuition

Once Base and Target are aligned structurally, anything connected to the aligned structure in Base **but not yet in Target** gets *projected* across the mapping as a prediction about Target. If the projection turns out to be true (or trivially derivable in Target), then Target was effectively *running Base’s machinery on relabeled objects*.

This is the formal counterpart of the “intellectual-property judge” framing from OpenPriors’s original motivation doc.

### 🧱 The mechanics

After SME settles on a global mapping $M$ between Base $\mathcal{B}$ and Target $\mathcal{T}$:

**Candidate inference** = a predicate $\phi \in \mathcal{B}$ such that:

1. $\phi$ is *connected* (via shared arguments or higher-order relations) to predicates in $\mathcal{B}$ that *are* mapped by $M$.
1. $\phi$ itself has *no counterpart* in $\mathcal{T}$.
1. $\phi$ can be projected by substitution: $M(\phi)$ uses existing entity correspondences for arguments that appear in $M$, and introduces **skolem entities** for arguments that don’t.

### 🧮 The scoring

Each candidate inference gets a score derived from:

$$\text{score}(\phi) = \alpha \cdot \text{StructuralScore}(M) + \beta \cdot \text{Connectedness}(\phi, M) - \gamma \cdot \text{SkolemPenalty}(\phi)$$

where $\alpha, \beta, \gamma > 0$ are tunable non-negative weights (set per implementation), and:

- **StructuralScore($M$)** is the systematicity-weighted score of the global mapping (deeper match = more credible projection).
- **Connectedness($\phi, M$)** counts how many edges of the matched system the inference $\phi$ is anchored to.
- **SkolemPenalty($\phi$)** punishes inferences that require *making up new entities* in Target (these are weaker projections).

The trickle-down evidence machinery (deep relations propagate score down to their argument matches) means **inferences attached to deep causal systems are scored highest**.

### 🎯 Why this is precisely the detector

The two desiderata, restated:

> 1. *Cheap to acquire* (don’t devalue obscure source); 2. *Cheap to build from* (short logical distance, reveals the shortcut).

In SME’s terms:

- **(1) ↔ MAC/FAC retrieval cost** + content-vector similarity — you found the source efficiently.
- **(2) ↔ depth of the projected inferences** — the target’s “novel” content is recoverable as a one-step projection from the source’s structure under the mapping. **A short projection from a deep mapping = exposed shortcut.**

The detector signal:

$$\text{ShortcutFlag} \propto \frac{\text{Coverage of Target by candidate inferences from Source}}{\text{Description length of the alignment } M}$$

This is **structural-alignment-based MDL** (minimum description length): if a short mapping projects almost all of the target, the target is a transplant.

### 📊 Empirical validation

Clement & Gentner (1991) and Markman (1997) showed humans systematically prefer candidate inferences that are deeply embedded in the matching causal/relational system, and reject inferences from isolated matches — exactly the bias the novelty judge needs.

-----

## 7. Synthesis: pipeline mapping for OpenPriors

|Pipeline stage                          |Cognitive-sci ancestor           |2026 modernization                                                                                                           |
|----------------------------------------|---------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
|**Encode papers as relational graphs**  |(none — assumed by SMT)          |LLM-based relation extraction → typed knowledge graph                                                                        |
|**Index millions of sources**           |MAC stage of MAC/FAC             |Dense embeddings of relational tuples + ANN search (approximate nearest neighbor — sub-linear search using e.g. FAISS / HNSW)|
|**Soft semantic matching of predicates**|ACME’s similarity table          |Predicate-embedding cosine, type-lattice ascension                                                                           |
|**Find best structural mapping**        |SME / FAC stage / LRME assignment|SME-style greedy merge over LLM-encoded graph                                                                                |
|**Detect “fancy disguise”**             |Candidate-inference projection   |Coverage of target by source-projected inferences ÷ mapping description length                                               |
|**Pragmatic / goal salience**           |ACME’s pragmatic constraint      |LLM-derived weighting of central-claim predicates                                                                            |

### Mapping back to OpenPriors’s original framing

|Original concept                          |Counterpart in this literature                                                            |
|------------------------------------------|------------------------------------------------------------------------------------------|
|“Renaming-invariant retrieval”            |The mapping `M` *is* a renaming; identicality + parallel connectivity make it well-defined|
|“Minimal generating backbone”             |Systematicity-maximizing Gmap                                                             |
|“Hidden shortcut under fancy disguise”    |Candidate inferences from a high-systematicity Gmap                                       |
|“Conceptual/logical distance proxy”       |(1 − normalized structural evaluation score) of the best Gmap                             |
|“Ontology problem”                        |Tiered identicality / minimal ascension over a predicate type hierarchy                   |
|“Indexing burden over millions of sources”|MAC/FAC two-stage retrieval                                                               |

### Two big caveats for adoption

1. **Encoding bottleneck.** SME assumes someone produced the predicate-calculus representation. For papers, you need an LLM-based front end to extract relational structure (entities, relations, causal/derivational graph) — and the **quality of the encoding dominates results**. This is the “powerful pre-trained model” half of the task.
1. **Identicality is brittle.** Two papers using `MINIMIZE` vs. `OPTIMIZE` on equivalent objectives will fail strict identicality. Need either learned predicate-equivalence (embeddings) or aggressive type-lattice ascension. ACME’s soft semantics or LRME’s corpus-based relational vectors are the canonical fixes.

-----

## 8. Primary sources

### Foundational

- **Gentner (1983)** “Structure-mapping: A theoretical framework for analogy,” *Cognitive Science* 7(2):155–170. [PDF (Northwestern)](https://groups.psych.northwestern.edu/gentner/papers/Gentner83.2b.pdf)
- **Falkenhainer, Forbus & Gentner (1989)** “The structure-mapping engine: Algorithm and examples,” *Artificial Intelligence* 41:1–63. [PDF (Northwestern)](https://groups.psych.northwestern.edu/gentner/papers/FalkenhainerForbusGentner89.pdf)

### Retrieval at scale

- **Forbus, Gentner & Law (1995)** “MAC/FAC: A model of similarity-based retrieval,” *Cognitive Science* 19(2):141–205. [PDF (Northwestern)](https://groups.psych.northwestern.edu/gentner/papers/ForbusGentnerLaw94.2b.pdf) · [Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1207/s15516709cog1902_1)

### Analogy by constraint satisfaction

- **Holyoak & Thagard (1989)** “Analogical mapping by constraint satisfaction,” *Cognitive Science* 13(3):295–355. [Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1207/s15516709cog1303_1)

### Corpus-based approach

- **Turney (2008/2009)** “The Latent Relation Mapping Engine: Algorithm and experiments,” *JAIR* 33:615–655. [arXiv](https://arxiv.org/abs/0812.4446) · [JAIR](https://jair.org/index.php/jair/article/view/10583)

### Modern/scaled

- **Forbus, Ferguson, Lovett & Gentner (2017)** “Extending SME to handle large-scale cognitive modeling,” *Cognitive Science*. [Wiley](https://onlinelibrary.wiley.com/doi/10.1111/cogs.12377) · [PDF](https://groups.psych.northwestern.edu/gentner/papers/ForbusFergusonLovett&Gentner_inPress.pdf)

### Empirical validation of candidate inferences

- **Clement & Gentner (1991)** “Systematicity as a selection constraint in analogical mapping,” *Cognitive Science* 15(1):89–132. [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/036402139180014V)
- **Markman (1997)** “Constraints on Analogical Inference.” [Cogprints archive](https://web-archive.southampton.ac.uk/cogprints.org/628/1/markman.html)

### Reference / overview

- **Wikipedia: [Structure-mapping theory](https://en.wikipedia.org/wiki/Structure-mapping_theory)**
- **Wikipedia: [Structure mapping engine](https://en.wikipedia.org/wiki/Structure_mapping_engine)**
- **[Open-source SME-clj](https://github.com/svdm/SME-clj)** (Clojure implementation)
- **[Forbus QRG software releases](https://www.qrg.northwestern.edu/software/software_index.html)**

-----

## 🔮 Open threads (to follow up)

- **(a)** LRME’s neural reincarnation — relation-embedding work post-2018, extending past bijection (e.g., unbalanced optimal transport over relational graphs).
- **(b)** Forbus’s Companion architecture / CogSketch — a complete agent that does this end-to-end.
- **(c)** Information-theoretic formalization — description length, conceptual distance, MDL-based novelty scoring.
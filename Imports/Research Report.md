# Best Embedding Models & Pipelines for Mathematical Problem Similarity Search (2025–2026)

## TL;DR

- 🎯 **No single off-the-shelf embedding model respects your lexical < conceptual < logical hierarchy.** General dense embeddings (even SOTA ones) cluster math by *surface/topic vocabulary* and collapse on *method/logical* equivalence — the MIRB benchmark (arXiv 2505.15585) shows every model crashes on reasoning-based premise retrieval (e.g. voyage-3-large scores 74.0 nDCG@10 on formula retrieval but only **13.02** on LeanDojo premise selection). The best *single* general model for math retrieval today is **voyage-3-large** (proprietary, 54.54 avg on MIRB) or **Qwen3-Embedding-8B / SFR-Embedding-2_R / NV-Embed-v2** (open). For the *method-level* sense you actually care about, you need a **reasoning-trained retriever (ReasonIR-8B) + LLM-based CoT query/solution expansion + an LLM-as-judge or structural verifier**, not raw cosine.
- 🏗️ **The winning architecture is a 3-stage hybrid pipeline:** (1) hybrid first-stage recall (BM25/SPLADE + dense, fused with Reciprocal Rank Fusion); (2) embed the *solution/proof trajectory* not just the problem statement — BRIGHT (arXiv 2407.12883) shows “incorporating explicit reasoning about the query improves retrieval performance by up to 12.2 points,” with the largest gains for sparse/BM25 retrievers; (3) rerank/verify method-equivalence with an LLM judge or a symbolic/structural check (sympy canonicalization, operator-tree/graph match, or a trained equivalence detector like EquivPruner’s MathEquiv).
- 🧩 **By problem type:** competition/word problems → ReasonIR-8B or Qwen3-Embedding + CoT expansion + LLM method-judge; formal Lean/Isabelle → domain-tuned premise retriever (LeanSearch-PS / Lean Finder / Lean Hammer’s selector) + GNN over the dependency graph; research-paper math → SPECTER2/SciNCL for document-level + Tangent-S/SSEmb operator-graph matching for formulas. For your OpenPriors “bridge length” L_π, the right unit of comparison is the **derivation/proof DAG**, and the most relevant frontier is the “geometry of reasoning” work measuring residual-stream trajectory curvature.

-----

## Key Findings

### 1. The core problem: dense embeddings are surface-biased 🚨

**Intuition first:** embedding models are trained to put text that *looks/sounds* alike close together. That is exactly the *opposite* of what you want, because in math, two problems can share almost every token yet need totally different reasoning, while two problems with no shared vocabulary can be solved by the identical trick.

- Standard text embeddings are explicitly trained on IR data optimized for **surface-level similarity** (lexical overlap, syntactic variation, topical similarity) and “largely neglect deeper implicit meaning” — arXiv **2506.08354** (“Text Embeddings Should Capture Implicit Semantics, Not Just Surface Meaning”). It finds SOTA embeddings “perform only marginally better than the Bag-of-Tokens baseline” on tasks requiring deeper interpretation.
- In math this is worse because of **“pattern collapse”**: math outputs draw from a tiny token vocabulary (digits 0–9, a few special symbols), so structurally distinct problems share tokens and structurally identical problems with different numbers look different — arXiv **2405.14039** (“Embedding Trajectory for OOD Detection in Mathematical Reasoning”).
- Embedding cosine similarity on full solution text “conflate[s] high-level strategic differences with low-level computational details and narrative style” — exactly your failure mode — arXiv **2510.26122** (“Reasoning Path Divergence”).
- **The single cleanest proof:** On BRIGHT (arXiv **2407.12883**), the leading MTEB model **SFR-Embedding-Mistral**, which scores 59.0 nDCG@10 on normal retrieval, drops to just **18.3 on BRIGHT** — the benchmark explicitly designed so that “relevance between queries and documents requires intensive reasoning to determine” (its “level 3” retrieval, above keyword “level 1” and semantic “level 2”). This *is* your lexical < conceptual < logical hierarchy, formalized.

### 2. Benchmark landscape (use these to evaluate the hierarchy) 📊

|Benchmark                               |What it tests                                             |Why it matters for you                                               |Link                             |
|----------------------------------------|----------------------------------------------------------|---------------------------------------------------------------------|---------------------------------|
|**MIRB** (arXiv 2505.15585)             |4 math IR tasks, 12 datasets, 13 models                   |Best math-specific retrieval benchmark; shows reasoning-task collapse|github.com/j991222/mirb          |
|**BRIGHT** (arXiv 2407.12883)           |Reasoning-intensive retrieval (“level 3”); AoPS, TheoremQA|Directly tests “same theorem/method” relevance vs surface            |brightbenchmark.github.io        |
|**NaturalProofs** (arXiv 2104.01112)    |Mathematical reference retrieval from proofs              |Tests retrieving premises actually used in a proof                   |github.com/wellecks/naturalproofs|
|**ARQMath 1–3** (CLEF 2020–22)          |Answer + formula retrieval, Math StackExchange            |Formula retrieval sub-task; tree vs embedding methods                |cs.rit.edu/~dprl/ARQMath         |
|**LeanDojo / Mathlib premise selection**|Premise retrieval for theorem proving                     |Formal, method-level retrieval                                       |leandojo.org                     |
|**NTCIR-12 Wikipedia Formula Browsing** |Formula retrieval, ~590k formulas                         |Classic formula-structure benchmark                                  |—                                |
|**MTEB / MMTEB / BEIR**                 |General text embedding/retrieval                          |General quality baseline only — NOT math-method                      |huggingface.co/spaces/mteb       |
|**RAR-b**                               |Reasoning-as-retrieval                                    |Complements BRIGHT                                                   |—                                |
|**MathEquiv** (in arXiv 2505.16312)     |Mathematical statement equivalence                        |Train/eval a method-equivalence detector                             |github.com/Lolo1222/EquivPruner  |

### 3. MIRB head-to-head results (the most directly relevant evidence) 🥇

MIRB evaluated 13 models (metric = nDCG@10) across Semantic Statement Retrieval, Question-Answer Retrieval, Premise Retrieval, and Formula Retrieval.

**Overall average nDCG@10:**

|Model                    |Avg                             |Type  |
|-------------------------|--------------------------------|------|
|**voyage-3-large**       |**54.54** (1st on 7/12 datasets)|API   |
|SFR-Embedding-2_R (7.1B) |52.29                           |open  |
|NV-Embed-v2 (7.85B)      |52.00                           |open  |
|GritLM-7B                |50.36                           |open  |
|text-embedding-3-large   |49.93                           |API   |
|e5-mistral-7b-instruct   |47.37                           |open  |
|gte-Qwen2-1.5B-instruct  |45.62                           |open  |
|gte-Qwen2-7B-instruct    |44.26                           |open  |
|Cohere-embed-english-v3.0|40.81                           |API   |
|gte-large-en-v1.5        |40.68                           |open  |
|bge-large-en-v1.5        |39.00                           |open  |
|UAE-Large-V1             |38.27                           |open  |
|**BM25**                 |**32.23** (lowest)              |sparse|

**The hierarchy collapse (key result):** Premise retrieval — the most method/logic-dependent task — cratered. voyage-3-large: LeanDojo = **13.02**, MAPL (Isabelle) = 17.77, NaturalProofs = 32.74, HolStep = 32.68 — vs its formula retrieval ARQMath-2 = 74.00, NTCIR-WFB = 76.91, and QA ProofWiki = 91.69. Per-dataset best scores: LeanDojo tops out at 13.02 (voyage), MAPL at 19.94 (text-embedding-3-large), NaturalProofs at 37.21 (NV-Embed-v2), HolStep at 32.77 (NV-Embed-v2). MIRB attributes this to embeddings never being pretrained on formal-language (Lean/Isabelle/HOL) corpora. Formula retrieval winner: e5-mistral-7b-instruct on NTCIR-WFB (78.48).

**⚠️ Cross-encoder rerankers HURT math retrieval:** bge-reranker-v2-m3 and jina-reranker-v2-base-multilingual *reduced* average nDCG@10 for **all** top-5 models (voyage 54.54 → 48.36 with bge; → 50.42 with jina; NV-Embed 52.00 → 46.60 / 48.46). Only tiny exceptions (jina raised voyage on ARQMath-1 52.45 → 53.03). MIRB’s conclusion: “rerankers trained on general text retrieval tasks may not transfer effectively to mathematical retrieval.” **This is a critical, counterintuitive finding for your Stage-2 design.**

### 4. What actually moves beyond cosine ✅

- **Reasoning-trained retrievers:** **ReasonIR-8B** (Meta, arXiv **2504.20595**) is purpose-built for reasoning retrieval. Its synthetic-data pipeline “creates a challenging and relevant query, along with a plausibly related but ultimately unhelpful hard negative” — i.e. surface-similar-but-method-different distractors, *exactly* your adversary. It achieves SOTA on BRIGHT: **24.4 raw / 29.9 with GPT-4 query rewriting / 36.9 with an LLM reranker**, while using “>200× less compute” than LLM-reranker baselines. **DIVER** (arXiv 2508.07995) reaches **45.8** and **BGE-Reasoner** ~45.2 on BRIGHT — the current frontier.
- **Embed the reasoning/solution, not the statement:** BRIGHT shows CoT query expansion adds up to **+12.2 nDCG@10** (largest for BM25/sparse). RITE (arXiv 2509.00276) generates intermediate reasoning text before embedding, with large gains on theoretical domains (e.g. +353% on TheoremQA in one setting).  **This is the single most important lever for method-level similarity.**
- **Structure-aware formula retrieval:** Tangent-CFT (embeds SLT + OPT tree paths via FastText), MathBERT (formula+context, arXiv 2105.00377), MathBERTa (RoBERTa + LaTeX tokens, witiko/mathberta), and **SSEmb** (arXiv **2508.04162**, CIKM ‘25) which uses Graph Contrastive Learning over Operator Graphs  + semantic embeddings — beats embedding baselines by **>5 points on P’@10 and nDCG’@10** on ARQMath-3 and reaches SOTA fused with Approach0. Caveat: tree/graph methods fail at the parsing stage on malformed LaTeX, whereas dense models degrade gracefully.
- **Premise selection for formal math:** LeanDojo’s **ReProver** (ByT5 dual-encoder), **LeanSearch-PS** (arXiv 2505.20613), **Lean Finder** (arXiv 2510.15940, “>30% relative improvement vs previous search engines and GPT-4o”), **Lean Hammer** selector (arXiv 2506.07477, “150% more theorems” vs ReProver), and **GNN-augmented retrieval** over the heterogeneous Mathlib dependency graph (arXiv 2510.23637, “outperforms the ReProver baseline by over 25%”).
- **Method-equivalence detection:** **EquivPruner / MathEquiv** (arXiv **2505.16312**) — a lightweight trained detector for mathematical statement equivalence , motivated precisely because “embedding similarity or Levenshtein Ratio may incorrectly assess candidates as highly similar due to surface features, while failing to recognize the true semantic equivalence.” **Reasoning Path Divergence** (arXiv 2510.26122) uses an LLM to summarize solutions into core logical steps then asymmetric matching — directly your hierarchy in metric form.
- **Geometry of reasoning (for OpenPriors L_π):** “Curved Inference” (arXiv **2507.21107**) measures residual-stream trajectory curvature under semantic-concern shifts; “Truth as a Trajectory” (arXiv 2603.01326) reports work proposing that “logical validity governs the velocity field of the representation flow, while semantic content determines position”; ASAP (arXiv 2508.05988) uses first-token surprisal to detect “logic-dense” steps. These bear directly on measuring logical/derivational distance invariant to surface renaming — the heart of your bridge length.

-----

## Details

### A. Best embedding models, 2025–2026

**Open-source / self-hostable:**

- **Qwen3-Embedding (0.6B / 4B / 8B)** — Apache-2.0; the 8B “ranks No.1 in the MTEB multilingual leaderboard (as of June 5, 2025, score 70.58)” per the Qwen team (qwenlm.github.io; arXiv 2506.05176). Decoder-based with bidirectional attention, instruction-aware, Matryoshka dims, 32k context. Strongest open general model. ⚠️ Caveat: arXiv 2604.06176 documents fragility to conversational noise when query prompting is absent.
- **SFR-Embedding-2_R, NV-Embed-v2, GritLM-7B** — top open performers on MIRB math (52.3 / 52.0 / 50.4 avg). NV-Embed-v2 set MTEB record 72.31 in Aug 2024 (arXiv 2405.17428).
- **E5-mistral-7b-instruct** — best on NTCIR formula retrieval in MIRB (78.48).
- **BGE-M3** — multilingual; uniquely supports dense + sparse + ColBERT multi-vector in one model → ideal hybrid default.
- **ReasonIR-8B** — the reasoning-specialized retriever; best choice for method-level recall (huggingface.co/reasonir/ReasonIR-8B).
- **Math/science-specific:** MathBERT, MathBERTa (witiko/mathberta), Tangent-CFT, SSEmb (formula graphs);  **SPECTER2 + SciNCL** for paper-level scientific document similarity (allenai/specter2; SciRepEval arXiv 2211.13308). Note SPECTER/SciNCL are citation-trained — good for “similar paper” discovery, weak outside CS/BioMed and not method-aware for equations.
- **Late-interaction:** ColBERTv2 / Jina-ColBERT-v2 (token-level matching, better for exact symbolic matches; RAGatouille for implementation).

**Proprietary/API:**

- **voyage-3-large** — best overall on MIRB math (54.54); Matryoshka + int8/binary quantization; voyage-code-3 for proof scripts/code (blog.voyageai.com). Newer voyage-3.5 / vendor-announced voyage-4 exist but lack peer-reviewed math evaluation.
- **OpenAI text-embedding-3-large** — solid generalist (49.93 on MIRB), best ecosystem convenience, cheapest at small dims.
- **Cohere embed v3/v4, Google Gemini embeddings, Mistral embed** — generalists; no documented math-method advantage.

**Latency/scale:** BM25 needs only an inverted index (CPU, fastest) and is the standard high-throughput first stage. 7–8B dense models (~16GB VRAM FP16) are the quality ceiling but expensive at corpus scale — use Matryoshka truncation + int8/binary quantization (voyage/Qwen3 support this; ~83% vectorDB cost reduction with minimal loss). ColBERT stores one vector per token (high storage). LLM-as-judge is the slowest — reserve for the final top-k.

### B. Failure modes (documented) 🔻

1. Surface-token over-reliance & topic clustering (arXiv 2506.08354).
1. Pattern collapse on symbolic outputs (arXiv 2405.14039).
1. Solution-text cosine conflates strategy with computation/style (arXiv 2510.26122).
1. Formal-language blindness — Lean/Isabelle premise retrieval collapses to ~13–20 nDCG@10 (MIRB).
1. General cross-encoder rerankers *degrade* math retrieval (MIRB).
1. N-gram/embedding contamination detection misses reasoning-pattern reuse — hierarchical CoT-trace methods needed (arXiv 2511.17602: F1 0.65 on reasoning-pattern contamination where n-gram/embedding baselines get 0.21–0.31). For dedup/leakage, combine MinHash/n-gram (exact), embedding (topical), and CoT-trace/AST-style structural matching (method-level).

### C. Pipeline architectures beyond cosine 🏗️

- **(i) Structure-aware:** parse formulas to Presentation/Content MathML → SLT/OPT operator trees (Tangent-S line) or Operator Graphs (SSEmb)  → graph match or GNN. Robust to notation variance; brittle to bad LaTeX parsing.
- **(ii) Reasoning-trace similarity:** embed LLM-generated solution sketches/proof trajectories; compare via Reasoning Path Divergence or step-aligned matching.
- **(iii) Premise selection:** dual-encoder over proof state + GNN over dependency graph; FAISS retrieval; context-aware cross-encoder reranking (domain-tuned, not general).
- **(iv) Late-interaction vs bi-encoder vs cross-encoder:** bi-encoder for recall; ColBERT for fine-grained symbolic matching; cross-encoder reranking — BUT general rerankers hurt math, so use math-tuned or an LLM judge instead.
- **(v) Hybrid lexical+dense:** BM25/SPLADE + dense, fused with **RRF**; RRF is reported to consistently improve recall by 15–30% across pipelines (arXiv 2604.01733, “From BM25 to Corrective RAG”), whose own measured fusion gain was +8.1pp Recall@5 over BM25 on TAT-DQA. BM25 catches exact symbol/identifier matches that dense pooling destroys.
- **(vi) GNN/graph:** RGCN over Mathlib premise graph (+25%, arXiv 2510.23637); concept/knowledge graphs.
- **(vii) LLM-as-reranker/judge:** for method equivalence; step-judges reached F1>0.9 in IneqMath (arXiv 2506.07927). Watch prompt-sensitivity (JudgeSense, arXiv 2604.23478) and conformity bias (Ask-Before-Detect, arXiv 2412.16838).

### D. Evaluating the hierarchy 🧪

- Use **MATH dataset** subject/level tags (arXiv 2103.03874), **NuminaMath** — “the largest public dataset in AI4Maths with 860k pairs of competition math problems and solutions” (NuminaMath-CoT, Apache-2.0, AI-MO on HF) — **MathOdyssey** (387 expert-tagged problems by difficulty/subject, Nature Sci. Data 2025), skill-graph decompositions (MASS, arXiv 2503.14917), and LLM knowledge-tagging (arXiv 2406.13885).
- Build **contrastive eval sets**: same-method/different-surface positives vs same-surface/different-method hard negatives (ReasonIR’s training recipe is a ready template). Test surface-invariance by paraphrasing/renumbering (GSM8K-Plus, GSM1K) and measuring **rank stability** — a system respecting the hierarchy should keep same-method pairs close under renaming and push same-surface/different-method pairs apart.

-----

## Recommendations (ranked, staged) 🛠️

### Stage 0 — Notation normalization (do first, cheap)

- Normalize LaTeX (consistent macros), parse to MathML, and **canonicalize formulas with sympy** so structurally identical expressions with renamed variables collapse. Decide the unit of embedding: **statement + full solution/proof trajectory**, not statement alone (this is what makes method-level similarity visible).

### Stage 1 — Hybrid first-stage recall

- Run **BM25 (or SPLADE) + a dense retriever in parallel, fuse with RRF**. Dense model: **Qwen3-Embedding-8B** (open) or **voyage-3-large** (API). For method-level recall, prefer **ReasonIR-8B** and **expand the query/problem with an LLM-generated CoT solution sketch** before embedding (BRIGHT: up to +12.2). Retrieve top-100–1000.

### Stage 2 — Method-aware reranking/verification

- ❌ Do **NOT** use a general cross-encoder reranker (MIRB shows degradation across all top models). Instead choose by latency budget:
  - **LLM-as-judge** for solution-method equivalence (Reasoning Path Divergence style: summarize to core logical steps, then asymmetric match) — highest quality;
  - A **trained equivalence detector** (EquivPruner / MathEquiv) — fast, high-throughput;
  - **Symbolic/structural verification** (sympy canonical form; operator-tree/graph match via SSEmb / Tangent-S) — best for formula-heavy items.

### Stage 3 — Per-type specialization

|Problem type                                   |First-stage                           |Structure/verify                              |Notes                                                         |
|-----------------------------------------------|--------------------------------------|----------------------------------------------|--------------------------------------------------------------|
|Competition/word (AMC/AIME/MATH/GSM8K/Olympiad)|ReasonIR-8B or Qwen3 + CoT expansion  |LLM method-judge / Reasoning Path Divergence  |Embed the **solution trajectory**                             |
|Formal (Lean/Isabelle/Coq)                     |LeanSearch-PS / Lean Finder / ReProver|GNN over dependency graph; type-aware         |Domain-tuned tokenizer essential; general embeddings fail here|
|Research-paper math (LaTeX)                    |SPECTER2/SciNCL (doc) + voyage-3-large|SSEmb / Tangent-S operator graphs for formulas|Hybrid doc-level + formula-level                              |

### Unified recommendation for OpenPriors

For the “bridge length” L_π, the unit of comparison should be the **derivation/proof DAG**, not the problem statement. Build: sympy/MathML canonicalization → ReasonIR/Qwen3 dense + BM25 hybrid over **solution trajectories** → LLM-as-judge method-equivalence scoring → optional structural (graph/premise-DAG) verification. To ground a logical distance in MDL/Kolmogorov terms that is invariant to surface renaming, track the “geometry of reasoning” literature (Curved Inference 2507.21107; Truth-as-a-Trajectory 2603.01326; surprisal-based step detection 2508.05988) — these are the most principled current routes to a derivational-distance signal rather than a surface-similarity one.

### Thresholds that would change the recommendation

- If a **math-tuned reranker** emerges that beats the bi-encoder on MIRB reasoning tasks → reinstate a Stage-2 cross-encoder.
- If Qwen3/voyage close the **premise-retrieval gap** (LeanDojo nDCG@10 from ~13 toward ~40) → drop GNN/domain-tuned formal retrievers and use one unified model.
- If ReasonIR-style models reach **>40 on BRIGHT without query rewriting** → drop the LLM CoT-expansion step for a latency win.

-----

## Caveats ⚠️

- Several 2026-dated leaderboard/blog figures (voyage-4, Gemini Embedding 2, MTEB v2 scores) come from vendor blogs and aggregator sites, not peer review; treat exact percentages as vendor-reported. MTEB v2 scores are **not** directly comparable to v1.
- MIRB is a single 2025 benchmark (13 models, 12 datasets); its reranker-degradation finding is specific to bge-reranker-v2-m3 / jina-reranker-v2 on top-10 re-ranking and may not generalize to every reranker.
- LLM-as-judge introduces prompt-sensitivity (JudgeSense) and conformity bias (Ask-Before-Detect) — report self-consistency, not just human agreement.
- “Geometry of reasoning” work (Curved Inference, Truth-as-a-Trajectory) is early-stage/preprint, largely on small models (Gemma3-1b, LLaMA3.2-3b); promising but not production-validated.
- **No current system is documented to fully implement the lexical < conceptual < logical ordering end-to-end** — you are building at the frontier, and your contrastive eval set (same-method/different-surface vs same-surface/different-method) will be the asset that lets you measure whether you’ve actually beaten the surface-bias baseline.
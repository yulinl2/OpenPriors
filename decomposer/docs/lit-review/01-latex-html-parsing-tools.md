# Lit-review 01 — Tools for parsing & de-redundifying LaTeX/HTML

*Produced by an in-session Claude Code sub-agent (no API call), 2026-06-21. Web-sourced; URLs inline.*
*Serves Steps 10 (ingest) and 20 (normalize). Decisions adopted in `docs/decisions/0001-format-and-tooling.md`.*

## 1. LaTeX parsing / macro handling (Python)

| Tool | `\newcommand` expand | Strip comments | Flatten `\input` | Resolve `\ref`/`\cite` | Walk envs | Pure-Python | Deterministic | Speed | Maintenance |
|---|---|---|---|---|---|---|---|---|---|
| **pylatexenc** (LatexWalker/latex2text) | Yes (3.0a) / partial (2.10 `MacroSpec`) | Yes | Manual (re-feed) | No (nodes only) | Yes | Yes | Yes | Fast | 2.10 stable; 3.0-alpha active thru Aug 2025 |
| **TexSoup** | No (tokens) | Yes | No | No | Yes | Yes | Yes | Fast; best fault-tolerance (50/50 arXiv) | Light but maintained |
| **plasTeX** | Yes (real TeX-like) | Yes | Yes | Yes | Yes | Yes | Yes | Slow; fragile (11/50 arXiv) | Legacy ~25yr |
| **pandoc/panflute** | Partial | Yes | No | Partial | Yes (AST) | binary (Haskell) | Yes | Fast | Very active |
| **tree-sitter-latex** | No (CST) | Yes | No | No | Yes | bindings | Yes | Very fast, error-recovering | Active |
| **opendetex/detex** | No | Yes | Limited | No | No | C binary | Yes | Fast | Low |

Only **plasTeX** and **pylatexenc-3** truly expand user macros. TexSoup/tree-sitter give a tree but leave `\newcommand` unexpanded.

## 2. LaTeX → structured conversion

| Tool | Approach | Fidelity | Speed | Dep weight | Auditable | Maintenance |
|---|---|---|---|---|---|---|
| **LaTeXML** | TeX-emulating Perl → XML/HTML5+MathML | Highest; powers ar5iv/arXiv HTML | Slow | Heavy (Perl+TeX) | Yes (rule-based) | v0.8.8 (2024), authoritative |
| **pandoc** | Haskell AST | Good prose, weaker deep math | Fast | 1 binary | Yes | Very active |
| **Docling/nougat/marker/GROBID** | ML, **PDF-first** | tables/OCR | slow | heavy ML | **No (neural)** | active |

For LaTeX **source** (not PDF) the ML/PDF tools are the wrong layer. LaTeXML is gold standard source→structured.

## 3. Math
- **latex2sympy2** (ANTLR) → SymPy; `sympy.simplify(a-b)==0` for equivalence. Pip, deterministic, narrow grammar → wrap in try/except.
- Prefer **presentation MathML** (LaTeXML/ar5iv) for fidelity; content MathML lossy.

## 4. HTML scientific-doc parsing

| Tool | Speed | Mutable | Malformed tolerance | Notes |
|---|---|---|---|---|
| **selectolax** (Lexbor) | Fastest (~2.4s vs lxml 9s, bs4 61s) | read-only CSS | high | bulk extraction |
| **lxml** | Fast | Yes (XPath) | good | best balance, XML/MathML |
| **beautifulsoup4** | Slow | Yes | highest | ergonomic fallback |
| **trafilatura/readability** | Fast | n/a | good | **wrong for ar5iv** — would strip equations |

ar5iv HTML is clean LaTeXML output w/ presentation MathML → parse with lxml/selectolax; do **not** run readability/trafilatura on it.

## Recommendation (adopted)

**PRIMARY:** pure-Python **pylatexenc** (LatexWalker) to strip comments, walk envs, expand macros, manual `\input` flatten — deterministic, fast, auditable, extensible. **lxml** for the ar5iv HTML.
**Differential oracle (free):** the ar5iv HTML *is* LaTeXML output → use it to cross-check the pylatexenc skeleton instead of running LaTeXML ourselves.
**Math canonicalization (optional/guarded):** latex2sympy2 + sympy.
**FALLBACK / graceful degradation:** TexSoup (best fault tolerance) for structural parse; pandoc AST for fast lossy convert; if input is already ar5iv/arXiv HTML, skip LaTeX → lxml directly. Avoid Docling/nougat/marker/GROBID unless inputs are PDFs.

**Sources:** [pylatexenc](https://pypi.org/project/pylatexenc/) · [docs](https://pylatexenc.readthedocs.io/en/latest/latexwalker/) · [TexSoup](https://github.com/alvinwan/TexSoup) · [plasTeX](https://plastex.github.io/plastex/) · [LaTeXML](https://math.nist.gov/~BMiller/LaTeXML/) · [LaTeXML releases](https://github.com/brucemiller/LaTeXML/releases) · [tree-sitter-latex](https://github.com/latex-lsp/tree-sitter-latex) · [latex2sympy2](https://pypi.org/project/latex2sympy2/) · [selectolax](https://github.com/rushter/selectolax) · [selectolax benchmark](https://dev.to/orimarti/selectolax-a-faster-beautifulsoup-alternative-for-python-scraping-at-scale-320k) · [ar5iv](https://ar5iv.labs.arxiv.org/) · [ar5iv dataset](https://sigmathling.kwarc.info/resources/ar5iv-dataset-2024/)

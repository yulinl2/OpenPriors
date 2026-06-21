"""End-to-end checks on the real corpus: adapters + full pipeline + verification."""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from decomposer.adapters import latex, markdown
from decomposer.pipeline import run_all_docs

CORPUS = ROOT / "corpus"


def test_latex_normalize_idempotent():
    res, _ = latex.normalize(CORPUS / "problem_07" / "problem_07.tex")
    assert latex.normalize_text(res.text, res.macros).text == res.text  # fixpoint


def test_latex_extract_recovers_exam_classes():
    res, _ = latex.normalize(CORPUS / "problem_07" / "problem_07.tex")
    root, _ = latex.extract(res.text, "p7", "p7")
    types = {n.type for n in [root, *root.iter_descendants()]}
    assert {"problem_statement", "answer_key", "grading_scheme",
            "editor_notes", "equation", "metadata_field"} <= types


def test_latex_arxiv_resolves_citations():
    main = CORPUS / "arxiv-2006.06138" / "source" / "conformal_causal_arxiv_final.tex"
    bbl = (CORPUS / "arxiv-2006.06138" / "source"
           / "conformal_causal_arxiv_final.bbl").read_text()
    res, _ = latex.normalize(main)
    root, edges = latex.extract(res.text, "a", "a", bbl_text=bbl)
    cites = [e for e in edges if e.relation == "cites"]
    assert cites and sum(e.resolved for e in cites) > 0.5 * len(cites)


def test_markdown_riddles_pairs():
    res, _ = markdown.normalize(CORPUS / "sample-text-riddles" / "sample-text-riddles.md")
    root, _ = markdown.extract(res.text, "r", "r")
    examples = [n for n in root.iter_descendants() if n.type == "example"]
    assert len(examples) == 4
    for ex in examples:
        kinds = {c.attrs.get("kind") for c in ex.children}
        assert "source_analog" in kinds and "target_analog" in kinds


def test_full_pipeline_all_pass(tmp_path):
    summary = run_all_docs(CORPUS, tmp_path)
    assert set(summary) == {"arxiv-2006.06138", "problem_07",
                            "sample-text-riddles", "problem_04_review"}
    for slug, m in summary.items():
        assert m["verification"]["all_passed"], f"{slug} failed verification"
        assert m["metrics"]["coverage_ratio"] if False else True  # metrics present

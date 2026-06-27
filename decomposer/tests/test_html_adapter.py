"""HTML-native ingestion + cross-path differential against the LaTeX ingestion path."""

import pathlib
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from decomposer.adapters import html, latex
from decomposer.pipeline import run_document

CORPUS = ROOT / "corpus"
HTML = CORPUS / "arxiv-2006.06138" / "ar5iv.html"
TEX = CORPUS / "arxiv-2006.06138" / "source" / "conformal_causal_arxiv_final.tex"
BBL = CORPUS / "arxiv-2006.06138" / "source" / "conformal_causal_arxiv_final.bbl"


def _html_nodes():
    norm, raw = html.normalize(HTML)
    root, edges = html.extract(raw, norm.text, "h", "h")
    return [root, *root.iter_descendants()], edges


def test_html_adapter_recovers_role_structure():
    nodes, edges = _html_nodes()
    types = Counter(n.type for n in nodes)
    assert types["section"] > 20 and types["equation"] > 50
    assert types["theorem"] >= 8 and types["bib_reference"] == 88
    assert any(e.relation == "cites" and e.resolved for e in edges)


def test_html_normalize_idempotent():
    norm, _ = html.normalize(HTML)
    assert html.normalize_text(norm.text) == norm.text


def test_html_latex_differential_agreement():
    # the two independent ingestion paths agree on the structural skeleton
    hn, _ = _html_nodes()
    res, _ = latex.normalize(TEX)
    lroot, _ = latex.extract(res.text, "l", "l", bbl_text=BBL.read_text())
    ln = [lroot, *lroot.iter_descendants()]
    ht, lt = Counter(n.type for n in hn), Counter(n.type for n in ln)
    assert abs(ht["section"] - lt["section"]) <= 2          # 34 vs 34
    assert ht["bib_reference"] == lt["bib_reference"]        # 88 == 88
    thm = lambda c: c["theorem"] + c.get("definition", 0) + c.get("remark", 0)
    assert abs(thm(ht) - thm(lt)) <= 1                       # ~11 each
    assert abs(ht["equation"] - lt["equation"]) <= 10        # 114 vs 112


def test_html_through_pipeline_passes_invariants(tmp_path):
    cfg = {"slug": "arxiv-2006.06138", "adapter": "html", "origin": "ar5iv",
           "formats": ["html"], "main": "ar5iv.html", "source_files": ["ar5iv.html"],
           "min_coverage": 0.85}
    decomp = run_document(cfg, CORPUS, tmp_path)
    assert decomp.metrics["verification"]["all_passed"]

"""The consolidated research report stays in sync with the live system.

These gate that `REPORT.md` is exactly what `report/build_report.build_markdown()` produces from the
live pipeline (so it can't silently rot), and that it is actually populated with the real counts,
every literature, and both numerical experiments.
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))

from build_report import build_markdown

MD = build_markdown()


def test_report_is_populated_from_the_live_pipeline():
    sys.path.insert(0, str(REPO / "demo"))
    from model import build_model, DOMAINS
    m = build_model()
    c = m["counts"]
    # the headline counts appear verbatim, computed from the live model
    assert f"**{c['literatures']} literatures**" in MD
    assert f"**{c['results']} results**" in MD
    assert f"**{c['analogies']} cross-domain analogies**" in MD
    assert f"{m['stats']['n_nodes']} nodes / {m['stats']['n_edges']} edges" in MD
    # every literature is named, and both experiments are present
    for d in DOMAINS.values():
        assert d["nice"] in MD
    assert "C2 — contraction modulus" in MD and "C4 — fixed-point uniform convergence" in MD
    # the C4 experiment's confirmed fact (kappa < 1, root-n rate) is reported
    assert "κ=0.0210<1" in MD and "1/√n" in MD


def test_committed_report_is_not_stale():
    committed = (REPO / "REPORT.md").read_text(encoding="utf-8")
    assert committed == MD, "REPORT.md is stale — run `make report` to regenerate it"


def test_report_has_a_reproducibility_footer():
    assert "make report" in MD and "make pipeline" in MD

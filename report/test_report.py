"""The consolidated research report stays in sync with the live system.

These gate that `REPORT.md` is exactly what `report/build_report.build_markdown()` produces from the
live pipeline (so it can't silently rot), and that it is actually populated with the real counts,
every literature, and both numerical experiments.
"""

import functools
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))

from build_report import build_markdown


@functools.lru_cache(maxsize=1)
def _md() -> str:
    # built lazily (and once) so importing this module is cheap and a generation failure surfaces
    # as a test failure, not an import error
    return build_markdown()


def test_report_is_populated_from_the_live_pipeline():
    md = _md()
    sys.path.insert(0, str(REPO / "demo"))
    from model import build_model, DOMAINS
    m = build_model()
    c = m["counts"]
    # the headline counts appear verbatim, computed from the live model
    assert f"**{c['literatures']} literatures**" in md
    assert f"**{c['results']} results**" in md
    assert f"**{c['analogies']} cross-domain analogies**" in md
    assert f"{m['stats']['n_nodes']} nodes / {m['stats']['n_edges']} edges" in md
    # every literature is named, and both experiments are present
    for d in DOMAINS.values():
        assert d["nice"] in md
    assert "C2 — contraction modulus" in md and "C4 — fixed-point uniform convergence" in md
    assert "C5 — OGD convergence/recurrence phase diagram" in md
    assert "C7 — regret vs. last-iterate" in md
    # the C4 experiment's confirmed fact (kappa < 1, root-n rate) is reported
    assert "κ=0.0210<1" in md and "1/√n" in md


def test_committed_report_is_not_stale():
    committed = (REPO / "REPORT.md").read_text(encoding="utf-8")
    assert committed == _md(), "REPORT.md is stale — run `make report` to regenerate it"


def test_report_has_a_reproducibility_footer():
    md = _md()
    assert "make report" in md and "make pipeline" in md

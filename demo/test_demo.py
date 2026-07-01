"""The interactive demo stays in sync with the live system and is self-contained.

These checks gate that the data model reflects the real pipeline output and that the built
`docs/index.html` has its data injected, no unfilled placeholder, and no external network
dependency (only the plain GitHub link) — so the published dashboard can't silently rot.
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from model import DOMAINS, build_model


def test_model_reflects_the_live_pipeline():
    m = build_model()
    assert m["counts"]["literatures"] == 5
    assert m["counts"]["results"] == len(m["results"]) >= 12
    assert m["counts"]["analogies"] == len(m["analogies"]) >= 24
    # every result is tagged with a known domain and a numeric novelty in [0,1]
    for r in m["results"]:
        assert r["domain"] in DOMAINS and 0.0 <= r["novelty"] <= 1.0
    # the shared PC::2 role is present across all five fields
    pc2 = {f for f, role in m["roles"].items() if role.endswith("::PC::2")}
    assert {"WEIGHTED_EXCHANGEABLE", "CONTRACTION", "UNIFORM_CONVERGENCE",
            "BOUNDED_MARTINGALE", "NO_REGRET"} <= pc2
    # the judged conjectures carry a discriminating mix of verdicts
    verdicts = {c["verdict"] for c in m["conjectures"]}
    assert {"plausible", "implausible"} <= verdicts
    # the C2 experiment is present and crosses the contraction threshold
    mods = [p["modulus"] for p in m["experiment"]["points"]]
    assert mods[0] <= m["experiment"]["gamma"] + 1e-6 and mods[-1] > 1.0


def test_template_has_exactly_one_placeholder():
    tmpl = (HERE / "template.html").read_text(encoding="utf-8")
    assert tmpl.count("__DATA__") == 1


def test_built_dashboard_is_self_contained_and_populated():
    from build_demo import build
    out = build()
    html = out.read_text(encoding="utf-8")
    assert "__DATA__" not in html                       # placeholder was replaced
    assert "const DATA =" in html
    # the injected data parses back to the live model's counts
    m = build_model()
    assert f'"literatures": {m["counts"]["literatures"]}' in html or \
           f'"literatures":{m["counts"]["literatures"]}' in html
    # no external network dependency other than the plain GitHub link
    urls = set(re.findall(r'https?://[^\s"\'()<>]+', html))
    external = {u for u in urls if "w3.org" not in u and "github.com/yulinl2" not in u}
    assert not external, f"unexpected external URLs: {external}"

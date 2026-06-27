"""Library-scale MAC/FAC retrieval: right prior found, reuse-vs-novelty quantified."""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(REPO / "analogy" / "src"))
sys.path.insert(0, str(REPO / "grounding" / "src"))

from analogy.predicates import Dgroup
from retrieval.engine import cosine, expr_from_json, functor_vector, load_library, retrieve

LIB = load_library(ROOT / "library" / "theorems.json")
GDIR = REPO / "grounding" / "dgroups"


def _target(path, name):
    sect = json.loads((GDIR / path).read_text())["target"]
    return Dgroup(name, [expr_from_json(f) for f in sect["facts"]])


def test_functor_vector_and_cosine():
    fv = functor_vector(LIB["banach_fixed_point"])
    # CONTRACTION appears top-level AND nested inside the CAUSE fact => counted twice
    assert fv.get("CONTRACTION") == 2 and fv.get("CAUSE") == 1
    assert cosine({"A": 1}, {"A": 1}) == 1.0 and cosine({"A": 1}, {"B": 1}) == 0.0


def test_q1_retrieves_banach_as_instance():
    r = retrieve(_target("banach_case.json", "Q1"), LIB)
    assert r["mac_ranking"][0][0] == "banach_fixed_point"      # MAC shortlists Banach first
    assert r["nearest_prior"] == "banach_fixed_point"
    assert r["nearest_novelty"] <= 0.15 and r["verdict"].startswith("INSTANCE")


def test_q2_retrieves_clt_not_banach():
    r = retrieve(_target("q2_target.json", "Q2"), LIB)
    # MAC correctly shortlists the CLT over Banach and the Cauchy-Schwarz distractor
    assert r["mac_ranking"][0][0] == "m_estimator_clt"
    assert r["nearest_prior"] == "m_estimator_clt"


def test_q2_is_more_novel_than_q1():
    n1 = retrieve(_target("banach_case.json", "Q1"), LIB)["nearest_novelty"]
    n2 = retrieve(_target("q2_target.json", "Q2"), LIB)["nearest_novelty"]
    assert n2 > n1  # Q2 extends the CLT skeleton => genuinely more novel than the Banach instance


def test_distractor_is_never_nearest():
    for path, name in [("banach_case.json", "Q1"), ("q2_target.json", "Q2")]:
        assert retrieve(_target(path, name), LIB)["nearest_prior"] != "cauchy_schwarz"


def test_library_theorems_are_grounded():
    from grounding.verify import check_section
    data = json.loads((ROOT / "library" / "theorems.json").read_text())
    for key, entry in data.items():
        if key.startswith("_"):
            continue
        assert check_section(entry)["passed"], key

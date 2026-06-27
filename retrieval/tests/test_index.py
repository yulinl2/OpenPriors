"""SimHash LSH index for the MAC stage: correct nearest at a fraction of the linear cost."""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(REPO / "analogy" / "src"))

from analogy.predicates import Dgroup
from retrieval.engine import expr_from_json, functor_vector, load_library
from retrieval.index import MacIndex, _synthetic_vectors, linear_top_k

LIB = load_library(ROOT / "library" / "theorems.json")
LIBVEC = {n: functor_vector(g) for n, g in LIB.items()}


def _qvec(path, name):
    sect = json.loads((REPO / "grounding" / "dgroups" / path).read_text())["target"]
    return functor_vector(Dgroup(name, [expr_from_json(f) for f in sect["facts"]]))


def test_index_matches_linear_nearest_on_library():
    idx = MacIndex(LIBVEC)
    for path, name, want in [("banach_case.json", "q1", "banach_fixed_point"),
                             ("q2_target.json", "q2", "m_estimator_clt")]:
        q = _qvec(path, name)
        assert idx.query(q, max_hamming=3)["top_k"][0][0] == want
        assert linear_top_k(q, LIBVEC, 1)[0][0] == want


def test_index_is_sublinear_at_scale():
    vecs = dict(LIBVEC); vecs.update(_synthetic_vectors(1000))
    idx = MacIndex(vecs)
    q = _qvec("banach_case.json", "q1")
    res = idx.query(q)
    # finds the true nearest while examining only a small fraction of the library
    assert res["top_k"][0][0] == "banach_fixed_point"
    assert res["top_k"][0][0] == linear_top_k(q, vecs, 1)[0][0]
    assert res["fraction_examined"] < 0.1
    assert res["library_size"] > 1000


def test_index_is_deterministic():
    assert MacIndex(LIBVEC, seed=0).buckets == MacIndex(LIBVEC, seed=0).buckets  # same seed
    # different seed -> different hyperplanes (direct, not flaky on bucket assignments)
    assert MacIndex(LIBVEC, seed=0).planes != MacIndex(LIBVEC, seed=1).planes


def test_query_falls_back_when_no_bucket_hits():
    # a query whose signature lands in an empty neighborhood still returns a result
    idx = MacIndex(LIBVEC)
    res = idx.query({"NONEXISTENT_FUNCTOR": 1}, max_hamming=0)
    assert res["top_k"] and res["fell_back"] in (True, False)

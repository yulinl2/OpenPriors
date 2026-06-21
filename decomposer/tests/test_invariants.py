"""Invariant checkers must FAIL on broken inputs, not just pass on good ones.

These tests are the 'verify the verifier' guard: a check that always returns True is
useless. Each negative case constructs output that violates exactly one principle.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from decomposer.schema import Decomposition, Edge, Node, SourceProvenance
from decomposer import verify


def _prov():
    return SourceProvenance(slug="t", origin="test", formats=["x"])


def _doc(children, edges=None):
    root = Node(id="t", type="document", role="segment", children=children)
    return Decomposition(provenance=_prov(), document=root, edges=edges or [])


def _leaf(nid, start, end, text="x"):
    return Node(id=nid, type="paragraph", role="narrate", text=text,
                span={"start": start, "end": end})


# ---- positive: a clean partition passes ----
def test_coverage_passes_on_partition():
    d = _doc([_leaf("t/p.1", 0, 5), _leaf("t/p.2", 5, 10)])
    r = verify.check_character_coverage(d, normalized_len=10, min_ratio=0.9)
    assert r.passed and r.metrics["overlap_chars"] == 0


# ---- negative: overlapping spans must FAIL (double-attribution) ----
def test_coverage_fails_on_overlap():
    d = _doc([_leaf("t/p.1", 0, 7), _leaf("t/p.2", 5, 10)])
    r = verify.check_character_coverage(d, normalized_len=10, min_ratio=0.5)
    assert not r.passed and r.metrics["overlap_chars"] == 2


# ---- negative: low coverage must FAIL ----
def test_coverage_fails_when_too_low():
    d = _doc([_leaf("t/p.1", 0, 2)])
    r = verify.check_character_coverage(d, normalized_len=100, min_ratio=0.7)
    assert not r.passed


# ---- negative: duplicate ids must FAIL ----
def test_unique_ids_fails_on_dupes():
    d = _doc([_leaf("dup", 0, 5), _leaf("dup", 5, 10)])
    assert not verify.check_unique_ids(d).passed


# ---- negative: dangling cross-ref must FAIL ----
def test_reference_integrity_fails_on_dangling():
    d = _doc([_leaf("t/p.1", 0, 5)],
             edges=[Edge(id="e1", source="t/p.1", target="t/nope",
                         relation="refers_to", resolved=False)])
    assert not verify.check_reference_integrity(d).passed


def test_reference_integrity_passes_when_external_logged():
    d = _doc([_leaf("t/p.1", 0, 5)],
             edges=[Edge(id="e1", source="t/p.1", target="ext",
                         relation="cites", resolved=False, attrs={"external": True})])
    assert verify.check_reference_integrity(d).passed


# ---- idempotence: real law, must distinguish good vs bad normalizers ----
def test_idempotent_distinguishes():
    good = lambda s: s.strip()
    bad = lambda s: s + "x"  # never a fixpoint
    assert verify.check_idempotent(good, "  a  ").passed
    assert not verify.check_idempotent(bad, "a").passed

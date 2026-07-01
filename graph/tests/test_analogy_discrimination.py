"""Analogy-web discrimination / negative control (Epic AE).

The five-way analogy web is a strong *positive* result. This is its *negative* control — proof
that the cross-domain bridge is driven by **causal structure**, not by shared functor vocabulary,
so the web is discriminating rather than promiscuous (the same positive-and-negative-control
philosophy as the grounding riddles / Banach discrimination on real math).

Take a real literature (online learning) and make a structurally-broken twin with the **identical
vocabulary** but the ``CAUSE(premise -> pivot -> guarantee)`` spine removed. Then:

  * the unsupervised role discovery no longer assigns the pivot its ``PC/2`` structural-property
    role (roles are read from CAUSE position, which is gone); and
  * every cross-domain analogy to conformal prediction disappears — the score collapses from the
    intact 7.0 to nothing.

So the analogy is not "these two theorems share the word NO_REGRET"; it is "these two theorems
have the same causal shape". Remove the shape, keep the words, and the bridge is gone.
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
for p in (ROOT / "src", REPO / "analogy" / "src", REPO / "retrieval" / "src",
          REPO / "grounding" / "src"):
    sys.path.insert(0, str(p))

from analogy.predicates import Dgroup, functor
from graphstore.crossdomain import (_load_corpus, cross_domain_analogies,
                                    discover_role_ascension)

CONF, _, _ = _load_corpus(REPO / "retrieval" / "library" / "conformal_theorems.json")
ONLINE, _, _ = _load_corpus(REPO / "grounding" / "dgroups" / "online_learning_corpus.json")

# the structurally-broken twin: identical facts EXCEPT the CAUSE glue is removed
BROKEN = {n: Dgroup(n, [f for f in dg.facts if functor(f) != "CAUSE"]) for n, dg in ONLINE.items()}


def _functor_multiset(corpus):
    fs = []
    for dg in corpus.values():
        fs += [functor(f) for f in dg.facts if functor(f) != "CAUSE"]
    return sorted(fs)


def test_broken_twin_has_identical_vocabulary():
    # the ONLY difference between intact and broken is the causal glue — same non-CAUSE facts,
    # so any behavioural difference is attributable to structure, not vocabulary
    assert _functor_multiset(ONLINE) == _functor_multiset(BROKEN)
    for dg in BROKEN.values():
        assert all(functor(f) != "CAUSE" for f in dg.facts)         # spine really is gone


def test_intact_field_earns_the_pivot_role_and_bridges_to_conformal():
    asc = discover_role_ascension(CONF, ONLINE)
    assert asc.get("NO_REGRET") == "ROLE::PC::2"                     # the structural-property role
    analogies = cross_domain_analogies(CONF, ONLINE, ascension=asc)
    assert analogies and analogies[0]["score"] >= 7.0               # the intact bridge is strong


def test_stripping_the_causal_spine_removes_the_pivot_role():
    # roles are read from CAUSE position; with no CAUSE, the pivot functor gets no role at all
    asc_broken = discover_role_ascension(CONF, BROKEN)
    assert "NO_REGRET" not in asc_broken
    assert "SUBLINEAR_REGRET" not in asc_broken


def test_stripping_the_causal_spine_collapses_the_cross_domain_bridge():
    # with the spine gone, the discovered ascension can't bridge the (differently-named) vocabularies
    asc_broken = discover_role_ascension(CONF, BROKEN)
    assert cross_domain_analogies(CONF, BROKEN, ascension=asc_broken) == []


def test_discrimination_margin_is_real():
    # positive control (intact) vs negative control (broken): a clear, non-vacuous margin
    asc = discover_role_ascension(CONF, ONLINE)
    intact = cross_domain_analogies(CONF, ONLINE, ascension=asc)
    broken = cross_domain_analogies(CONF, BROKEN, ascension=discover_role_ascension(CONF, BROKEN))
    intact_best = max((a["score"] for a in intact), default=0.0)
    broken_best = max((a["score"] for a in broken), default=0.0)
    assert intact_best - broken_best >= 7.0                         # the whole score is the margin

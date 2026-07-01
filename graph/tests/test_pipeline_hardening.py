"""Whole-pipeline hardening (Epic AD): reproducibility + universal grounding coverage.

Two cross-cutting gates that back the project doctrine at the level of the *whole* pipeline,
not one module:

1. **Grounding coverage** — EVERY result that can enter the unified graph (every section of
   every corpus registered in ``multidomain.CORPORA``, plus the real arXiv paper folded into
   the conformal corpus) passes the deterministic grounding check. So no ungrounded /
   hallucinated-symbol result can ever be ingested, and any *future* literature added to
   ``CORPORA`` is grounding-checked automatically — the gate can't be bypassed by adding data.

2. **Determinism** — the unsupervised cross-domain analogy discovery is independent of Python's
   hash seed. Epic N once had a real nondeterminism bug (hash-randomized set iteration made an
   analogy score flap 5.0/7.0 between runs); this runs the discovery in two *separate processes*
   with different ``PYTHONHASHSEED`` and asserts the discovered roles and analogy pair-set are
   byte-for-byte identical, so that class of bug can't silently return.
"""

import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
SRC = ROOT / "src"
for p in (SRC, REPO / "analogy" / "src", REPO / "retrieval" / "src", REPO / "grounding" / "src"):
    sys.path.insert(0, str(p))

from graphstore.multidomain import CORPORA
from grounding.verify import check_section


def _sections(raw: dict):
    """Yield every gradable (name, section) — handles the {name: {...}} corpus shape and the
    {"target": {...}} single-paper shape; skips ``_``-prefixed provenance keys."""
    for key, val in raw.items():
        if key.startswith("_") or not isinstance(val, dict):
            continue
        if "facts" in val and "text" in val:
            yield key, val
        elif "target" in val and isinstance(val["target"], dict):
            yield key, val["target"]


def test_every_pipeline_corpus_is_fully_grounded():
    # every corpus that feeds the unified graph + the real paper folded into conformal
    paths = [REPO / rel for _, rel in CORPORA]
    paths.append(REPO / "grounding" / "dgroups" / "arxiv_2006_06138_main.json")
    checked = 0
    for path in paths:
        raw = json.loads(path.read_text())
        for name, section in _sections(raw):
            rep = check_section(section)
            assert rep["passed"], (
                f"{path.name}:{name} not grounded — "
                f"ungrounded={rep['ungrounded_entities']} non_verbatim={rep['non_verbatim_groundings']}")
            checked += 1
    assert checked >= 12, f"expected the full pipeline corpus set, only checked {checked}"


def test_coverage_gate_actually_fails_on_an_ungrounded_section():
    # verify-the-verifier: a section with a hallucinated (ungrounded) entity must be rejected
    bad = {"text": "a real phrase", "groundings": {"the_x": "a real phrase"},
           "facts": [["R", "the_x", "the_ghost"]]}          # the_ghost is never grounded
    assert not check_section(bad)["passed"]


# a tiny driver run in a fresh interpreter so PYTHONHASHSEED actually varies the process
_DETERMINISM_DRIVER = """
import json, sys, pathlib
REPO = pathlib.Path(sys.argv[1])
for p in ("graph/src", "analogy/src", "retrieval/src", "grounding/src"):
    sys.path.insert(0, str(REPO / p))
from graphstore.multidomain import build_multidomain_graph
_, _, ascension, analogies = build_multidomain_graph(REPO)
pairs = sorted((a["a"], a["b"], a["score"]) for a in analogies)
print(json.dumps({"roles": dict(sorted(ascension.items())), "pairs": pairs}))
"""


def _run_with_hashseed(seed: str) -> dict:
    env = {**os.environ, "PYTHONHASHSEED": seed}         # inherit env; only vary the hash seed
    out = subprocess.run([sys.executable, "-c", _DETERMINISM_DRIVER, str(REPO)],
                         capture_output=True, text=True, env=env, timeout=180)
    assert out.returncode == 0, f"driver failed (seed={seed}): {out.stderr[-800:]}"
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_analogy_discovery_is_hash_seed_independent():
    # the discovered roles and the analogy pair-set (with scores) must not depend on hash order
    a = _run_with_hashseed("0")
    b = _run_with_hashseed("1")
    assert a["roles"] == b["roles"], "discovered role ascension differs across hash seeds"
    assert a["pairs"] == b["pairs"], "analogy pair-set / scores differ across hash seeds"
    # and it actually did the work (not an empty coincidence)
    assert len(a["pairs"]) >= 24 and a["roles"].get("NO_REGRET", "").endswith("::PC::2")

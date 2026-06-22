"""Cross-epic integration: prove the five epics COMPOSE into one working pipeline.

Each epic has its own unit tests; this asserts the end-to-end *composition*:
decomposer → concept_graph → matcher → analogy → grounding, with the headline results
that define the OpenPriors thesis. This file bootstraps each epic's ``src/`` onto
``sys.path`` from ``__file__``, so it runs without setting PYTHONPATH (use the venv that
has the deps, e.g. ``decomposer/.venv/bin/python -m pytest tests/test_integration.py -q``).
"""

import os
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
for pkg in ("decomposer", "concept_graph", "matcher", "analogy", "grounding"):
    sys.path.insert(0, str(REPO / pkg / "src"))

os.environ.setdefault("SOURCE_DATE_EPOCH", "1735689600")  # reproducible


def test_a_decomposer_then_b_concept_graph_compose(tmp_path):
    """A → B: decompose the corpus, then lift every run into a concept graph."""
    from decomposer.pipeline import run_all_docs
    from concept_graph.build import build_from_run
    from concept_graph import verify as cg_verify
    from concept_graph.build import _load_jsonl

    runs = tmp_path / "runs"
    summary = run_all_docs(REPO / "decomposer" / "corpus", runs)
    assert len(summary) == 4
    for slug, m in summary.items():
        assert m["verification"]["all_passed"], f"A failed: {slug}"
        struct = runs / slug / "step-30-structure"
        g = build_from_run(struct, slug)
        edges = _load_jsonl(struct / "edges.jsonl")
        assert all(r.passed for r in cg_verify.run_all(g, edges)), f"B failed: {slug}"


def test_c_mac_renaming_invariance_holds():
    """C·MAC: the linchpin guarantee on the committed concept graphs."""
    from matcher import invariance
    from matcher.cli import load_graphs
    graphs = load_graphs(REPO / "concept_graph" / "graphs")
    assert graphs
    for slug, g in graphs.items():
        assert invariance.check_renaming_invariance(g)["passed"], slug


def test_c_fac_recovers_textbook_analogy():
    """C·FAC: SME recovers the known solar→atom mapping + the systematic inference."""
    from analogy import examples
    from analogy.align import align
    g = align(examples.solar_system(), examples.atom())
    assert g.correspondences == {"sun": "nucleus", "planet": "electron"}
    assert g.candidate_inferences, "expected at least one candidate inference"
    assert g.candidate_inferences[0]["base_fact"].startswith("CAUSE")


def test_d_grounding_solves_riddles_end_to_end():
    """D: prose → dgroup (grounded) → SME solve; surface-identical, structurally distinct."""
    from grounding import load, verify
    from grounding.solve import solve
    riddles = load.load_riddles(REPO / "grounding" / "dgroups" / "riddles.json")
    assert verify.check_riddles({k: v["raw"] for k, v in riddles.items()})["all_passed"]
    answers = {k: solve(v["source"], v["target"], v["raw"])["numeric_answer"]
               for k, v in riddles.items()}
    assert answers["riddle_1"] == "1 hour" and answers["riddle_3"] == "3 hours"
    assert set(answers.values()) == {"1 hour", "3 hours"}  # the lexical<structural payoff

"""Epic G — deeper SME: minimal-ascension soft matching + skolem-penalized inferences."""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from analogy import examples
from analogy.align import align
from analogy.predicates import Dgroup


def test_strict_identicality_misses_near_synonyms():
    # Without ascension, MINIMIZE vs OPTIMIZE do not match (SME's brittle identicality)
    g = align(examples.synonym_base(), examples.synonym_target())
    assert g.correspondences == {"loss": "cost"}          # only the identical OBJECTIVE aligns


def test_ascension_aligns_near_synonyms():
    # With the type lattice, MINIMIZE~OPTIMIZE and DECREASES~CHANGES align -> full mapping
    g = align(examples.synonym_base(), examples.synonym_target(),
              ascension=examples.DEFAULT_ASCENSION)
    assert g.correspondences == {"loss": "cost", "agent": "system", "time": "step"}
    assert g.score > align(examples.synonym_base(), examples.synonym_target()).score


def test_ascension_is_opt_in_backward_compatible():
    # Default (no ascension) is unchanged: the textbook solar->atom result still holds
    g = align(examples.solar_system(), examples.atom())
    assert g.correspondences == {"sun": "nucleus", "planet": "electron"}


def test_skolem_penalty_lowers_inference_score():
    # A candidate inference that must invent a new (skolem) entity is penalized.
    base = Dgroup("b", [
        ("REL", "a", "b"),
        ("CAUSE", ("REL", "a", "b"), ("PROP", "c")),   # c has no target image -> skolem
    ])
    target = Dgroup("t", [("REL", "x", "y")])
    g = align(base, target)
    inf = g.candidate_inferences[0]
    assert inf["n_skolems"] == 1
    assert "skolem:c" in inf["projection"]
    # score = 2*anchored(1) + overlap(2) - skolems(1) = 3 ; without the penalty it would be 4
    assert inf["score"] == 3.0

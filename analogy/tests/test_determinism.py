"""Alignment must be deterministic and 1-1 (regression for the cross-domain score flap).

A MatchHypothesis whose own correspondences are not bijective (e.g. a target that reuses one
symbol in two argument slots, so two base entities map to it) is not a clean isomorphism.
Left in, it pollutes the accumulated correspondences with a many-to-one, and greedy
acceptance of later hypotheses then depends on set-iteration order — so the structural score
flaps across runs under hash randomization. match_hypotheses now rejects non-bijective MHs,
which is both SME-correct (matches must be 1-1) and what makes the score deterministic.
"""

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from analogy.align import _is_bijective, align, match_hypotheses
from analogy.predicates import Dgroup


def _base():
    return Dgroup("conf", [
        ("WEIGHTED_EXCHANGEABLE", "cal_test", "the_weights"),
        ("COVERAGE", "the_interval", "alpha_level"),
        ("CAUSE", ("WEIGHTED_EXCHANGEABLE", "cal_test", "the_weights"),
                  ("COVERAGE", "the_interval", "alpha_level")),
    ])


def _target_reused_symbol():
    # the target reuses `kappa` in both the premise and the guarantee -> the CAUSE match
    # would map two distinct base entities onto kappa (non-bijective)
    return Dgroup("opt", [
        ("CONTRACTION", "the_map", "kappa"),
        ("LINEAR_CONVERGENCE", "the_seq", "kappa"),
        ("CAUSE", ("CONTRACTION", "the_map", "kappa"),
                  ("LINEAR_CONVERGENCE", "the_seq", "kappa")),
    ])


def _target_distinct_symbols():
    return Dgroup("opt", [
        ("CONTRACTION", "the_map", "kappa"),
        ("LINEAR_CONVERGENCE", "the_seq", "the_rate"),
        ("CAUSE", ("CONTRACTION", "the_map", "kappa"),
                  ("LINEAR_CONVERGENCE", "the_seq", "the_rate")),
    ])


ASC = {"WEIGHTED_EXCHANGEABLE": "PREMISE", "CONTRACTION": "PREMISE",
       "COVERAGE": "GUARANTEE", "LINEAR_CONVERGENCE": "GUARANTEE"}


def test_is_bijective_helper():
    assert _is_bijective({("a", "x"), ("b", "y")})
    assert not _is_bijective({("a", "x"), ("b", "x")})     # two bases -> one target
    assert not _is_bijective({("a", "x"), ("a", "y")})     # one base -> two targets


def test_non_bijective_match_hypotheses_are_rejected():
    # the CAUSE-level MH against the symbol-reusing target is non-bijective and dropped;
    # only the two clean base-level MHs (which conflict pairwise) remain
    mhs = match_hypotheses(_base(), _target_reused_symbol(), ascension=ASC)
    assert all(_is_bijective(m.corrs) for m in mhs)
    assert not any(m.order == 2 for m in mhs)              # the order-2 CAUSE MH was rejected


def test_clean_bijective_target_aligns_fully_and_scores_deterministically():
    g = align(_base(), _target_distinct_symbols(), ascension=ASC)
    assert g.correspondences == {"cal_test": "the_map", "the_weights": "kappa",
                                 "the_interval": "the_seq", "alpha_level": "the_rate"}
    assert g.score == 7.0


def test_score_is_stable_across_hash_seeds():
    # the real flap was across PROCESSES (hash randomization), so re-run in subprocesses
    prog = (
        "import sys; sys.path.insert(0, %r);"
        "from analogy.align import align;"
        "from analogy.predicates import Dgroup;"
        "b=Dgroup('b',[('WEIGHTED_EXCHANGEABLE','cal_test','the_weights'),"
        "('COVERAGE','the_interval','alpha_level'),"
        "('CAUSE',('WEIGHTED_EXCHANGEABLE','cal_test','the_weights'),"
        "('COVERAGE','the_interval','alpha_level'))]);"
        "t=Dgroup('t',[('CONTRACTION','the_map','kappa'),"
        "('LINEAR_CONVERGENCE','the_seq','the_rate'),"
        "('CAUSE',('CONTRACTION','the_map','kappa'),"
        "('LINEAR_CONVERGENCE','the_seq','the_rate'))]);"
        "asc={'WEIGHTED_EXCHANGEABLE':'P','CONTRACTION':'P','COVERAGE':'G','LINEAR_CONVERGENCE':'G'};"
        "print(align(b,t,ascension=asc).score)"
    ) % str(ROOT / "src")
    scores = set()
    for seed in ("0", "1", "2", "3", "4"):
        env = {"PYTHONHASHSEED": seed, "PATH": "/usr/bin:/bin"}
        out = subprocess.run([sys.executable, "-c", prog], capture_output=True, text=True, env=env)
        scores.add(out.stdout.strip())
    assert scores == {"7.0"}, scores

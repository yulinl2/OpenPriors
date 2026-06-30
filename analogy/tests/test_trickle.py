"""Epic I — trickle-down systematicity: a deep relational web is rewarded over flat facts."""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from analogy import examples
from analogy.align import align

T = 0.5


def test_trickle_default_is_backward_compatible():
    sb, st = examples.systematic_pair()
    assert align(sb, st).score == align(sb, st, trickle=0.0).score
    g = align(examples.solar_system(), examples.atom())
    assert g.correspondences == {"sun": "nucleus", "planet": "electron"}  # unchanged


def test_trickle_rewards_systematicity_more_than_flat():
    sb, st = examples.systematic_pair()
    fb, ft = examples.flat_pair()
    # concrete scores lock in the exact behavior (not just inequalities)
    assert align(sb, st).score == 12.0 and align(sb, st, trickle=T).score == 15.5
    assert align(fb, ft).score == 7.0 and align(fb, ft, trickle=T).score == 7.0
    d_sys = align(sb, st, trickle=T).score - align(sb, st).score
    d_flat = align(fb, ft, trickle=T).score - align(fb, ft).score
    assert d_sys == 3.5 and d_flat == 0.0  # web gains; isolated relations gain nothing
    assert d_sys > d_flat                  # systematicity preferred


def test_systematic_outscores_flat_under_trickle():
    sb, st = examples.systematic_pair()
    fb, ft = examples.flat_pair()
    # both share the three relations; with trickle the deep web scores strictly higher
    assert align(sb, st, trickle=T).score > align(fb, ft, trickle=T).score

"""OpenPriors analogy engine (Epic C / FAC): SME-style structural alignment + the
candidate-inference "shortcut" novelty detector."""

from .align import Gmap, align, match_hypotheses
from .novelty import novelty_report
from .predicates import Dgroup

__version__ = "0.1.0"
__all__ = ["Dgroup", "Gmap", "align", "match_hypotheses", "novelty_report"]

"""Candidate-inference novelty / "shortcut" signal (structure-mapping notes §6).

Intuition: once base and target are structurally aligned, if a *small* systematic mapping
already explains *most* of the target, the target is effectively the base's machinery on
relabeled objects — a "shortcut under fancy disguise". So:

    target_coverage = matched target facts / all target facts
    shortcut signal  ∝ coverage of target by the source mapping ÷ description length of M
    novelty          = 1 − target_coverage   (what the target adds beyond the renamed base)

Candidate inferences are what the base *predicts* about the target beyond what the target
states — the formal trace the novelty judge keys on.
"""

from __future__ import annotations

from .align import Gmap
from .predicates import Dgroup


def novelty_report(base: Dgroup, target: Dgroup, gmap: Gmap) -> dict:
    n_target = len(target.facts)
    matched_t = {repr(e) for e in gmap.matched_target}
    covered = sum(1 for f in target.facts if repr(f) in matched_t)
    coverage = covered / n_target if n_target else 0.0
    mapping_size = len(gmap.correspondences)
    n_matched = len(gmap.matched_base)
    desc_len = mapping_size + n_matched  # description length of the alignment M
    shortcut = (coverage * n_matched / desc_len) if desc_len else 0.0
    return {
        "target_facts": n_target,
        "matched_target_facts": covered,
        "target_coverage": round(coverage, 4),
        "mapping_size": mapping_size,
        "matched_relations": n_matched,
        "structural_score": gmap.score,
        "n_candidate_inferences": len(gmap.candidate_inferences),
        "top_inference": gmap.candidate_inferences[0]["projection"]
        if gmap.candidate_inferences else None,
        "shortcut_signal": round(shortcut, 4),
        "novelty_score": round(1.0 - coverage, 4),
    }

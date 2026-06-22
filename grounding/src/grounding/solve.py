"""Solve a riddle by structure mapping: align source->target, read off the blank.

The end-to-end payoff: align the SOURCE description (which has the worked answer) onto the
TARGET, confirm the known answer corresponds to the blank, then read the blank's *defining
relation* (DIVIDES vs EQUALS) to produce the structural answer. Near-identical surface,
different relation => different answer — the whole OpenPriors thesis, on raw prose.
"""

from __future__ import annotations

import re

from analogy.align import align
from analogy.predicates import args, functor


def _leaf_entities(e) -> set:
    if isinstance(e, str):
        return {e}
    out: set = set()
    for a in args(e):
        out |= _leaf_entities(a)
    return out


def _first_int(s: str):
    m = re.search(r"-?\d+", s)
    return int(m.group()) if m else None


def _unit(grounding: str):
    m = re.search(r"\d+\s+([A-Za-z]+)", grounding)
    return m.group(1) if m else ""


def solve(source_dg, target_dg, raw: dict) -> dict:
    g = align(source_dg, target_dg)
    answer_symbol = raw["source"]["answer_symbol"]
    blank_symbol = raw["target"]["blank_symbol"]
    tg = raw["target"]["groundings"]

    defining = None
    for f in target_dg.facts:
        if isinstance(f, tuple) and functor(f) in ("DIVIDES", "EQUALS") \
                and blank_symbol in _leaf_entities(f):
            defining = f
            break

    structural, numeric = None, None
    if defining is not None and functor(defining) == "DIVIDES":
        total, count, _ = args(defining)
        structural = f"{blank_symbol} = {total} ÷ {count}"
        tnum, cnum = _first_int(tg.get(total, "")), _first_int(tg.get(count, ""))
        if tnum is not None and cnum:
            numeric = f"{tnum // cnum if tnum % cnum == 0 else tnum / cnum} {_unit(tg.get(total, ''))}".strip()
    elif defining is not None and functor(defining) == "EQUALS":
        a, b = args(defining)
        total = b if a == blank_symbol else a
        structural = f"{blank_symbol} = {total} (the whole total, undivided)"
        tnum = _first_int(tg.get(total, ""))
        if tnum is not None:
            numeric = f"{tnum} {_unit(tg.get(total, ''))}".strip()

    return {
        "structural_score": g.score,
        "answer_maps_to_blank": g.correspondences.get(answer_symbol) == blank_symbol,
        "mapped_to": g.correspondences.get(answer_symbol),
        "blank_defining_relation": functor(defining) if defining else None,
        "structural_answer": structural,
        "numeric_answer": numeric,
    }

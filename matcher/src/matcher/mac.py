"""MAC stage: cheap content-vector retrieval (MAC/FAC, Forbus-Gentner-Law 1995).

The content vector is a bag of predicate/attribute labels (emitted by
``concept_graph.sme.content_vector``). The **dot product** of two content vectors is the
MAC score, and is an *upper bound* on the SME structural score — so ranking candidates by
dot product is a *sound* cheap pre-filter (items low on the MAC dot score cannot score
high under full structural matching). ``cosine`` is provided as a length-normalized
*similarity view* for interpretability; it does **not** carry the upper-bound guarantee,
so it is used for the human-readable similarity matrix, not for the retrieval short-list.
"""

from __future__ import annotations

from math import sqrt


def dot(v1: dict[str, int], v2: dict[str, int]) -> float:
    """MAC score: the content-vector dot product (upper-bounds SME structural score)."""
    keys = set(v1) & set(v2)
    return float(sum(v1[k] * v2[k] for k in keys))


# the sound MAC retrieval primitive
mac_score = dot


def cosine(v1: dict[str, int], v2: dict[str, int]) -> float:
    """Length-normalized similarity view (interpretable; NOT the upper-bound MAC score)."""
    n1 = sqrt(sum(x * x for x in v1.values()))
    n2 = sqrt(sum(x * x for x in v2.values()))
    return dot(v1, v2) / (n1 * n2) if n1 and n2 else 0.0


def similarity_matrix(vectors: dict[str, dict]) -> dict[str, dict[str, float]]:
    """Human-readable cosine matrix (a normalized view; see ``rank_against`` for retrieval)."""
    slugs = sorted(vectors)
    return {a: {b: round(cosine(vectors[a], vectors[b]), 4) for b in slugs} for a in slugs}


def rank_against(query: str, vectors: dict[str, dict]) -> list[tuple[str, float]]:
    """MAC short-list: rank candidates by the sound **dot-product** MAC score (self excluded)."""
    return sorted(
        ((b, round(dot(vectors[query], vectors[b]), 4)) for b in vectors if b != query),
        key=lambda kv: -kv[1],
    )

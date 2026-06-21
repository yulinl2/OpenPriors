"""MAC stage: cheap content-vector retrieval (MAC/FAC, Forbus-Gentner-Law 1995).

The content vector is a bag of predicate/attribute labels (emitted by
``concept_graph.sme.content_vector``). Its dot product is the MAC similarity and an
*upper bound* on the SME structural score, so it is a sound cheap pre-filter: items that
score low on MAC cannot score high under full structural matching.
"""

from __future__ import annotations

from math import sqrt


def dot(v1: dict[str, int], v2: dict[str, int]) -> float:
    keys = set(v1) & set(v2)
    return float(sum(v1[k] * v2[k] for k in keys))


def cosine(v1: dict[str, int], v2: dict[str, int]) -> float:
    n1 = sqrt(sum(x * x for x in v1.values()))
    n2 = sqrt(sum(x * x for x in v2.values()))
    return dot(v1, v2) / (n1 * n2) if n1 and n2 else 0.0


def similarity_matrix(vectors: dict[str, dict]) -> dict[str, dict[str, float]]:
    slugs = sorted(vectors)
    return {a: {b: round(cosine(vectors[a], vectors[b]), 4) for b in slugs} for a in slugs}


def rank_against(query: str, vectors: dict[str, dict]) -> list[tuple[str, float]]:
    """MAC short-list: rank all candidates by cosine to the query (self excluded)."""
    return sorted(
        ((b, round(cosine(vectors[query], vectors[b]), 4)) for b in vectors if b != query),
        key=lambda kv: -kv[1],
    )

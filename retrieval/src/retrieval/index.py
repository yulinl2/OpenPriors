"""ANN index for the MAC stage — SimHash LSH over content vectors (the indexing burden).

MAC's content-vector scan is O(N) over the whole library; at corpus scale that is the
"indexing burden over millions of sources" (notes §3). This is a pure-Python (no FAISS,
deterministic, auditable) **sign-random-projection LSH**: each content vector gets a K-bit
signature from K fixed random hyperplanes; similar vectors (high cosine) get similar
signatures, so a query only exact-scores the candidates in nearby Hamming buckets — a small
fraction of the library — then ranks those exactly. Recall is tunable via ``max_hamming``.
"""

from __future__ import annotations

import random
from itertools import combinations

from .engine import cosine


class MacIndex:
    def __init__(self, vectors: dict[str, dict], n_planes: int = 16, seed: int = 0):
        self.vectors = vectors
        self.n_planes = n_planes
        self.vocab = sorted({k for v in vectors.values() for k in v})
        self.vindex = {k: i for i, k in enumerate(self.vocab)}
        rng = random.Random(seed)                       # deterministic hyperplanes
        self.planes = [[rng.choice((-1.0, 1.0)) for _ in self.vocab]
                       for _ in range(n_planes)]
        self.buckets: dict[tuple, list[str]] = {}
        for name, vec in vectors.items():
            self.buckets.setdefault(self._sig(vec), []).append(name)

    def _sig(self, vec: dict) -> tuple:
        bits = []
        for plane in self.planes:
            dot = sum(val * plane[self.vindex[k]] for k, val in vec.items() if k in self.vindex)
            bits.append(1 if dot >= 0 else 0)
        return tuple(bits)

    def _nearby_buckets(self, sig: tuple, max_hamming: int):
        idx = range(self.n_planes)
        for h in range(max_hamming + 1):
            for flips in combinations(idx, h):
                s = list(sig)
                for i in flips:
                    s[i] ^= 1
                yield tuple(s)

    def query(self, qvec: dict, top_k: int = 2, max_hamming: int = 2) -> dict:
        sig = self._sig(qvec)
        seen: set[str] = set()
        for b in self._nearby_buckets(sig, max_hamming):
            seen.update(self.buckets.get(b, ()))
        ranked = sorted(((n, round(cosine(qvec, self.vectors[n]), 4)) for n in seen),
                        key=lambda kv: -kv[1])[:top_k]
        return {
            "top_k": ranked,
            "candidates_examined": len(seen),
            "library_size": len(self.vectors),
            "fraction_examined": round(len(seen) / max(1, len(self.vectors)), 4),
        }


def linear_top_k(qvec: dict, vectors: dict[str, dict], top_k: int = 2) -> list[tuple]:
    """Exact O(N) MAC scan, for correctness comparison against the index."""
    return sorted(((n, round(cosine(qvec, v), 4)) for n, v in vectors.items()),
                  key=lambda kv: -kv[1])[:top_k]


def _synthetic_vectors(n: int, seed: int = 1) -> dict[str, dict]:
    """Deterministic distractor content vectors over a fake functor vocabulary."""
    import random
    rng = random.Random(seed)
    funcs = [f"F{i}" for i in range(40)]
    return {f"syn{i}": {rng.choice(funcs): rng.randint(1, 4)
                        for _ in range(rng.randint(3, 8))} for i in range(n)}


def main(argv=None) -> int:
    import json
    from pathlib import Path

    from analogy.predicates import Dgroup

    from .engine import expr_from_json, functor_vector, load_library

    here = Path(__file__).resolve().parents[2]
    repo = here.parent
    vecs = {n: functor_vector(g) for n, g in load_library(here / "library" / "theorems.json").items()}
    vecs.update(_synthetic_vectors(1000))               # scale to ~1000 priors
    q = json.loads((repo / "grounding" / "dgroups" / "banach_case.json").read_text())["target"]
    qvec = functor_vector(Dgroup("q", [expr_from_json(f) for f in q["facts"]]))

    idx = MacIndex(vecs)
    res = idx.query(qvec)
    print(f"library size: {res['library_size']}; ANN nearest: {res['top_k'][0]}")
    print(f"candidates examined: {res['candidates_examined']} "
          f"({res['fraction_examined'] * 100:.1f}% of the library)")
    print(f"matches exact linear nearest: "
          f"{res['top_k'][0][0] == linear_top_k(qvec, vecs, 1)[0][0]}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

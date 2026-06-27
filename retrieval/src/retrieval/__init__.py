"""OpenPriors retrieval (Epic E): library-scale MAC/FAC novelty retrieval — find the
nearest known prior of a result from a theorem library."""

from .engine import functor_vector, load_library, retrieve

__version__ = "0.1.0"
__all__ = ["functor_vector", "load_library", "retrieve"]

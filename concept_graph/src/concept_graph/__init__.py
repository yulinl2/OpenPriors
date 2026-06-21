"""OpenPriors concept_graph: lift decomposer output into an (object, attribute, relation)
concept + reasoning-chain graph; the bridge to a structure-mapping matcher (Epic C)."""

from .schema import Concept, ConceptGraph, Relation, Triple

__version__ = "0.1.0"
__all__ = ["Concept", "ConceptGraph", "Relation", "Triple"]

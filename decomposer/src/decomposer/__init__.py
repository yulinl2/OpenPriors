"""OpenPriors decomposer: raw documents -> clean, nested, hierarchical structured data.

A first-principles, independently-verified document-decomposition workflow; the upstream
stage of OpenPriors' (object, attribute, relation) concept/reasoning graph.
"""

from .schema import Decomposition, Edge, Node, Role, SourceProvenance

__version__ = "0.1.0"
__all__ = ["Decomposition", "Edge", "Node", "Role", "SourceProvenance"]

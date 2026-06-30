"""Concept-graph schema: the (object, attribute, relation) representation.

Lifts a decomposer bundle (nodes + edges) into OpenPriors' target form:
* **Concept** = an *object* (a node), carrying its *attributes*.
* **Relation** = a typed edge between concepts (the *relation*), including derived
  semantic relations (`proves`, `derives_from`) that form the **reasoning-chain DAG**.
* **Triple** = the flat ``(subject, predicate, object)`` record — the minimal tuple a
  structure-mapping (SME/MAC-FAC) matcher consumes downstream.

Everything is traceable: each concept/relation records the source node/edge id it came
from (provenance), so the lift is auditable and conservation is checkable.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

SCHEMA_VERSION = "0.1.0"

Predicate = Literal[
    "contains",       # structural: parent concept contains child (the tree)
    "cites",          # structural: a block cites a bibliography concept
    "refers_to",      # structural: a cross-reference (\ref/\eqref)
    "proves",         # derived: a proof concept proves a theorem-like concept
    "derives_from",   # derived: a reasoning step depends on a prior result (the chain)
    "defines",        # derived: a definition/assumption/field introduces a named thing
]


class Concept(BaseModel):
    """An *object* with *attributes*."""

    model_config = {"extra": "forbid"}

    id: str                       # = source node id (stable, path-based)
    kind: str                     # node type (theorem, equation, section, ...)
    role: str                     # coarse role (assert/formalize/segment/...)
    name: Optional[str] = None    # title | label | short excerpt
    label: Optional[str] = None
    attributes: dict = Field(default_factory=dict)
    source_node: str              # provenance


class Relation(BaseModel):
    """A typed *relation* between two concepts (an edge / a predicate)."""

    model_config = {"extra": "forbid"}

    id: str
    subject: str
    predicate: Predicate
    object: str
    resolved: bool = True
    higher_order: bool = False    # relation over relations (SME systematicity)
    attributes: dict = Field(default_factory=dict)
    provenance: str               # source edge/node id

    def triple(self) -> "Triple":
        return Triple(s=self.subject, p=self.predicate, o=self.object)


class Triple(BaseModel):
    """Flat OAR record — the SME/MAC content-vector unit."""

    model_config = {"extra": "forbid"}

    s: str
    p: str
    o: str


class ConceptGraph(BaseModel):
    model_config = {"extra": "forbid"}

    schema_version: str = SCHEMA_VERSION
    slug: str
    concepts: list[Concept] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)
    metrics: dict = Field(default_factory=dict)

    def concept_ids(self) -> set[str]:
        return {c.id for c in self.concepts}

    def triples(self) -> list[Triple]:
        return [r.triple() for r in self.relations]

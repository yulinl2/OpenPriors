"""Single source of truth for the decomposer data classes (principle **P3**).

Design (see ``docs/decisions/0001-format-and-tooling.md``):

* **Pydantic v2** models => validation + ``model_json_schema()`` for audit.
* A *coarse* :class:`Role` layer (format-agnostic, 7 roles) sits above a *fine*
  :class:`NodeType` vocabulary (JATS-inspired, extensible). Classifiers and adapters
  target the role layer, which is what makes the workflow generalize across formats.
* A document is simultaneously a **tree** (``Node.children`` -> ``document.json``)
  and a **graph** (flat ``nodes.jsonl`` + ``edges.jsonl``), bridging to OpenPriors'
  eventual ``(object, attribute, relation)`` representation: a Node *is* an object,
  its scalar fields are attributes, an Edge is a relation.

Extending the taxonomy = add a ``NodeType`` literal + a ``TYPE_ROLE`` entry. No new
class, no schema migration. That is the "易拓展" (easy-to-extend) property.
"""

from __future__ import annotations

import hashlib
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

SCHEMA_VERSION = "0.1.0"


# --------------------------------------------------------------------------- #
# Coarse role layer (format-agnostic) — the generalization surface.           #
# --------------------------------------------------------------------------- #
class Role(str, Enum):
    """The seven *roles* a structural unit can play in human technical writing.

    Surface markup is unbounded and idiosyncratic; *roles* are few and stable
    across formats (LaTeX env, custom macro, bold-prose, markdown heading). The
    workflow keys on roles so it survives an unknown next document.
    """

    SEGMENT = "segment"        # sections / headings — partition the document
    ASSERT = "assert"          # theorems / definitions / claims / problem statements
    FORMALIZE = "formalize"    # equations / displayed math
    REFER = "refer"            # citations, cross-references, bibliography entries
    EXEMPLIFY = "exemplify"    # examples, problems, samples, riddles
    NARRATE = "narrate"        # ordinary prose paragraphs / lists
    META = "meta"             # comments, editor notes, grading schemes, metadata fields


# --------------------------------------------------------------------------- #
# Fine node-type vocabulary (JATS-inspired + theorem/exam extensions).         #
# --------------------------------------------------------------------------- #
NodeType = Literal[
    "document",
    "section",
    "paragraph",
    "list",
    "list_item",
    "theorem",       # theorem | lemma | proposition | corollary | conjecture (see attrs.kind)
    "definition",
    "assumption",
    "remark",
    "proof",
    "equation",
    "problem_statement",
    "answer_key",
    "grading_scheme",
    "editor_notes",
    "example",
    "riddle",
    "metadata_field",
    "problem",        # generic exemplifying problem (EXEMPLIFY role)
    "bib_reference",
    "citation",
    "cross_reference",
    "figure",
    "table",
    "block",         # generic unclassified residual (kept small + itemized)
]

# Authoritative type -> role map. Classifiers MUST stay consistent with this.
TYPE_ROLE: dict[str, Role] = {
    "document": Role.SEGMENT,
    "section": Role.SEGMENT,
    "paragraph": Role.NARRATE,
    "list": Role.NARRATE,
    "list_item": Role.NARRATE,
    "theorem": Role.ASSERT,
    "definition": Role.ASSERT,
    "assumption": Role.ASSERT,
    "remark": Role.ASSERT,
    "proof": Role.ASSERT,
    "problem_statement": Role.ASSERT,
    "answer_key": Role.ASSERT,
    "equation": Role.FORMALIZE,
    "grading_scheme": Role.META,
    "editor_notes": Role.META,
    "metadata_field": Role.META,
    "example": Role.EXEMPLIFY,
    "riddle": Role.EXEMPLIFY,
    "problem": Role.EXEMPLIFY,
    "bib_reference": Role.REFER,
    "citation": Role.REFER,
    "cross_reference": Role.REFER,
    "figure": Role.NARRATE,
    "table": Role.NARRATE,
    "block": Role.NARRATE,
}

RelationType = Literal[
    "contains",        # parent -> child (the containment tree)
    "cites",           # block -> bib_reference (from \cite)
    "refers_to",       # block -> labeled node (from \ref / \eqref)
    "in_bibliography",  # bib_reference -> document
    "has_label",       # node -> its label string (degenerate; kept for completeness)
]


# --------------------------------------------------------------------------- #
# Models                                                                       #
# --------------------------------------------------------------------------- #
class Span(BaseModel):
    """Half-open ``[start, end)`` char offsets into the *normalized* source.

    Powers the conservation / character-coverage invariant (principle **P1**).
    """

    start: int
    end: int

    @property
    def length(self) -> int:
        return self.end - self.start


class Node(BaseModel):
    """A structural unit. An *object* in the eventual (object, attribute, relation) graph."""

    model_config = {"extra": "forbid"}

    id: str = Field(description="Stable path/logical id, unique within the document.")
    type: NodeType
    role: Role
    label: Optional[str] = Field(default=None, description="LaTeX \\label / HTML anchor.")
    title: Optional[str] = None
    text: Optional[str] = Field(default=None, description="Normalized textual payload (leaf content).")
    depth: int = 0
    order: int = Field(default=0, description="Reading order within the parent.")
    span: Optional[Span] = None
    source_file: Optional[str] = None
    content_sha256: Optional[str] = None
    attrs: dict[str, Any] = Field(default_factory=dict, description="Extensible type-specific payload (kind, numbering, bib fields, mathml, ...).")
    children: list["Node"] = Field(default_factory=list)

    def iter_descendants(self):
        for c in self.children:
            yield c
            yield from c.iter_descendants()

    def flat(self) -> "Node":
        """A copy with ``children`` stripped (for the flat node stream)."""
        return self.model_copy(update={"children": []})


class Edge(BaseModel):
    """A *relation* in the eventual (object, attribute, relation) graph."""

    model_config = {"extra": "forbid"}

    id: str
    source: str
    target: str
    relation: RelationType
    resolved: bool = True
    attrs: dict[str, Any] = Field(default_factory=dict)


class SourceProvenance(BaseModel):
    """Where the document came from + how it was processed (full metadata)."""

    model_config = {"extra": "forbid"}

    slug: str
    origin: str                      # arxiv id / file path / url
    formats: list[str]               # e.g. ["latex", "html"]
    retrieved_at: Optional[str] = None
    source_files: list[str] = Field(default_factory=list)
    source_sha256: dict[str, str] = Field(default_factory=dict)
    tool_versions: dict[str, str] = Field(default_factory=dict)
    external_ids: dict[str, str] = Field(default_factory=dict)  # arxiv/doi/...


class Decomposition(BaseModel):
    """Top-level bundle: nested document + cross-ref edges + provenance + metrics."""

    model_config = {"extra": "forbid"}

    schema_version: str = SCHEMA_VERSION
    provenance: SourceProvenance
    document: Node
    edges: list[Edge] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)

    def all_nodes(self) -> list[Node]:
        out = [self.document]
        out.extend(self.document.iter_descendants())
        return out


def content_hash(text: str) -> str:
    """Stable SHA-256 of a node's textual content (audit / dedup / change-detection)."""
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def role_for(node_type: str) -> Role:
    return TYPE_ROLE.get(node_type, Role.NARRATE)

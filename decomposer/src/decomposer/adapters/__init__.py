"""Format-specific adapters feeding the format-agnostic core.

Each adapter exposes the same surface so the pipeline is format-blind:

    normalize(raw_or_path) -> NormalizeResult(text, removal_log, macros)
    extract(normalized_text, slug) -> (root: Node, edges: list[Edge])

Adapters target the coarse :class:`~decomposer.schema.Role` layer, which is what
lets the same core serve LaTeX papers, exam macros, and plain prose.
"""

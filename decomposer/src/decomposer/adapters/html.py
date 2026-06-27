"""HTML adapter: decompose ar5iv / LaTeXML HTML into the same role-based structure.

Generalizes ingestion beyond LaTeX/Markdown. LaTeXML HTML is richly classed
(``ltx_section``, ``ltx_theorem_*``, ``ltx_equation``, ``ltx_cite``, ``ltx_bibitem`` ...),
so the role mapping is direct. Decomposing the *same* paper from its HTML and from its
LaTeX source gives two independent ingestion paths that can be cross-checked (a differential
test, in addition to the per-document invariants).
"""

from __future__ import annotations

import re
from pathlib import Path

from lxml import html as lhtml

from ..schema import Edge, Node, content_hash, role_for
from .latex import NormalizeResult

_WS = re.compile(r"\s+")

# ltx_theorem_<kind> -> our node type
_THM_KIND = {"theorem": "theorem", "proposition": "theorem", "lemma": "theorem",
             "corollary": "theorem", "definition": "definition", "assumption": "assumption",
             "remark": "remark", "proof": "proof"}
_SEC_LEVEL = {"ltx_section": 1, "ltx_subsection": 2, "ltx_subsubsection": 3,
              "ltx_appendix": 1, "ltx_paragraph": 4}


def _classes(el) -> set[str]:
    return set((el.get("class") or "").split())


def _vis(el) -> str:
    """Collapsed visible text of an element, excluding LaTeXML numbering tags."""
    parts = [el.text or ""]
    for child in el:
        if "ltx_tag" not in (child.get("class") or ""):
            parts.append("".join(child.itertext()))
        parts.append(child.tail or "")
    return _WS.sub(" ", "".join(parts)).strip()


def _title_of(el) -> str | None:
    for child in el:
        if "ltx_title" in (child.get("class") or ""):
            return _vis(child) or None
    return None


# --------------------------------------------------------------------------- #
# Step 2: normalize — the canonical visible text (P2 is light for HTML)        #
# --------------------------------------------------------------------------- #
def _body(root):
    for cls in ("ltx_document", "ltx_page_content"):
        els = root.find_class(cls)
        if els:
            return els[0]
    return root


def normalize(path: str | Path):
    raw = Path(path).read_text(encoding="utf-8")
    root = lhtml.fromstring(raw)
    text = _WS.sub(" ", "".join(_body(root).itertext())).strip()
    log = [{"op": "html_visible_text", "chars": len(text)}]
    return NormalizeResult(text=text, removal_log=log, macros={}), raw


def normalize_text(text: str) -> str:
    return _WS.sub(" ", text).strip()  # idempotent


# --------------------------------------------------------------------------- #
# Steps 3 & 4: structure extraction over the DOM                               #
# --------------------------------------------------------------------------- #
class _Ctx:
    def __init__(self, normalized: str):
        self.norm = normalized
        self.cursor = 0
        self.counter: dict[str, int] = {}
        self.edges: list[Edge] = []
        self.labels: dict[str, str] = {}   # html id -> node id

    def nid(self, kind: str, parent: str) -> str:
        self.counter[kind] = self.counter.get(kind, 0) + 1
        return f"{parent}/{kind}.{self.counter[kind]}"

    def span(self, text: str):
        if not text:
            return None
        pos = self.norm.find(text[:60], self.cursor)
        if pos < 0:
            return None
        end = pos + len(text)
        self.cursor = pos + len(text[:60])
        return {"start": pos, "end": min(end, len(self.norm))}


def _leaf(ctx: _Ctx, el, ntype: str, nid: str, depth: int, order: int, **attrs) -> Node:
    text = _vis(el)
    return Node(id=nid, type=ntype, role=role_for(ntype),
                title=attrs.pop("title", None), text=text or None, depth=depth, order=order,
                span=ctx.span(text), content_sha256=content_hash(text) if text else None,
                attrs=attrs)


def _refs_in(ctx: _Ctx, el, source_id: str):
    for a in el.find_class("ltx_ref"):
        href = a.get("href") or ""
        if href.startswith("#"):
            tgt = href[1:]
            rel = "cites" if tgt.startswith("bib") else "refers_to"
            ctx.edges.append(Edge(id=ctx.nid("edge", "e"), source=source_id, target=tgt,
                                  relation=rel, resolved=False, attrs={"href": tgt}))


def _walk(ctx: _Ctx, el, parent_id: str, depth: int) -> list[Node]:
    out: list[Node] = []
    order = 0
    for child in el:
        cls = _classes(child)
        # sectioning containers
        sec = next((c for c in cls if c in _SEC_LEVEL), None)
        if sec or "ltx_abstract" in cls:
            title = _title_of(child) or ("Abstract" if "ltx_abstract" in cls else None)
            nid = ctx.nid("section", parent_id)
            node = Node(id=nid, type="section", role=role_for("section"), title=title,
                        depth=depth, order=order, attrs={"html_class": sec or "ltx_abstract"})
            node.children = _walk(ctx, child, nid, depth + 1)
            out.append(node); order += 1; continue
        # theorem-like
        if "ltx_theorem" in cls:
            kind = next((c.split("ltx_theorem_")[1] for c in cls if c.startswith("ltx_theorem_")), "theorem")
            ntype = _THM_KIND.get(kind, "theorem")
            nid = ctx.nid(ntype, parent_id)
            n = _leaf(ctx, child, ntype, nid, depth, order, title=_title_of(child), kind=kind)
            _refs_in(ctx, child, nid); out.append(n); order += 1; continue
        # equations
        if "ltx_equation" in cls or "ltx_equationgroup" in cls:
            nid = ctx.nid("equation", parent_id)
            math = child.find_class("ltx_Math")
            attrs = {}
            if math and math[0].get("alttext"):
                attrs["latex"] = math[0].get("alttext")
            out.append(_leaf(ctx, child, "equation", nid, depth, order, **attrs)); order += 1; continue
        # bibliography
        if "ltx_bibliography" in cls:
            nid = ctx.nid("section", parent_id)
            sec_node = Node(id=nid, type="section", role=role_for("section"),
                            title="References", depth=depth, order=order, attrs={"auto": True})
            bo = 0
            for bib in child.find_class("ltx_bibitem"):
                bid = bib.get("id") or ctx.nid("bib", nid)
                node_bid = f"{nid}/bib.{bo + 1}"
                ctx.labels[bid] = node_bid
                sec_node.children.append(_leaf(ctx, bib, "bib_reference", node_bid, depth + 1, bo, bibhtmlid=bid))
                bo += 1
            out.append(sec_node); order += 1; continue
        # paragraphs — but if a para wraps display equations, split them out
        if "ltx_para" in cls or "ltx_p" in cls:
            if child.find_class("ltx_equation") or child.find_class("ltx_equationgroup"):
                nested = _walk(ctx, child, parent_id, depth)
                for n in nested:
                    n.order = order; order += 1
                out.extend(nested); continue
            nid = ctx.nid("paragraph", parent_id)
            n = _leaf(ctx, child, "paragraph", nid, depth, order)
            _refs_in(ctx, child, nid); out.append(n); order += 1; continue
        # titles are consumed by their parent; skip standalone
        if "ltx_title" in cls:
            continue
        # otherwise descend to find nested ltx_ elements
        nested = _walk(ctx, child, parent_id, depth)
        if nested:
            for n in nested:
                n.order = order; order += 1
            out.extend(nested)
    return out


def extract(raw_html: str, normalized_text: str, slug: str, root_id: str):
    root_el = lhtml.fromstring(raw_html)
    ctx = _Ctx(normalized_text)
    children = _walk(ctx, _body(root_el), root_id, 1)
    root = Node(id=root_id, type="document", role=role_for("document"), title=slug,
                depth=0, order=0, children=children, attrs={"adapter": "html"})

    # resolve cite/ref edges against bib html-ids and node ids
    node_ids = {n.id for n in [root, *root.iter_descendants()]}
    for e in ctx.edges:
        tgt = ctx.labels.get(e.target)
        if tgt and tgt in node_ids:
            e.target, e.resolved = tgt, True
        else:
            e.attrs["external"] = True
    return root, ctx.edges

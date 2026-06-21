"""Markdown adapter: handles prose riddles and metadata forms.

Same surface as the LaTeX adapter (``normalize`` / ``extract``), targeting the coarse
:class:`~decomposer.schema.Role` layer so the format-agnostic core is unchanged.

Two documented case-by-case rules (PEP-5 in ``docs/principles.md``):
  * a list item shaped ``- **Key:** value`` => a ``metadata_field`` (form fields);
  * a heading-less doc segmented by thematic breaks => each chunk is an ``example``
    whose blockquote child is the *source* analog and prose child the *target*
    (the structure-mapping pair OpenPriors cares about).
"""

from __future__ import annotations

import re
from pathlib import Path

from ..schema import Edge, Node, content_hash, role_for
from .latex import NormalizeResult, _Block  # reuse dataclasses

_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*$")
_THEMATIC = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,}|[—–]+)\s*$")
_FENCE = re.compile(r"^\s*(```+|~~~+)(.*)$")
_LISTITEM = re.compile(r"^(\s*)(?:[-*+]|\d+[.)])\s+(.*)$")
_METAFIELD = re.compile(r"^\*{0,2}([A-Z][^:*]{0,60}?):\*{0,2}\s*(.*)$")
_BLANK = re.compile(r"^\s*$")


# --------------------------------------------------------------------------- #
# Step 2: normalize (P2) — markdown carries little redundancy; keep idempotent #
# --------------------------------------------------------------------------- #
def normalize_text(text: str) -> NormalizeResult:
    before = len(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)          # HTML comments
    text = "\n".join(line.rstrip() for line in text.split("\n"))  # trailing ws
    text = re.sub(r"\n{3,}", "\n\n", text).strip()                # blank-line runs
    log = [{"op": "normalize_markdown", "chars": before - len(text)}]
    return NormalizeResult(text=text, removal_log=log, macros={})


def normalize(src: str | Path) -> tuple[NormalizeResult, str]:
    raw = Path(src).read_text(encoding="utf-8") if Path(str(src)).exists() else str(src)
    return normalize_text(raw), raw


# --------------------------------------------------------------------------- #
# Steps 3 & 4: extract                                                         #
# --------------------------------------------------------------------------- #
def _line_offsets(text: str) -> list[int]:
    offs, pos = [], 0
    for line in text.split("\n"):
        offs.append(pos)
        pos += len(line) + 1
    return offs


def _parse_blocks(text: str) -> list[_Block]:
    lines = text.split("\n")
    offs = _line_offsets(text)
    blocks: list[_Block] = []
    i, n = 0, len(lines)
    buf, buf_start = [], None

    def flush():
        nonlocal buf, buf_start
        if buf and buf_start is not None:
            content = "\n".join(buf).strip()
            if content:
                end = buf_start + len("\n".join(buf))
                blocks.append(_Block("paragraph", None, None, buf_start, end, content))
        buf, buf_start = [], None

    while i < n:
        line = lines[i]
        start = offs[i]
        if _BLANK.match(line):
            flush(); i += 1; continue
        m = _HEADING.match(line)
        if m:
            flush()
            blocks.append(_Block("section", m.group(2).strip(), None, start,
                                 start + len(line), "", level=len(m.group(1))))
            i += 1; continue
        if _THEMATIC.match(line):
            flush()
            blocks.append(_Block("divider", None, None, start, start + len(line), ""))
            i += 1; continue
        fm = _FENCE.match(line)
        if fm:
            flush()
            fence = fm.group(1)[0]
            j = i + 1
            while j < n and not lines[j].lstrip().startswith(fence * 3):
                j += 1
            end = offs[j] + len(lines[j]) if j < n else offs[-1] + len(lines[-1])
            blocks.append(_Block("block", None, None, start, end,
                                 "\n".join(lines[i:j + 1]).strip(), kind="code"))
            i = j + 1; continue
        if line.lstrip().startswith(">"):
            flush()
            j = i
            while j < n and (lines[j].lstrip().startswith(">") or _BLANK.match(lines[j]) is None and lines[j].startswith(" ")):
                if lines[j].lstrip().startswith(">"):
                    j += 1
                else:
                    break
            quote = "\n".join(re.sub(r"^\s*>\s?", "", ln) for ln in lines[i:j]).strip()
            end = offs[j - 1] + len(lines[j - 1])
            blocks.append(_Block("block", None, None, start, end, quote, kind="blockquote"))
            i = j; continue
        lm = _LISTITEM.match(line)
        if lm:
            flush()
            items = []
            while i < n and (_LISTITEM.match(lines[i]) or (not _BLANK.match(lines[i]) and lines[i].startswith("  "))):
                im = _LISTITEM.match(lines[i])
                if im:
                    body = im.group(2)
                    s = offs[i]
                    mf = _METAFIELD.match(body)
                    if mf:  # "Key: value" form => a form field
                        items.append(_Block("metadata_field", mf.group(1).strip(), None,
                                            s, s + len(lines[i]), mf.group(2).strip()))
                    else:
                        items.append(_Block("list_item", None, None, s,
                                            s + len(lines[i]), body.strip()))
                i += 1
            lst = _Block("list", None, None, items[0].start if items else start,
                         items[-1].end if items else start + len(line), "")
            lst.children = items
            blocks.append(lst); continue
        # ordinary text
        if buf_start is None:
            buf_start = start
        buf.append(line); i += 1
    flush()
    return blocks


def _build_tree(blocks: list[_Block]) -> list[_Block]:
    headings = [b for b in blocks if b.type == "section"]
    dividers = [b for b in blocks if b.type == "divider"]
    # Special rule: heading-less + divider-segmented => example chunks.
    if not headings and dividers:
        chunks, cur = [], []
        for b in blocks:
            if b.type == "divider":
                if cur:
                    chunks.append(cur); cur = []
            else:
                cur.append(b)
        if cur:
            chunks.append(cur)
        out = []
        for k, chunk in enumerate(chunks):
            for c in chunk:                       # tag source/target of the analogy pair
                if c.type == "block" and c.kind == "blockquote":
                    c.kind = "source_analog"
                elif c.type == "paragraph":
                    c.kind = "target_analog"
            ex = _Block("example", f"riddle {k + 1}", None,
                        chunk[0].start, chunk[-1].end, "", kind="riddle")
            ex.children = chunk
            out.append(ex)
        return out
    # Normal: nest by heading level.
    root_children: list[_Block] = []
    stack: list[tuple[int, _Block]] = []
    for b in blocks:
        if b.type == "divider":
            continue
        if b.type == "section":
            while stack and stack[-1][0] >= b.level:
                stack.pop()
            (stack[-1][1].children if stack else root_children).append(b)
            stack.append((b.level, b))
        else:
            (stack[-1][1].children if stack else root_children).append(b)
    return root_children


def _to_nodes(blocks: list[_Block], parent_id: str, depth: int, counter: dict) -> list[Node]:
    out = []
    for order, b in enumerate(blocks):
        counter[b.type] = counter.get(b.type, 0) + 1
        nid = f"{parent_id}/{b.type}.{counter[b.type]}"
        attrs = {}
        if b.kind:
            attrs["kind"] = b.kind
        node = Node(
            id=nid, type=b.type if b.type != "divider" else "block",
            role=role_for(b.type), label=b.label, title=b.title,
            text=(b.text or None) if not b.children else None,
            depth=depth, order=order, span={"start": b.start, "end": b.end},
            content_sha256=content_hash(b.text) if b.text else None, attrs=attrs,
        )
        node.children = _to_nodes(b.children, nid, depth + 1, counter) if b.children else []
        out.append(node)
    return out


def extract(normalized_text: str, slug: str, root_id: str) -> tuple[Node, list[Edge]]:
    blocks = _parse_blocks(normalized_text)
    tree = _build_tree(blocks)
    children = _to_nodes(tree, root_id, 1, {})
    root = Node(id=root_id, type="document", role=role_for("document"),
                title=slug, depth=0, order=0, children=children,
                attrs={"adapter": "markdown"})
    return root, []

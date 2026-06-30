"""LaTeX adapter: de-redundancy (P2) + structure extraction (P3/P4).

Deterministic and pure-Python (pylatexenc). Every redundancy removal is logged so it
is reversible on paper (P2). Spans are offsets into the *normalized body*, which is the
canonical text the coverage invariant (P1) audits.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from pylatexenc.latexwalker import (
    LatexCharsNode,
    LatexCommentNode,
    LatexEnvironmentNode,
    LatexGroupNode,
    LatexMacroNode,
    LatexMathNode,
    LatexSpecialsNode,
    LatexWalker,
)

from ..schema import Edge, Node, content_hash, role_for

# --------------------------------------------------------------------------- #
# Vocabulary                                                                   #
# --------------------------------------------------------------------------- #
SECTION_LEVEL = {
    "part": 0, "chapter": 0, "section": 1, "subsection": 2,
    "subsubsection": 3, "paragraph": 4, "subparagraph": 5,
}
# environment name -> (node type, is_container)
ENV_TYPE = {
    "theorem": ("theorem", False), "lemma": ("theorem", False),
    "proposition": ("theorem", False), "corollary": ("theorem", False),
    "conjecture": ("theorem", False), "claim": ("theorem", False),
    "definition": ("definition", False), "assumption": ("assumption", False),
    "remark": ("remark", False), "proof": ("proof", False),
    "example": ("example", False),
    "equation": ("equation", False), "equation*": ("equation", False),
    "align": ("equation", False), "align*": ("equation", False),
    "gather": ("equation", False), "gather*": ("equation", False),
    "multline": ("equation", False), "eqnarray": ("equation", False),
    "displaymath": ("equation", False),
    "itemize": ("list", True), "enumerate": ("list", True),
    # exam-bank custom envs (problem_07.tex)
    "msbproblem": ("block", True), "problemstatement": ("problem_statement", True),
    "answerkey": ("answer_key", True), "gradingscheme": ("grading_scheme", True),
    "editornotes": ("editor_notes", True),
    "abstract": ("section", True),
}
THEOREM_KINDS = {"theorem", "lemma", "proposition", "corollary", "conjecture",
                 "claim", "definition", "assumption", "remark"}
CITE_MACROS = {"cite", "citep", "citet", "citealp", "citeauthor", "citeyear",
               "Citet", "Citep"}
REF_MACROS = {"ref", "eqref", "autoref", "cref", "Cref", "pageref"}
# Custom metadata macros (case-by-case adapter rule, see docs/principles.md PEP-5).
# Maps an undefined-but-known macro to the field names of its positional args.
META_MACROS = {
    "problemsetup": ["title", "subject", "subtopic", "level", "contributor",
                     "contact", "status"],
    "problemtags": ["question_type", "challenged_capability",
                    "verification_method", "observed_failure_mode"],
}


def _sanitize_title(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = s.strip()
    if s.startswith("*"):
        s = s[1:].strip()
    return s or None


def _is_real_label(s: Optional[str]) -> bool:
    return bool(s) and "=" not in s and not s.startswith("\\")


@dataclass
class NormalizeResult:
    text: str                         # canonical normalized body
    removal_log: list = field(default_factory=list)
    macros: dict = field(default_factory=dict)
    preamble_macros: int = 0


# --------------------------------------------------------------------------- #
# Step 1 (filesystem): flatten \input / \subfile                              #
# --------------------------------------------------------------------------- #
_INPUT_RE = re.compile(r"\\(?:input|include|subfile)\s*\{([^}]+)\}")


def flatten_inputs(main_path: str | Path, _seen: Optional[set] = None) -> tuple[str, list]:
    main_path = Path(main_path)
    _seen = _seen or set()
    log: list = []
    if main_path.resolve() in _seen:
        return "", log
    _seen.add(main_path.resolve())
    text = main_path.read_text(encoding="utf-8", errors="replace")

    def repl(m: re.Match) -> str:
        name = m.group(1).strip()
        cand = main_path.parent / name
        for p in (cand, cand.with_suffix(".tex"), Path(str(cand) + ".tex")):
            if p.exists():
                inc, sub = flatten_inputs(p, _seen)
                log.append({"op": "flatten_input", "file": p.name, "chars": len(inc)})
                log.extend(sub)
                return inc
        log.append({"op": "flatten_input_missing", "file": name})
        return ""  # missing include -> drop, logged

    return _INPUT_RE.sub(repl, text), log


# --------------------------------------------------------------------------- #
# Step 2 (pure): macro table + comment strip + expansion + whitespace          #
# --------------------------------------------------------------------------- #
_NEWCMD_RE = re.compile(
    r"\\(?:newcommand|renewcommand|providecommand)\*?\s*\{?\\([a-zA-Z]+)\}?\s*"
    r"(?:\[(\d+)\])?\s*(?:\[[^\]]*\])?\s*\{",
)


def extract_macros(text: str) -> dict:
    """Parse simple ``\\newcommand`` definitions: name -> (nargs, body)."""
    macros: dict = {}
    for m in _NEWCMD_RE.finditer(text):
        name = m.group(1)
        nargs = int(m.group(2) or 0)
        body = _grab_balanced(text, m.end() - 1)
        if body is None:
            continue
        macros[name] = (nargs, body)
    return macros


def _grab_balanced(text: str, open_brace_idx: int) -> Optional[str]:
    """Return the content between matching braces; ``open_brace_idx`` points at '{'."""
    if open_brace_idx >= len(text) or text[open_brace_idx] != "{":
        return None
    depth, i = 0, open_brace_idx
    while i < len(text):
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[open_brace_idx + 1:i]
        i += 1
    return None


def strip_comments(text: str) -> tuple[str, int]:
    """Remove LaTeX comments (``%`` to EOL), respecting escaped ``\\%``."""
    out, removed, i, n = [], 0, 0, len(text)
    while i < n:
        c = text[i]
        if c == "\\" and i + 1 < n:
            out.append(text[i:i + 2]); i += 2; continue
        if c == "%":
            j = i
            while i < n and text[i] != "\n":
                i += 1
            removed += i - j
            continue
        out.append(c); i += 1
    return "".join(out), removed


def _grab_args(text: str, idx: int, n: int) -> Optional[tuple[list, int]]:
    args, i = [], idx
    for _ in range(n):
        while i < len(text) and text[i] in " \t\n":
            i += 1
        if i >= len(text) or text[i] != "{":
            return None
        body = _grab_balanced(text, i)
        if body is None:
            return None
        args.append(body)
        i += len(body) + 2
    return args, i


def expand_macros(text: str, macros: dict, max_passes: int = 6) -> tuple[str, int]:
    """Expand user macros to a fixpoint (=> idempotent). Returns (text, n_expansions)."""
    total = 0
    zero = {k: v[1] for k, v in macros.items() if v[0] == 0}
    narg = {k: v for k, v in macros.items() if v[0] > 0}
    for _ in range(max_passes):
        changed = False
        # zero-arg: simple boundary-safe substitution
        for name, body in sorted(zero.items(), key=lambda kv: -len(kv[0])):
            pat = re.compile(r"\\" + re.escape(name) + r"(?![a-zA-Z])")
            text, k = pat.subn(lambda _m: body, text)
            if k:
                total += k; changed = True
        # n-arg: manual scan
        for name, (nargs, body) in sorted(narg.items(), key=lambda kv: -len(kv[0])):
            out, i, n = [], 0, len(text)
            tok = "\\" + name
            while i < n:
                if text.startswith(tok, i) and (i + len(tok) >= n or not text[i + len(tok)].isalpha()):
                    got = _grab_args(text, i + len(tok), nargs)
                    if got is not None:
                        args, end = got
                        expanded = body
                        for j, a in enumerate(args, 1):
                            expanded = expanded.replace(f"#{j}", a)
                        out.append(expanded); i = end; total += 1; changed = True
                        continue
                out.append(text[i]); i += 1
            text = "".join(out)
        if not changed:
            break
    return text, total


_WS_RE = re.compile(r"[ \t]+")
_BLANKLINES_RE = re.compile(r"\n[ \t]*\n(?:[ \t]*\n)+")


def collapse_whitespace(text: str) -> tuple[str, int]:
    before = len(text)
    text = _WS_RE.sub(" ", text)
    text = _BLANKLINES_RE.sub("\n\n", text)
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return text.strip(), before - len(text)


def _strip_to_body(text: str) -> tuple[str, int]:
    m = re.search(r"\\begin\{document\}", text)
    e = re.search(r"\\end\{document\}", text)
    if m and e:
        removed = m.end() + (len(text) - e.start())
        return text[m.end():e.start()], removed
    return text, 0


def normalize_text(text: str, macros: Optional[dict] = None) -> NormalizeResult:
    """Pure, idempotent normalization of LaTeX *body* text (P2)."""
    macros = macros if macros is not None else extract_macros(text)
    body, pre_removed = _strip_to_body(text)
    body, n_comments = strip_comments(body)
    body, n_exp = expand_macros(body, macros)
    body, n_ws = collapse_whitespace(body)
    log = [
        {"op": "strip_preamble_and_doc_wrappers", "chars": pre_removed},
        {"op": "strip_comments", "chars": n_comments},
        {"op": "expand_macros", "count": n_exp, "n_macros": len(macros)},
        {"op": "collapse_whitespace", "chars": n_ws},
    ]
    return NormalizeResult(text=body, removal_log=log, macros=macros,
                           preamble_macros=len(macros))


def normalize(main_path: str | Path) -> tuple[NormalizeResult, str]:
    """Full Step-1+2: flatten includes then normalize. Returns (result, raw_flattened)."""
    flat, flog = flatten_inputs(main_path)
    macros = extract_macros(flat)
    res = normalize_text(flat, macros)
    res.removal_log = flog + res.removal_log
    return res, flat


# --------------------------------------------------------------------------- #
# Steps 3 & 4: structure extraction over the normalized body                   #
# --------------------------------------------------------------------------- #
def _node_text(body: str, node) -> str:
    return body[node.pos:node.pos + node.len]


def _macro_arg_text(node) -> str:
    if not getattr(node, "nodeargd", None) or not node.nodeargd.argnlist:
        return ""
    parts = []
    for arg in node.nodeargd.argnlist:
        if arg is None:
            continue
        if isinstance(arg, LatexGroupNode):
            parts.append("".join(_plain(n) for n in arg.nodelist))
        else:
            parts.append(_plain(arg))
    return " ".join(p for p in parts if p).strip()


def _plain(node) -> str:
    if isinstance(node, LatexCharsNode):
        return node.chars
    if isinstance(node, LatexGroupNode):
        return "".join(_plain(n) for n in node.nodelist)
    if isinstance(node, LatexMacroNode):
        return _macro_arg_text(node)
    if isinstance(node, LatexMathNode):
        return "".join(_plain(n) for n in node.nodelist)
    return ""


@dataclass
class _Block:
    type: str
    title: Optional[str]
    label: Optional[str]
    start: int
    end: int
    text: str
    level: Optional[int] = None
    kind: Optional[str] = None
    children: list = field(default_factory=list)
    cites: list = field(default_factory=list)
    refs: list = field(default_factory=list)


class _Extractor:
    def __init__(self, body: str, slug: str):
        self.body = body
        self.slug = slug
        self.counter: dict[str, int] = {}

    def _id(self, kind: str) -> str:
        self.counter[kind] = self.counter.get(kind, 0) + 1
        return f"{kind}.{self.counter[kind]}"

    # ---- pass 1: flat block stream from a node list (index-based for lookahead) ----
    def parse(self, nodelist) -> list:
        nodes = [n for n in (nodelist or []) if n is not None
                 and not isinstance(n, LatexCommentNode)]
        blocks: list = []
        buf_start = buf_end = None
        buf_cites: list = []
        buf_refs: list = []

        def flush():
            nonlocal buf_start, buf_end, buf_cites, buf_refs
            if buf_start is not None:
                txt = self.body[buf_start:buf_end].strip()
                if txt:
                    b = _Block("paragraph", None, None, buf_start, buf_end, txt)
                    b.cites, b.refs = buf_cites, buf_refs
                    blocks.append(b)
            buf_start = buf_end = None
            buf_cites, buf_refs = [], []

        i, n = 0, len(nodes)
        while i < n:
            node = nodes[i]
            # custom metadata macro: consume following consecutive group args
            if isinstance(node, LatexMacroNode) and node.macroname in META_MACROS:
                flush()
                fields = META_MACROS[node.macroname]
                args, j = [], i + 1
                while j < n and len(args) < len(fields):
                    nx = nodes[j]
                    if isinstance(nx, LatexCharsNode) and not nx.chars.strip():
                        j += 1; continue
                    if isinstance(nx, LatexGroupNode):
                        args.append("".join(_plain(x) for x in nx.nodelist).strip()); j += 1
                    else:
                        break
                start, end = node.pos, (nodes[j - 1].pos + nodes[j - 1].len) if j > i + 1 else node.pos + node.len
                b = _Block("metadata_field", node.macroname, None, start, end, "")
                # children share no real per-arg offsets -> span=-1 (excluded from coverage)
                b.children = [
                    _Block("metadata_field", fields[k], None, -1, -1, v)
                    for k, v in enumerate(args)
                ]
                blocks.append(b); i = j; continue
            # sectioning
            if isinstance(node, LatexMacroNode) and node.macroname in SECTION_LEVEL:
                flush()
                blocks.append(_Block("section", _sanitize_title(_macro_arg_text(node)),
                                     None, node.pos, node.pos + node.len, "",
                                     level=SECTION_LEVEL[node.macroname]))
                i += 1; continue
            # \label attaches to most recent block
            if isinstance(node, LatexMacroNode) and node.macroname == "label":
                lbl = _macro_arg_text(node)
                if _is_real_label(lbl) and blocks:
                    blocks[-1].label = lbl
                i += 1; continue
            # citations / refs within prose
            if isinstance(node, LatexMacroNode) and node.macroname in CITE_MACROS:
                keys = [k for k in _macro_arg_text(node).replace(" ", "").split(",") if k]
                if buf_start is None:
                    buf_start = node.pos
                buf_end = node.pos + node.len
                buf_cites.extend(keys)
                i += 1; continue
            if isinstance(node, LatexMacroNode) and node.macroname in REF_MACROS:
                tgt = _macro_arg_text(node)
                if buf_start is None:
                    buf_start = node.pos
                buf_end = node.pos + node.len
                if tgt:
                    buf_refs.append(tgt)
                i += 1; continue
            # display vs inline math
            if isinstance(node, LatexMathNode):
                if node.displaytype == "display":
                    flush()
                    blocks.append(_Block("equation", None, None, node.pos,
                                         node.pos + node.len,
                                         _node_text(self.body, node).strip()))
                else:
                    if buf_start is None:
                        buf_start = node.pos
                    buf_end = node.pos + node.len
                i += 1; continue
            # environments
            if isinstance(node, LatexEnvironmentNode):
                flush()
                blocks.append(self._env_block(node))
                i += 1; continue
            # plain chars / groups / specials / other macros -> prose buffer
            if isinstance(node, LatexCharsNode) and not node.chars.strip() and buf_start is None:
                i += 1; continue
            if buf_start is None:
                buf_start = node.pos
            buf_end = node.pos + node.len
            i += 1
        flush()
        return blocks

    def _list_items(self, node: LatexEnvironmentNode) -> list:
        """Split an itemize/enumerate body into list_item blocks on \\item."""
        items, cur_start, cur_nodes = [], None, []
        nodes = [x for x in (node.nodelist or []) if x is not None]

        def close(end_pos):
            if cur_start is None:
                return
            sub = self.parse(cur_nodes)
            txt = "" if any(s.children for s in sub) else \
                self.body[cur_start:end_pos].strip()
            it = _Block("list_item", None, None, cur_start, end_pos, txt)
            it.children = self.build_tree(sub) if len(sub) > 1 or (sub and sub[0].children) else \
                ([] if len(sub) <= 1 else sub)
            if len(sub) == 1 and not sub[0].children:
                it.text = sub[0].text; it.children = []
            items.append(it)

        for x in nodes:
            if isinstance(x, LatexMacroNode) and x.macroname == "item":
                if cur_start is not None:
                    close(x.pos)
                cur_start, cur_nodes = x.pos + x.len, []
            elif cur_start is not None:
                cur_nodes.append(x)
        if cur_start is not None:
            close(node.pos + node.len - len("\\end{%s}" % node.environmentname))
        return items

    def _env_block(self, node: LatexEnvironmentNode) -> _Block:
        env = node.environmentname
        ntype, is_container = ENV_TYPE.get(env, ("block", False))
        start, end = node.pos, node.pos + node.len
        title = _sanitize_title(_macro_arg_text(node)) or None
        b = _Block(ntype, title, None, start, end,
                   _node_text(self.body, node).strip(),
                   kind=env if ntype in ("theorem", "block") else None)
        if ntype == "section" and b.level is None:
            b.level = 1  # e.g. abstract -> top-level section
        for inner in node.nodelist or []:
            if isinstance(inner, LatexMacroNode) and inner.macroname == "label":
                lbl = _macro_arg_text(inner)
                if _is_real_label(lbl):
                    b.label = lbl
                break
        if ntype == "list":
            b.children = self._list_items(node)
            b.text = ""
        elif is_container:
            b.children = self.build_tree(self.parse(node.nodelist or []))
            b.text = ""
        return b

    # ---- pass 2: flat stream -> section tree ----
    def build_tree(self, blocks: list) -> list:
        root_children: list = []
        stack: list[tuple[int, _Block]] = []  # (level, section-block)

        def attach(b: _Block):
            if stack:
                stack[-1][1].children.append(b)
            else:
                root_children.append(b)

        for b in blocks:
            if b.type == "section":
                while stack and stack[-1][0] >= b.level:
                    stack.pop()
                attach(b)
                stack.append((b.level, b))
            else:
                attach(b)
        return root_children

    # ---- pass 3: _Block tree -> schema Nodes + edges ----
    def to_nodes(self, blocks: list, parent_id: str, depth: int,
                 edges: list, labels: dict) -> list:
        out: list[Node] = []
        for order, b in enumerate(blocks):
            nid = f"{parent_id}/{self._id(b.type)}"
            attrs: dict = {}
            if b.kind:
                attrs["kind"] = b.kind
            if b.type == "theorem" and b.kind in THEOREM_KINDS:
                attrs["kind"] = b.kind
            span = {"start": b.start, "end": b.end} if b.start >= 0 and b.end > b.start else None
            node = Node(
                id=nid, type=b.type, role=role_for(b.type),
                label=b.label, title=_sanitize_title(b.title),
                text=(b.text or None) if not b.children else None,
                depth=depth, order=order, span=span,
                content_sha256=content_hash(b.text) if b.text else None,
                attrs=attrs,
            )
            if b.label:
                labels[b.label] = nid
            child_nodes = self.to_nodes(b.children, nid, depth + 1, edges, labels) if b.children else []
            node.children = child_nodes
            for key in b.cites:
                edges.append(Edge(id=self._id("edge"), source=nid, target=f"bib:{key}",
                                  relation="cites", resolved=False,
                                  attrs={"key": key}))
            for tgt in b.refs:
                edges.append(Edge(id=self._id("edge"), source=nid, target=tgt,
                                  relation="refers_to", resolved=False,
                                  attrs={"raw_target": tgt}))
            out.append(node)
        return out


_BIBITEM_RE = re.compile(r"\\bibitem(?:\[[^\]]*\])?\s*\{([^}]+)\}")


def extract_bibliography(bbl_or_tex: str) -> list[tuple[str, str]]:
    """Return (key, raw_entry_text) for each \\bibitem in a .bbl / .tex string."""
    entries = []
    matches = list(_BIBITEM_RE.finditer(bbl_or_tex))
    for i, m in enumerate(matches):
        key = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(bbl_or_tex)
        raw = bbl_or_tex[start:end]
        raw = re.sub(r"\\end\{thebibliography\}.*", "", raw, flags=re.S)
        raw = re.sub(r"\s+", " ", raw).strip()
        entries.append((key, raw))
    return entries


def extract(normalized_body: str, slug: str, root_id: str,
            bbl_text: Optional[str] = None) -> tuple[Node, list[Edge]]:
    """Steps 3+4: normalized body -> (root Node, edges). Resolves internal refs."""
    ex = _Extractor(normalized_body, slug)
    w = LatexWalker(normalized_body)
    nodelist, _, _ = w.get_latex_nodes()
    flat = ex.parse(nodelist)
    tree = ex.build_tree(flat)

    edges: list[Edge] = []
    labels: dict[str, str] = {}
    children = ex.to_nodes(tree, root_id, 1, edges, labels)

    root = Node(id=root_id, type="document", role=role_for("document"),
                title=slug, depth=0, order=0, children=children,
                attrs={"adapter": "latex"})

    # bibliography nodes + contains edges
    if bbl_text:
        bib_children = []
        for order, (key, raw) in enumerate(extract_bibliography(bbl_text)):
            bid = f"{root_id}/bib.{order + 1}"
            labels[f"bib:{key}"] = bid
            bib_children.append(Node(
                id=bid, type="bib_reference", role=role_for("bib_reference"),
                label=key, text=raw, depth=2, order=order,
                content_sha256=content_hash(raw), attrs={"bibkey": key}))
        if bib_children:
            bibsec = Node(id=f"{root_id}/references", type="section",
                          role=role_for("section"), title="References", depth=1,
                          order=len(children), children=bib_children,
                          attrs={"auto": True})
            root.children.append(bibsec)

    # resolve cross-ref / citation edges against labels
    node_ids = {n.id for n in [root, *root.iter_descendants()]}
    for e in edges:
        if e.relation == "cites":
            tgt = labels.get(e.target)
            if tgt:
                e.target, e.resolved = tgt, True
            else:
                e.attrs["external"] = True
        elif e.relation == "refers_to":
            tgt = labels.get(e.target)
            if tgt and tgt in node_ids:
                e.target, e.resolved = tgt, True
            else:
                e.attrs["external"] = True
    return root, edges

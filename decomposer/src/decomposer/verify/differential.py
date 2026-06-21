"""Differential oracle: compare the pylatexenc skeleton against ar5iv (LaTeXML) HTML.

Independent because the two extractions share no code: ours walks LaTeX source with
pylatexenc; this reads the *rendered* HTML that LaTeXML produced. Agreement on the
section skeleton is strong evidence neither has a structural bug.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher


_SEC_XPATH = ("//*[contains(@class,'ltx_title_section') or "
              "contains(@class,'ltx_title_subsection') or "
              "contains(@class,'ltx_title_subsubsection') or "
              "contains(@class,'ltx_title_appendix')]")
_THM_XPATH = "//*[contains(@class,'ltx_title_theorem')]"


def _visible_title(h) -> str:
    """Text of a heading minus the ``ltx_tag`` numbering, *without* mutating the tree.

    ar5iv shape is ``<h3><span class="ltx_tag">2.1 </span>Title</h3>`` where the title
    is the span's *tail*; removing the span would drop the tail too, so instead we skip
    only the tag span's own text while keeping every tail.
    """
    parts = [h.text or ""]
    for child in h:
        cls = child.get("class") or ""
        if "ltx_tag" not in cls:
            parts.append("".join(child.itertext()))
        parts.append(child.tail or "")
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def _titles_for(tree, xpath: str) -> list[str]:
    out = []
    for h in tree.xpath(xpath):
        txt = _visible_title(h)
        if txt and not txt.lower().startswith("report issue"):
            out.append(txt)
    return out


def html_section_titles(html: str) -> list[str]:
    """Section heading texts from ar5iv/LaTeXML HTML, via the ``ltx_title_*`` classes."""
    try:
        from lxml import html as lhtml
    except Exception:  # pragma: no cover
        return []
    return _titles_for(lhtml.fromstring(html), _SEC_XPATH)


def html_theorem_count(html: str) -> int:
    try:
        from lxml import html as lhtml
    except Exception:  # pragma: no cover
        return 0
    return len(_titles_for(lhtml.fromstring(html), _THM_XPATH))


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def compare_sections(our_titles: list[str], html_titles: list[str]) -> dict:
    ours = [_norm(t) for t in our_titles if t]
    theirs = [_norm(t) for t in html_titles if t]
    matched = 0
    for t in ours:
        if any(SequenceMatcher(None, t, h).ratio() > 0.8 for h in theirs):
            matched += 1
    recall = matched / len(ours) if ours else 0.0
    return {
        "n_our_sections": len(ours),
        "n_html_sections": len(theirs),
        "matched": matched,
        "title_recall": round(recall, 3),
    }

"""Build the self-contained interactive demo: inject the live data model into the template.

`demo/template.html` contains the UI with a single `__DATA__` placeholder; this replaces it
with the JSON model computed by `demo/model.build_model` (from the real system output) and
writes `docs/index.html`. Regenerate any time the pipeline output changes:

    decomposer/.venv/bin/python demo/build_demo.py
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def build() -> Path:
    import sys
    sys.path.insert(0, str(HERE))
    from model import build_model                       # demo/ is on sys.path

    template = (HERE / "template.html").read_text(encoding="utf-8")
    if template.count("__DATA__") != 1:
        raise SystemExit(f"template must contain exactly one __DATA__ token, "
                         f"found {template.count('__DATA__')}")
    data = build_model()
    # embed as JSON; </script> can't appear inside a script, so escape defensively
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = template.replace("__DATA__", payload)

    # the dashboard must be fully self-contained — no external network dependency other than
    # the w3.org SVG/XML namespaces and the plain GitHub repo link. Fail the build otherwise.
    import re
    urls = set(re.findall(r"https?://[^\s\"'()<>]+", html))
    external = {u for u in urls if "w3.org" not in u and "github.com/yulinl2" not in u}
    if external:
        raise SystemExit(f"dashboard has external dependencies (must be self-contained): "
                         f"{sorted(external)}")

    out = REPO / "docs" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({len(html):,} bytes)")
    print(f"  literatures={data['counts']['literatures']} results={data['counts']['results']} "
          f"analogies={data['counts']['analogies']} conjectures={data['counts']['conjectures']}")
    return out


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(HERE))
    build()

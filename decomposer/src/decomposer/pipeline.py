"""Pipeline orchestrator: runs the staged workflow and writes uniform artifacts.

For each corpus document it executes the four task steps, each emitting a uniform
``step.json`` (id, principle, tool, metrics, verification) plus its build output, and
appends to a ``trajectory.jsonl`` development log. Independent verification
(``verify/``) runs at the end and its report gates the run.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import verify
from .adapters import latex as latex_adapter
from .adapters import markdown as md_adapter
from .schema import Decomposition, SourceProvenance
from .serialize import canonical_json, write_bundle
from .verify import differential


def _sha256(p: Path) -> str:
    return "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def _now() -> str:
    """Timestamp for provenance. Honors SOURCE_DATE_EPOCH so committed artifacts are
    reproducible (no wall-clock churn on regeneration); falls back to current time for
    live runs."""
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    dt = (datetime.fromtimestamp(int(epoch), tz=timezone.utc)
          if epoch else datetime.now(timezone.utc))
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _tool_versions() -> dict:
    import pydantic
    import pylatexenc
    return {
        "python": platform.python_version(),
        "pydantic": pydantic.VERSION,
        "pylatexenc": getattr(pylatexenc, "__version__", "2.10"),
    }


def _principles_for(adapter: str) -> list[dict]:
    """The up-front PEP record: principle -> conserved/target -> verifier."""
    common = [
        {"principle": "P1", "question": "what must be conserved?",
         "conserved": "source characters of the normalized body",
         "target": "every content char attributed to exactly one leaf; overlap=0",
         "verifier": "check_character_coverage"},
        {"principle": "P2", "question": "what is redundant?",
         "conserved": "content up to a declared presentation equivalence",
         "target": "redundancy removed and logged; normalization idempotent",
         "verifier": "check_idempotent + removal_log"},
        {"principle": "P3", "question": "which data classes recur?",
         "conserved": "the role-based class inventory",
         "target": "classified_ratio high; residual 'block' itemized",
         "verifier": "check_schema_valid + classified_ratio"},
        {"principle": "P4", "question": "what is the hierarchy & reference structure?",
         "conserved": "containment tree + cross-reference graph",
         "target": "single-rooted acyclic tree; dangling refs = 0",
         "verifier": "check_acyclic_tree + check_unique_ids + check_reference_integrity"},
    ]
    if adapter in ("latex", "html"):
        common.append({"principle": "P5", "question": "task-specific (exam/paper)",
                       "conserved": "statement/answer-key separability; bib identity",
                       "target": "answer_key & problem_statement distinct subtrees; one "
                                 "bib_reference per bibliography entry (\\bibitem / ltx_bibitem)",
                       "verifier": "type_counts inspection + differential HTML oracle"})
    else:
        common.append({"principle": "P5", "question": "task-specific (prose/form)",
                       "conserved": "form-field identity; source/target analog pairing",
                       "target": "metadata_field per Key:value; example holds source_analog+target_analog",
                       "verifier": "type_counts inspection"})
    return common


def _write_step(run_dir: Path, step: dict, traj: list) -> None:
    sub = run_dir / step["dir"]
    sub.mkdir(parents=True, exist_ok=True)
    (sub / "step.json").write_text(canonical_json(step) + "\n", encoding="utf-8")
    traj.append({k: step[k] for k in ("id", "name", "principle", "tool", "metrics", "status")})


def run_document(cfg: dict, corpus_root: Path, runs_root: Path) -> Decomposition:
    slug = cfg["slug"]
    run_dir = runs_root / slug
    run_dir.mkdir(parents=True, exist_ok=True)
    traj: list = []
    tools = _tool_versions()

    # ---------- Step 00: EXTRACT PRINCIPLES (PEP) ---------- (up-front analysis)
    pep = _principles_for(cfg["adapter"])
    pdir = run_dir / "step-00-principles"
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "principles.json").write_text(canonical_json(pep) + "\n", encoding="utf-8")
    _write_step(run_dir, {
        "id": "00", "name": "extract_principles", "dir": "step-00-principles",
        "principle": "meta", "tool": "Principle-Extraction Protocol (PEP)", "status": "ok",
        "metrics": {"n_principles": len(pep), "adapter": cfg["adapter"]},
    }, traj)

    # ---------- Step 10: INGEST ---------- (acquisition + provenance) P1
    src_files = [corpus_root / slug / f for f in cfg["source_files"]]
    prov = SourceProvenance(
        slug=slug, origin=cfg["origin"], formats=cfg["formats"], retrieved_at=_now(),
        source_files=[str(p.relative_to(corpus_root)) for p in src_files],
        source_sha256={p.name: _sha256(p) for p in src_files if p.exists()},
        tool_versions=tools, external_ids=cfg.get("external_ids", {}),
    )
    _write_step(run_dir, {
        "id": "10", "name": "ingest", "dir": "step-10-ingest", "principle": "P1",
        "tool": "curl/arxiv e-print + local corpus", "status": "ok",
        "metrics": {"n_source_files": len(src_files),
                    "bytes": sum(p.stat().st_size for p in src_files if p.exists())},
    }, traj)

    # ---------- Step 20: NORMALIZE (de-redundancy) ---------- P2
    adapter_name = cfg["adapter"]
    main_path = (corpus_root / slug / cfg["main"]).resolve()
    if adapter_name == "latex":
        norm, raw = latex_adapter.normalize(main_path)
        normalize_text = lambda t: latex_adapter.normalize_text(t, norm.macros).text
    elif adapter_name == "html":
        from .adapters import html as html_adapter
        norm, raw = html_adapter.normalize(main_path)
        normalize_text = lambda t: html_adapter.normalize_text(t)
    else:
        norm, raw = md_adapter.normalize(main_path)
        normalize_text = lambda t: md_adapter.normalize_text(t).text

    norm_dir = run_dir / "step-20-normalize"
    norm_dir.mkdir(parents=True, exist_ok=True)
    (norm_dir / "normalized.txt").write_text(norm.text, encoding="utf-8")
    (norm_dir / "removal_log.json").write_text(canonical_json(norm.removal_log) + "\n", encoding="utf-8")
    idem = verify.check_idempotent(normalize_text, norm.text)
    removed = sum(e.get("chars", 0) for e in norm.removal_log if "chars" in e)
    _write_step(run_dir, {
        "id": "20", "name": "normalize", "dir": "step-20-normalize", "principle": "P2",
        "tool": f"{adapter_name} adapter (pure-Python, deterministic)",
        "status": "ok" if idem.passed else "warn",
        "metrics": {"raw_chars": len(raw), "normalized_chars": len(norm.text),
                    "redundancy_removed_chars": removed,
                    "n_macros": len(norm.macros), "idempotent": idem.passed},
    }, traj)

    # ---------- Steps 30+40: CLASSIFY data classes + HIERARCHICAL split ---------- P3/P4
    if adapter_name == "latex":
        bbl_text = None
        if cfg.get("bbl"):
            bp = corpus_root / slug / cfg["bbl"]
            bbl_text = bp.read_text(encoding="utf-8") if bp.exists() else None
        root, edges = latex_adapter.extract(norm.text, slug, slug, bbl_text=bbl_text)
    elif adapter_name == "html":
        from .adapters import html as html_adapter
        root, edges = html_adapter.extract(raw, norm.text, slug, slug)
    else:
        root, edges = md_adapter.extract(norm.text, slug, slug)

    from collections import Counter
    all_nodes = [root, *root.iter_descendants()]
    type_counts = dict(Counter(n.type for n in all_nodes))
    role_counts = dict(Counter(n.role.value for n in all_nodes))
    n_block = type_counts.get("block", 0)
    classified_ratio = 1 - n_block / max(1, len(all_nodes) - 1)

    decomp = Decomposition(provenance=prov, document=root, edges=edges)
    decomp.metrics = {
        "n_nodes": len(all_nodes), "type_counts": type_counts,
        "role_counts": role_counts, "n_edges": len(edges),
        "n_edges_resolved": sum(e.resolved for e in edges),
        "classified_ratio": round(classified_ratio, 4),
        "max_depth": max((n.depth for n in all_nodes), default=0),
    }
    paths = write_bundle(decomp, run_dir / "step-30-structure")
    _write_step(run_dir, {
        "id": "30-40", "name": "classify_and_split", "dir": "step-30-structure",
        "principle": "P3+P4", "tool": f"{adapter_name} adapter -> Pydantic schema -> canonical JSON/JSONL",
        "status": "ok",
        "metrics": {"n_nodes": len(all_nodes), "type_counts": type_counts,
                    "classified_ratio": round(classified_ratio, 4),
                    "n_edges": len(edges), "outputs": list(paths)},
    }, traj)

    # ---------- VERIFICATION (独立检验) ----------
    results = verify.run_all(decomp, normalized_len=len(norm.text),
                             min_coverage=cfg.get("min_coverage", 0.70),
                             normalize=normalize_text, raw=norm.text)
    report = {"checks": [r.model_dump() for r in results],
              "all_passed": all(r.passed for r in results)}
    # differential oracle for arxiv (pylatexenc vs ar5iv HTML)
    if cfg.get("html"):
        hp = corpus_root / slug / cfg["html"]
        if hp.exists():
            html = hp.read_text(encoding="utf-8")
            our_titles = [n.title for n in all_nodes if n.type == "section" and n.title]
            diff = differential.compare_sections(
                our_titles, differential.html_section_titles(html))
            our_thm = sum(1 for n in all_nodes if n.type in ("theorem", "definition", "remark"))
            diff["our_theorem_like"] = our_thm
            diff["html_theorem_like"] = differential.html_theorem_count(html)
            report["differential_html"] = diff
    vdir = run_dir / "verification"
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / "report.json").write_text(canonical_json(report) + "\n", encoding="utf-8")
    decomp.metrics["verification"] = {"all_passed": report["all_passed"],
                                      "checks": {r.name: r.passed for r in results}}
    # rewrite bundle so metrics include verification summary
    write_bundle(decomp, run_dir / "step-30-structure")

    traj.append({"id": "verify", "name": "independent_verification", "principle": "P1-P4",
                 "tool": "verify/ invariants + differential oracle",
                 "status": "ok" if report["all_passed"] else "fail",
                 "metrics": {r.name: r.passed for r in results}})

    # ---------- run-level metadata + trajectory ----------
    (run_dir / "meta.json").write_text(canonical_json({
        "slug": slug, "adapter": adapter_name, "generated_at": _now(),
        "tool_versions": tools, "provenance": prov.model_dump(exclude_none=True),
        "metrics": decomp.metrics,
    }) + "\n", encoding="utf-8")
    with (run_dir / "trajectory.jsonl").open("w", encoding="utf-8") as fh:
        for rec in traj:
            fh.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    return decomp


def load_manifest(corpus_root: Path) -> list[dict]:
    return json.loads((corpus_root / "manifest.json").read_text(encoding="utf-8"))


def run_all_docs(corpus_root: Path, runs_root: Path) -> dict:
    summary = {}
    for cfg in load_manifest(corpus_root):
        decomp = run_document(cfg, corpus_root, runs_root)
        summary[cfg["slug"]] = decomp.metrics
    (runs_root / "summary.json").write_text(canonical_json(summary) + "\n", encoding="utf-8")
    return summary

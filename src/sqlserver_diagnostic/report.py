from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import __version__
from .findings import Finding, Severity, SEVERITY_ORDER


TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

CATEGORY_ORDER = ["performance", "bottlenecks", "health", "capacity"]


def _verdict(by_sev):
    c, w = by_sev.get("critical", 0), by_sev.get("warning", 0)
    if c >= 3:
        return {"headline": "Action required",
                "summary": f"{c} critical issues need attention."}
    if c:
        return {"headline": "Needs attention",
                "summary": f"{c} critical, {w} warnings to review."}
    if w >= 10:
        return {"headline": "Minor issues accumulated",
                "summary": f"{w} warnings. Triage in the next maintenance window."}
    return {"headline": "Healthy",
            "summary": "Informational findings only."}


def summarise(findings: list[Finding], server_info: dict[str, Any],
              errors: list[dict[str, str]] | None = None) -> dict[str, Any]:
    findings = sorted(findings, key=lambda f: (SEVERITY_ORDER[f.severity], f.category, f.id))

    by_sev = Counter(f.severity.value for f in findings)
    by_cat = Counter(f.category for f in findings)

    grouped_sev: dict[str, list[dict[str, Any]]] = {"critical": [], "warning": [], "info": []}
    for f in findings:
        grouped_sev[f.severity.value].append(f.to_dict())

    cat_breakdown: dict[str, dict[str, int]] = {}
    matrix: dict[tuple[str, str], int] = defaultdict(int)
    for f in findings:
        matrix[(f.category, f.severity.value)] += 1
    for cat in CATEGORY_ORDER:
        if by_cat.get(cat, 0) == 0:
            continue
        cat_breakdown[cat] = {
            "critical": matrix[(cat, "critical")],
            "warning": matrix[(cat, "warning")],
            "info": matrix[(cat, "info")],
            "total": by_cat.get(cat, 0),
        }

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "tool_version": __version__,
        "server_info": server_info,
        "totals": {
            "finding_count": len(findings),
            "by_severity": dict(by_sev),
            "by_category": dict(by_cat),
        },
        "verdict": _verdict(dict(by_sev)),
        "by_severity": grouped_sev,
        "category_breakdown": cat_breakdown,
        "findings": [f.to_dict() for f in findings],
        "errors": errors or [],
    }


def write_json(summary: dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")


def _is_sql(rec: str) -> bool:
    up = rec.lstrip().upper()
    return any(up.startswith(k) for k in ("CREATE", "ALTER", "DROP", "BACKUP", "USE ", "SELECT", "INSERT", "UPDATE", "DELETE"))


def write_markdown(summary, path):
    si = summary["server_info"]
    t = summary["totals"]
    crit = summary["by_severity"]["critical"]
    warn = summary["by_severity"]["warning"]
    info = summary["by_severity"]["info"]

    buf = [
        f"# {si['database_name']} — diagnostic report",
        "",
        f"`{si['server_name']}` · {si['sql_version']} · scanned {summary['generated_at']}",
        "",
        f"**{summary['verdict']['headline']}.** "
        f"{t['by_severity'].get('critical', 0)} critical, "
        f"{t['by_severity'].get('warning', 0)} warning, "
        f"{t['by_severity'].get('info', 0)} info.",
        "",
    ]

    if crit:
        buf.append(f"## Critical ({len(crit)})")
        buf.append("")
        for f in crit:
            buf.append(f"### {f['title']}")
            buf.append("")
            buf.append(f["description"])
            if f.get("recommendation"):
                fence = "```sql" if _is_sql(f["recommendation"]) else "```"
                buf += ["", fence, f["recommendation"], "```"]
            buf.append("")

    if warn:
        buf += [f"## Warnings ({len(warn)})", "",
                "| Finding | ID |",
                "| --- | --- |"]
        for f in warn:
            buf.append(f"| {f['title']} | `{f['id']}` |")
        buf.append("")

    if info:
        buf += [f"## Info ({len(info)})", "",
                "| Finding | ID |",
                "| --- | --- |"]
        for f in info:
            buf.append(f"| {f['title']} | `{f['id']}` |")
        buf.append("")

    if summary.get("errors"):
        buf += ["## Probes that failed", ""]
        for e in summary["errors"]:
            buf.append(f"- `{e['probe']}` — {e['error']}")
        buf.append("")

    path.write_text("\n".join(buf), encoding="utf-8")


def write_html(summary: dict[str, Any], path: Path) -> None:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    tpl = env.get_template("report.html.j2")
    path.write_text(tpl.render(**summary), encoding="utf-8")


def write_all(summary: dict[str, Any], output_prefix: Path) -> dict[str, Path]:
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": output_prefix.with_suffix(".json"),
        "md":   output_prefix.with_suffix(".md"),
        "html": output_prefix.with_suffix(".html"),
    }
    write_json(summary,     paths["json"])
    write_markdown(summary, paths["md"])
    write_html(summary,     paths["html"])
    return paths

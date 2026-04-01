from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Protocol


SQL_DIR = Path(__file__).resolve().parent / "sql"


PROBES_BY_CATEGORY: dict[str, list[str]] = {
    "performance": [
        "top_slow_queries",
        "plan_warnings",
        "missing_indexes",
        "unused_indexes",
        "index_fragmentation",
    ],
    "bottlenecks": [
        "wait_stats",
        "current_blocking",
        "tempdb_contention",
    ],
    "health": [
        "database_sizes",
        "backup_status",
        "vlf_counts",
    ],
    "capacity": [
        "sessions",
        "memory_pressure",
    ],
}


class _Queryable(Protocol):
    def query(self, sql: str) -> list[dict[str, Any]]: ...


def _load(name: str) -> str:
    return (SQL_DIR / f"{name}.sql").read_text(encoding="utf-8")


def probes_for(categories: Iterable[str] | None) -> list[tuple[str, str]]:
    """Return (category, probe_name) pairs for the requested categories."""
    cats = list(categories) if categories else list(PROBES_BY_CATEGORY)
    out: list[tuple[str, str]] = []
    for cat in cats:
        for probe in PROBES_BY_CATEGORY.get(cat, []):
            out.append((cat, probe))
    return out


def scan(conn: _Queryable, categories: Iterable[str] | None = None) -> dict[str, Any]:
    """Run every requested probe. On failure, probe result is [] and the error
    is appended to `_errors`. Does not abort the whole scan on a single failure,
    since some DMVs require permissions or editions the user may not have."""
    results: dict[str, Any] = {}
    errors: list[dict[str, str]] = []

    for _, name in probes_for(categories):
        try:
            results[name] = conn.query(_load(name))
        except Exception as e:
            results[name] = []
            errors.append({"probe": name, "error": str(e)})

    results["_errors"] = errors
    return results

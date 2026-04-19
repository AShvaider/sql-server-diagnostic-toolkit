from __future__ import annotations

from typing import Any

from . import severity as S
from .findings import Finding, Severity


# Explanations for the most common wait types. Not exhaustive; falls back to
# generic text for anything not listed. Add entries as you run into new ones.
WAIT_EXPLAIN = {
    "PAGEIOLATCH_SH":      ("Data page read from disk.", "IO pressure. Check storage latency and buffer pool."),
    "PAGEIOLATCH_EX":      ("Data page read for modification.", "IO pressure under writes."),
    "PAGELATCH_EX":        ("In-memory page contention, typically tempdb allocation.", "Bump tempdb file count."),
    "CXPACKET":            ("Parallelism coordination.", "Usually benign. Check MAXDOP only if dominant."),
    "CXCONSUMER":          ("Parallelism consumer wait.", "Not actionable on its own."),
    "LCK_M_X":             ("Exclusive lock wait.", "Look at current blocking and long transactions."),
    "LCK_M_U":             ("Update lock wait during UPDATE/DELETE scan.", "Usually fixed by a better index."),
    "LCK_M_S":             ("Shared lock wait. Readers blocked by writers.", "Consider RCSI."),
    "WRITELOG":            ("Log writer flush wait.", "Log IO latency. Faster log storage or smaller txns."),
    "ASYNC_NETWORK_IO":    ("Client slow to consume results.", "Almost always client-side."),
    "SOS_SCHEDULER_YIELD": ("CPU pressure.", "Top CPU consumers; parallelism."),
    "RESOURCE_SEMAPHORE":  ("Memory grant queue.", "Critical when sustained."),
    "THREADPOOL":          ("Out of worker threads.", "Check blocking chains."),
}


def _missing_indexes(rows):
    findings = []
    for r in rows:
        im = r["improvement_measure"]
        table = f"{r['schema_name']}.{r['table_name']}"
        cols = r.get("equality_columns") or r.get("inequality_columns") or ""
        key = cols.split(",")[0].strip() if cols else "scan"

        if im >= S.MISSING_INDEX_CRITICAL:
            sev = Severity.CRITICAL
        elif im >= S.MISSING_INDEX_WARNING:
            sev = Severity.WARNING
        else:
            sev = Severity.INFO

        findings.append(Finding(
            id=f"perf.missing_idx.{r['table_name']}.{key}",
            category="performance",
            severity=sev,
            title=f"Missing index on {table} ({cols or 'no key'})",
            description=(
                f"Improvement measure {im:,.0f}, avg impact {r['avg_user_impact']:.0f}%, "
                f"{r['user_seeks']:,} seeks."
            ),
            recommendation=r["create_index_statement"],
            details={
                "improvement_measure": int(im),
                "avg_user_impact_pct": round(r["avg_user_impact"], 1),
                "user_seeks": r["user_seeks"],
                "user_scans": r.get("user_scans", 0),
                "equality_columns": r.get("equality_columns") or "",
                "inequality_columns": r.get("inequality_columns") or "",
                "included_columns": r.get("included_columns") or "",
            },
        ))
    return findings


def _unused_indexes(rows):
    return [
        Finding(
            id=f"perf.unused_idx.{r['index_name']}",
            category="performance",
            severity=Severity.WARNING,
            title=f"Unused index: {r['index_name']}",
            description=(
                f"{r['schema_name']}.{r['table_name']}: 0 reads, "
                f"{r['user_updates']:,} writes, {r['size_mb']} MB."
            ),
            recommendation=r["drop_statement"],
            details={
                "table": f"{r['schema_name']}.{r['table_name']}",
                "size_mb": r["size_mb"],
                "user_updates": r["user_updates"],
                # kept separately so you can see whether scans were truly zero
                "user_seeks": r["user_seeks"],
                "user_scans": r["user_scans"],
                "user_lookups": r["user_lookups"],
            },
        )
        for r in rows
    ]


def _index_fragmentation(rows):
    findings = []
    skipped = []  # for a single aggregate info entry at the end

    for r in rows:
        pct = r["avg_fragmentation_in_percent"]
        idx = r["index_name"]
        tbl = f"{r['schema_name']}.{r['table_name']}"
        pages = r["page_count"]

        if pct >= S.FRAG_CRITICAL:
            findings.append(Finding(
                id=f"perf.frag.{idx}",
                category="performance",
                severity=Severity.CRITICAL,
                title=f"Heavily fragmented: {idx} on {tbl}",
                description=f"{pct:.1f}% over {pages:,} pages. Rebuild.",
                recommendation=f"ALTER INDEX [{idx}] ON [{r['schema_name']}].[{r['table_name']}] REBUILD;",
                details={
                    "fragmentation_pct": round(pct, 1),
                    "page_count": pages,
                    "index_type": r["index_type_desc"],
                },
            ))
        elif pct >= S.FRAG_WARNING:
            findings.append(Finding(
                id=f"perf.frag.{idx}",
                category="performance",
                severity=Severity.WARNING,
                title=f"Fragmented: {idx} ({pct:.0f}%)",
                description=f"{pct:.1f}% on {tbl} ({pages:,} pages). Reorganize.",
                recommendation=f"ALTER INDEX [{idx}] ON [{r['schema_name']}].[{r['table_name']}] REORGANIZE;",
                details={"fragmentation_pct": round(pct, 1), "page_count": pages},
            ))
        else:
            skipped.append(idx)

    if skipped:
        findings.append(Finding(
            id="perf.frag.summary",
            category="performance",
            severity=Severity.INFO,
            title=f"{len(skipped)} indexes below 10% fragmentation",
            description="No maintenance needed. Sampled in SAMPLED mode.",
            details={"indexes": ", ".join(skipped[:10]) + ("..." if len(skipped) > 10 else "")},
        ))
    return findings


def _top_slow_queries(rows):
    # Always list the top queries; severity is only about how bad the worst are.
    findings = []
    for r in rows:
        avg_ms = r["avg_worker_time_ms"]
        if avg_ms >= S.SLOW_QUERY_CRITICAL_MS:
            sev = Severity.CRITICAL
        elif avg_ms >= S.SLOW_QUERY_WARNING_MS:
            sev = Severity.WARNING
        else:
            sev = Severity.INFO

        text = r["query_text"].strip()
        snippet = text if len(text) <= 140 else text[:137] + "..."

        findings.append(Finding(
            id=f"perf.query.{r['query_hash'][2:10]}",
            category="performance",
            severity=sev,
            title=f"{avg_ms:,} ms avg · {r['execution_count']:,} runs",
            description=snippet,
            recommendation=text if sev != Severity.INFO else "",
            details={
                "query_hash": r["query_hash"],
                "execution_count": r["execution_count"],
                "avg_worker_time_ms": avg_ms,
                "total_worker_time_ms": r["total_worker_time_ms"],
                "avg_logical_reads": r["avg_logical_reads"],
                "last_execution_time": r["last_execution_time"],
            },
        ))
    return findings


# TODO: SpillToTempDB and TableScan aren't always warnings; scan on a small
# lookup table is fine. Revisit when we wire this up against Query Store.
_PLAN_WARNING_SEVERITY = {
    "ImplicitConversion":       Severity.WARNING,
    "NoJoinPredicate":          Severity.WARNING,
    "MissingStatistics":        Severity.WARNING,
    "TableScan":                Severity.WARNING,
    "SpillToTempDB":            Severity.WARNING,
    "ColumnsWithNoStatistics":  Severity.INFO,
}


def _plan_warnings(rows):
    findings = []
    for r in rows:
        wt = r["warning_type"]
        sev = _PLAN_WARNING_SEVERITY.get(wt, Severity.INFO)
        findings.append(Finding(
            id=f"perf.plan.{wt.lower()}.{r['query_hash'][2:8]}",
            category="performance",
            severity=sev,
            title=f"Plan: {wt}",
            description=r["detail"],
            details={
                "query_text": r["query_text"],
                "query_hash": r["query_hash"],
                "column_ref": r.get("column_ref"),
            },
        ))
    return findings


def _wait_stats(rows):
    findings = []
    for r in rows:
        wt = r["wait_type"]
        pct = r["pct_total_wait"]
        blurb, direction = WAIT_EXPLAIN.get(wt, (f"Wait type {wt}.", ""))

        noisy = wt in ("CXCONSUMER", "ASYNC_NETWORK_IO")
        sev = Severity.WARNING if (pct >= 25.0 and not noisy) else Severity.INFO

        findings.append(Finding(
            id=f"bot.wait.{wt.lower()}",
            category="bottlenecks",
            severity=sev,
            title=f"{wt}: {pct:.1f}%",
            description=f"{blurb} {direction}".strip(),
            details={
                "rank": r["rank"],
                "pct_total_wait": pct,
                "wait_time_s": r["wait_time_s"],
                "signal_wait_time_s": r["signal_wait_time_s"],
                "waiting_tasks_count": r["waiting_tasks_count"],
            },
        ))
    return findings


def _current_blocking(rows):
    return [
        Finding(
            id=f"bot.block.{r['blocker_session_id']}_{r['blocked_session_id']}",
            category="bottlenecks",
            severity=Severity.WARNING,
            title=f"Session {r['blocker_session_id']} blocking {r['blocked_session_id']} ({r['wait_time_ms']:,} ms)",
            description=(
                f"{r['wait_type']}. Blocker: {r['blocker_login']}. "
                f"Blocked: {r['blocked_login']}."
            ),
            details={
                "resource": r["resource_description"],
                "blocker_query": r["blocker_query"],
                "blocked_query": r["blocked_query"],
            },
        )
        for r in rows
    ]


def _tempdb_contention(rows):
    if not rows:
        return []
    r = rows[0]
    fc = r["file_count"]
    rec = r["recommended_file_count"]
    imbalance = r["file_count_imbalance_mb"]

    if fc >= rec and imbalance <= 1000 and r["pagelatch_contention_s"] < 60:
        return []  # nothing worth mentioning

    sev = Severity.CRITICAL if fc == 1 else Severity.WARNING
    return [Finding(
        id="bot.tempdb",
        category="bottlenecks",
        severity=sev,
        title=f"tempdb: {fc} data file(s), recommended {rec}",
        description=(
            f"Imbalance {imbalance:,} MB. PAGELATCH contention "
            f"{r['pagelatch_contention_s']:,}s on {r['top_contention_resource']}."
        ),
        recommendation=(
            f"ALTER DATABASE tempdb ADD FILE ... ; -- grow to {rec} equal files"
        ),
        details={
            "file_count": fc,
            "recommended_file_count": rec,
            "imbalance_mb": imbalance,
            "top_contention_resource": r["top_contention_resource"],
        },
    )]


def _database_sizes(rows):
    return [
        Finding(
            id=f"hlt.size.{r['database_name']}",
            category="health",
            severity=Severity.INFO,
            title=f"{r['database_name']}: {r['data_used_mb']:,} MB data, {r['log_used_mb']:,} MB log",
            description=f"Largest table: {r['largest_table']} ({r['largest_table_mb']:,} MB).",
            details={k: r[k] for k in ("data_size_mb", "data_used_mb", "log_size_mb",
                                       "log_used_mb", "largest_table", "largest_table_mb")},
        )
        for r in rows
    ]


def _backup_status(rows):
    findings = []
    for r in rows:
        db = r["database_name"]
        rm = r["recovery_model"]
        hf = r.get("hours_since_full")
        hl = r.get("hours_since_log")

        if hf is None or hf > S.BACKUP_FULL_CRITICAL_H:
            findings.append(Finding(
                id=f"hlt.backup.full.{db}",
                category="health",
                severity=Severity.CRITICAL,
                title=f"No recent full backup: {db}",
                description=f"Last FULL: {hf if hf is not None else 'never'} hours ago.",
                recommendation=f"BACKUP DATABASE [{db}] TO DISK='...' WITH CHECKSUM, COMPRESSION;",
                details={"recovery_model": rm, "hours_since_full": hf},
            ))
        elif hf > S.BACKUP_FULL_WARNING_H:
            findings.append(Finding(
                id=f"hlt.backup.full.{db}",
                category="health",
                severity=Severity.WARNING,
                title=f"Full backup > 24h old: {db}",
                description=f"{hf:.1f} hours since last FULL backup.",
                details={"hours_since_full": hf},
            ))

        if rm != "FULL":
            continue

        if hl is None or hl > S.BACKUP_LOG_CRITICAL_H:
            findings.append(Finding(
                id=f"hlt.backup.log.{db}",
                category="health",
                severity=Severity.CRITICAL,
                title=f"Log backup gap > 24h: {db}",
                description=(
                    f"Recovery model is FULL, last log backup "
                    f"{hl if hl is not None else 'never'} hours ago. Log will grow unbounded."
                ),
                recommendation=f"BACKUP LOG [{db}] TO DISK='...' WITH COMPRESSION;",
                details={"hours_since_log": hl},
            ))
        elif hl > S.BACKUP_LOG_WARNING_H:
            findings.append(Finding(
                id=f"hlt.backup.log.{db}",
                category="health",
                severity=Severity.WARNING,
                title=f"Log backup > 6h old: {db}",
                description=f"{hl:.1f} hours since last LOG backup.",
                details={"hours_since_log": hl},
            ))
    return findings


def _vlf_counts(rows):
    findings = []
    for r in rows:
        n = r["vlf_count"]
        db = r["database_name"]
        if n >= S.VLF_CRITICAL:
            findings.append(Finding(
                id=f"hlt.vlf.{db}",
                category="health",
                severity=Severity.CRITICAL,
                title=f"VLF count {n:,} on {db}",
                description="Startup, log backups, and crash recovery will be slow.",
                recommendation=r["recommendation_statement"],
                details={"vlf_count": n, "log_size_mb": r["log_size_mb"]},
            ))
        elif n >= S.VLF_WARNING:
            findings.append(Finding(
                id=f"hlt.vlf.{db}",
                category="health",
                severity=Severity.WARNING,
                title=f"VLF count elevated: {db} ({n:,})",
                description="Shrink log and regrow in larger increments.",
                recommendation=r["recommendation_statement"],
                details={"vlf_count": n, "log_size_mb": r["log_size_mb"]},
            ))
        # below threshold: skip. no point emitting "VLF healthy" noise.
    return findings


def _sessions(rows):
    # Group-by already done server-side; we just list.
    return [
        Finding(
            id=f"cap.sess.{r['login_name']}.{r['host_name']}",
            category="capacity",
            severity=Severity.INFO,
            title=f"{r['session_count']} × {r['login_name']} from {r['host_name']}",
            description=f"{r['program_name']} · status {r['status']}.",
            details=dict(r),
        )
        for r in rows
    ]


def _memory_pressure(rows):
    findings = []
    for r in rows:
        metric, val = r["metric"], r["value"]

        if metric == "page_life_expectancy":
            if val < S.PLE_CRITICAL:
                sev, title = Severity.CRITICAL, f"PLE critically low: {val}s"
                desc = "Buffer pool is churning. Add memory or reduce IO."
            elif val < S.PLE_WARNING:
                sev, title = Severity.WARNING, f"PLE low: {val}s"
                desc = "Watch for sustained drops under peak load."
            else:
                continue  # healthy PLE is not interesting

        elif metric == "buffer_cache_hit_ratio":
            if val < S.BCHR_CRITICAL:
                sev = Severity.CRITICAL
            elif val < S.BCHR_WARNING:
                sev = Severity.WARNING
            else:
                continue
            title = f"Buffer cache hit ratio {val:.1f}%"
            desc = "Healthy OLTP sits at 95%+. Correlate with PLE and IO waits."

        elif metric == "memory_grants_pending":
            if val <= 0:
                continue
            sev, title = Severity.CRITICAL, f"{val} memory grants pending"
            desc = "Queries queued for workspace memory. Investigate large sorts/hashes."

        else:
            # Unknown metric. Keep as info, don't try to classify.
            sev, title, desc = Severity.INFO, f"{metric}: {val}", ""

        findings.append(Finding(
            id=f"cap.mem.{metric}",
            category="capacity",
            severity=sev,
            title=title,
            description=desc,
            details={"metric": metric, "value": val, "unit": r["unit"]},
        ))
    return findings


HANDLERS = {
    "missing_indexes":      _missing_indexes,
    "unused_indexes":       _unused_indexes,
    "index_fragmentation":  _index_fragmentation,
    "top_slow_queries":     _top_slow_queries,
    "plan_warnings":        _plan_warnings,
    "wait_stats":           _wait_stats,
    "current_blocking":     _current_blocking,
    "tempdb_contention":    _tempdb_contention,
    "database_sizes":       _database_sizes,
    "backup_status":        _backup_status,
    "vlf_counts":           _vlf_counts,
    "sessions":             _sessions,
    "memory_pressure":      _memory_pressure,
}


def classify(scan: dict[str, Any]) -> list[Finding]:
    result = []
    for probe, handler in HANDLERS.items():
        rows = scan.get(probe) or []
        if isinstance(rows, list):
            result.extend(handler(rows))
    return result

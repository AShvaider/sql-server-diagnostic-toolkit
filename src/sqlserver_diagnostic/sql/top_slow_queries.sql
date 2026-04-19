-- Top 25 slowest cached statements by avg CPU time.
-- Caveat: only what's currently in the plan cache. Recently-evicted plans
-- won't show. For a long-running view use Query Store.
SELECT TOP 25
    qs.query_hash                                            AS query_hash,
    qs.execution_count                                       AS execution_count,
    qs.total_worker_time / 1000                              AS total_worker_time_ms,
    (qs.total_worker_time / qs.execution_count) / 1000       AS avg_worker_time_ms,
    qs.total_logical_reads / qs.execution_count              AS avg_logical_reads,
    qs.last_execution_time                                   AS last_execution_time,
    SUBSTRING(
        st.text,
        (qs.statement_start_offset / 2) + 1,
        ((CASE qs.statement_end_offset
              WHEN -1 THEN DATALENGTH(st.text)
              ELSE qs.statement_end_offset
          END - qs.statement_start_offset) / 2) + 1
    )                                                        AS query_text
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
WHERE qs.execution_count > 0
  -- Skip statements averaging under 50ms. Cache is full of trivial DMV
  -- self-queries; anything that actually matters runs longer than this.
  AND (qs.total_worker_time / qs.execution_count) >= 50000
ORDER BY (qs.total_worker_time / qs.execution_count) DESC;

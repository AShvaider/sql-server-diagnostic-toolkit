-- Plan warnings emitted by the optimizer that we can scrape from cached plans.
-- Not every warning is actionable; the classifier decides severity.
WITH plans AS (
    SELECT
        qs.query_hash,
        qp.query_plan,
        SUBSTRING(
            st.text,
            (qs.statement_start_offset / 2) + 1,
            ((CASE qs.statement_end_offset
                  WHEN -1 THEN DATALENGTH(st.text)
                  ELSE qs.statement_end_offset
              END - qs.statement_start_offset) / 2) + 1
        ) AS query_text
    FROM sys.dm_exec_query_stats qs
    CROSS APPLY sys.dm_exec_query_plan(qs.plan_handle) qp
    CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
)
SELECT
    CONVERT(VARCHAR(64), p.query_hash, 1) AS query_hash,
    w.warning_type,
    w.detail,
    p.query_text,
    w.column_ref
FROM plans p
CROSS APPLY (
    -- Inline rule set; replace with shred from query_plan XML in v2.
    SELECT 'ImplicitConversion' AS warning_type,
           'Predicate forces convert; index unusable.' AS detail,
           '<unknown>' AS column_ref
    WHERE p.query_plan.exist('//*:Warnings/*:PlanAffectingConvert') = 1
) w;

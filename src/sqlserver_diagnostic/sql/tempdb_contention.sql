-- tempdb data file count, size imbalance, and recent allocation contention.
-- Recommendation = min(8, num_logical_cpus). Adjust if you've documented otherwise.
DECLARE @cpu int = (SELECT cpu_count FROM sys.dm_os_sys_info);

;WITH files AS (
    SELECT
        COUNT(*)                                  AS file_count,
        MAX(size * 8 / 1024) - MIN(size * 8 / 1024) AS file_count_imbalance_mb
    FROM sys.master_files
    WHERE database_id = DB_ID('tempdb')
      AND type_desc = 'ROWS'
),
contention AS (
    SELECT
        ISNULL(SUM(wait_duration_ms) / 1000.0, 0) AS pagelatch_contention_s,
        MAX(resource_description)             AS top_contention_resource
    FROM sys.dm_os_waiting_tasks
    WHERE wait_type LIKE 'PAGELATCH_%'
      AND resource_description LIKE '2:%'  -- tempdb db_id
)
SELECT
    f.file_count,
    CASE WHEN @cpu < 8 THEN @cpu ELSE 8 END AS recommended_file_count,
    f.file_count_imbalance_mb,
    c.pagelatch_contention_s,
    c.top_contention_resource
FROM files f CROSS JOIN contention c;

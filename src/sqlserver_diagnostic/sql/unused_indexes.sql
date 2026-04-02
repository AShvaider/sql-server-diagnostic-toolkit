-- Indexes with zero reads since last server restart but ongoing write cost.
-- Be careful before dropping: short uptime can mislead.
SELECT
    OBJECT_SCHEMA_NAME(i.object_id) AS schema_name,
    OBJECT_NAME(i.object_id)        AS table_name,
    i.name                          AS index_name,
    s.user_seeks,
    s.user_scans,
    s.user_lookups,
    s.user_updates,
    CAST(SUM(au.total_pages) * 8.0 / 1024 AS INT) AS size_mb,
    'DROP INDEX [' + i.name + '] ON ['
        + OBJECT_SCHEMA_NAME(i.object_id) + '].['
        + OBJECT_NAME(i.object_id) + '];'                AS drop_statement
FROM sys.indexes i
JOIN sys.dm_db_index_usage_stats s
       ON s.object_id = i.object_id AND s.index_id = i.index_id
JOIN sys.partitions p
       ON p.object_id = i.object_id AND p.index_id = i.index_id
JOIN sys.allocation_units au
       ON au.container_id = p.partition_id
WHERE i.is_primary_key = 0
  AND i.is_unique_constraint = 0
  AND i.type_desc = 'NONCLUSTERED'
  AND s.database_id = DB_ID()
  AND (s.user_seeks + s.user_scans + s.user_lookups) = 0
  AND s.user_updates > 100
GROUP BY i.object_id, i.name, s.user_seeks, s.user_scans, s.user_lookups, s.user_updates
ORDER BY s.user_updates DESC;

-- SAMPLED mode: cheap. Use LIMITED for a quick gate or DETAILED before action.
-- Skips small indexes (< 1000 pages) since fragmentation there is noise.
SELECT
    OBJECT_SCHEMA_NAME(ips.object_id)             AS schema_name,
    OBJECT_NAME(ips.object_id)                    AS table_name,
    i.name                                        AS index_name,
    ips.index_type_desc,
    ips.avg_fragmentation_in_percent,
    ips.page_count
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'SAMPLED') ips
JOIN sys.indexes i
       ON i.object_id = ips.object_id AND i.index_id = ips.index_id
WHERE ips.page_count >= 1000
  AND i.name IS NOT NULL
ORDER BY ips.avg_fragmentation_in_percent DESC;

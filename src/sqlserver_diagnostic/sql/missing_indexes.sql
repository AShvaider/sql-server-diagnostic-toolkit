/*
  Missing index suggestions. Treat as hints, not commands.
  improvement_measure is a rough heuristic; combine with workload knowledge.
*/
SELECT
    OBJECT_SCHEMA_NAME(d.object_id, d.database_id) AS schema_name,
    OBJECT_NAME(d.object_id, d.database_id)        AS table_name,
    d.equality_columns,
    d.inequality_columns,
    d.included_columns,
    s.user_seeks,
    s.user_scans,
    s.avg_user_impact,
    CAST(s.avg_user_impact * (s.user_seeks + s.user_scans) AS BIGINT) AS improvement_measure,
    'CREATE NONCLUSTERED INDEX IX_'
        + OBJECT_NAME(d.object_id, d.database_id)
        + '_' + REPLACE(REPLACE(REPLACE(ISNULL(d.equality_columns, d.inequality_columns), ', ', '_'), '[', ''), ']', '')
        + ' ON ' + OBJECT_SCHEMA_NAME(d.object_id, d.database_id) + '.'
        + OBJECT_NAME(d.object_id, d.database_id)
        + ' (' + ISNULL(d.equality_columns, '')
        + CASE WHEN d.equality_columns IS NOT NULL AND d.inequality_columns IS NOT NULL THEN ', ' ELSE '' END
        + ISNULL(d.inequality_columns, '') + ')'
        + CASE WHEN d.included_columns IS NOT NULL THEN ' INCLUDE (' + d.included_columns + ')' ELSE '' END
        + ';'                                                      AS create_index_statement
FROM sys.dm_db_missing_index_details d
JOIN sys.dm_db_missing_index_groups g     ON d.index_handle = g.index_handle
JOIN sys.dm_db_missing_index_group_stats s ON g.index_group_handle = s.group_handle
WHERE d.database_id = DB_ID()
ORDER BY improvement_measure DESC;

-- Per-DB data/log size + the single biggest table.
-- Iterates user DBs. Skips system DBs. NOCOUNT so the dynamic INSERTs don't
-- confuse the driver about how many result sets are coming back.
SET NOCOUNT ON;

DECLARE @sql NVARCHAR(MAX) = N'';

CREATE TABLE #out (
    database_name      sysname,
    data_size_mb       INT,
    data_used_mb       INT,
    log_size_mb        INT,
    log_used_mb        INT,
    largest_table      NVARCHAR(256),
    largest_table_mb   INT
);

SELECT @sql = @sql + N'
USE ' + QUOTENAME(name) + N';
INSERT #out
SELECT
    DB_NAME(),
    (SELECT SUM(size) * 8 / 1024 FROM sys.database_files WHERE type_desc = ''ROWS''),
    (SELECT SUM(FILEPROPERTY(name, ''SpaceUsed'')) * 8 / 1024 FROM sys.database_files WHERE type_desc = ''ROWS''),
    (SELECT SUM(size) * 8 / 1024 FROM sys.database_files WHERE type_desc = ''LOG''),
    (SELECT SUM(FILEPROPERTY(name, ''SpaceUsed'')) * 8 / 1024 FROM sys.database_files WHERE type_desc = ''LOG''),
    (SELECT TOP 1 OBJECT_SCHEMA_NAME(t.object_id) + ''.'' + t.name
       FROM sys.tables t
       JOIN sys.partitions p ON p.object_id = t.object_id
       JOIN sys.allocation_units au ON au.container_id = p.partition_id
       GROUP BY t.object_id, t.name
       ORDER BY SUM(au.total_pages) DESC),
    (SELECT TOP 1 SUM(au.total_pages) * 8 / 1024
       FROM sys.partitions p
       JOIN sys.allocation_units au ON au.container_id = p.partition_id
       JOIN sys.tables t ON t.object_id = p.object_id
       GROUP BY t.object_id
       ORDER BY SUM(au.total_pages) DESC);
'
FROM sys.databases
WHERE database_id > 4
  AND state_desc = 'ONLINE'
  AND HAS_DBACCESS(name) = 1;

EXEC sp_executesql @sql;

SELECT * FROM #out ORDER BY data_used_mb DESC;

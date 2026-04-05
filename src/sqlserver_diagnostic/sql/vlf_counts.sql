-- VLF count per user DB via sys.dm_db_log_info (2016 SP2+ / 2017+).
-- For older versions you'd need DBCC LOGINFO and a temp table per DB.
;WITH vlf AS (
    SELECT
        d.name AS database_name,
        (SELECT COUNT(*) FROM sys.dm_db_log_info(d.database_id)) AS vlf_count,
        (SELECT SUM(size) * 8 / 1024 FROM sys.master_files
          WHERE database_id = d.database_id AND type_desc = 'LOG') AS log_size_mb
    FROM sys.databases d
    WHERE d.database_id > 4
      AND d.state_desc = 'ONLINE'
)
SELECT
    database_name,
    vlf_count,
    log_size_mb,
    'DBCC SHRINKFILE ([' + database_name + '_log], 0); '
        + '-- then ALTER DATABASE [' + database_name + '] MODIFY FILE (NAME = ''' + database_name + '_log'', SIZE = '
        + CAST(log_size_mb AS VARCHAR(20)) + 'MB, FILEGROWTH = 1024MB);' AS recommendation_statement
FROM vlf
ORDER BY vlf_count DESC;

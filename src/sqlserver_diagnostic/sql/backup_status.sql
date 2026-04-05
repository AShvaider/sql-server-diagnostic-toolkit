-- Hours since last full / log backup per user DB.
-- NULL hours_since_full means no backup ever recorded in msdb.
SELECT
    d.name                                                 AS database_name,
    d.recovery_model_desc                                  AS recovery_model,
    DATEDIFF(MINUTE, MAX(bf.backup_finish_date), SYSUTCDATETIME()) / 60.0 AS hours_since_full,
    DATEDIFF(MINUTE, MAX(bl.backup_finish_date), SYSUTCDATETIME()) / 60.0 AS hours_since_log
FROM sys.databases d
LEFT JOIN msdb.dbo.backupset bf
       ON bf.database_name = d.name AND bf.type = 'D'
LEFT JOIN msdb.dbo.backupset bl
       ON bl.database_name = d.name AND bl.type = 'L'
WHERE d.database_id > 4
  AND d.state_desc = 'ONLINE'
GROUP BY d.name, d.recovery_model_desc
ORDER BY d.name;

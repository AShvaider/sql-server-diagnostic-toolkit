-- User sessions grouped by login + host. Excludes internal/system.
SELECT
    login_name,
    host_name,
    program_name,
    status,
    COUNT(*) AS session_count
FROM sys.dm_exec_sessions
WHERE is_user_process = 1
GROUP BY login_name, host_name, program_name, status
ORDER BY session_count DESC;

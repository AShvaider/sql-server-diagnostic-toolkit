-- Snapshot of current blocking chains. Refresh to see if it persists.
SELECT
    blocked.session_id            AS blocked_session_id,
    blocker.session_id            AS blocker_session_id,
    blocked.wait_time             AS wait_time_ms,
    blocked.wait_type             AS wait_type,
    blocked.resource_description  AS resource_description,
    bs.login_name                 AS blocker_login,
    bd.login_name                 AS blocked_login,
    bt.text                       AS blocker_query,
    blocked_t.text                AS blocked_query
FROM sys.dm_os_waiting_tasks blocked
JOIN sys.dm_exec_requests blocked_req
       ON blocked.session_id = blocked_req.session_id
JOIN sys.dm_exec_sessions bd
       ON bd.session_id = blocked.session_id
JOIN sys.dm_exec_sessions bs
       ON bs.session_id = blocked.blocking_session_id
JOIN sys.dm_exec_requests blocker
       ON blocker.session_id = blocked.blocking_session_id
OUTER APPLY sys.dm_exec_sql_text(blocker.sql_handle)     bt
OUTER APPLY sys.dm_exec_sql_text(blocked_req.sql_handle) blocked_t
WHERE blocked.blocking_session_id IS NOT NULL
  AND blocked.blocking_session_id <> 0;

-- Top waits since last DBCC SQLPERF reset (or server restart).
-- Excludes a long list of benign idle/internal waits.
WITH ranked AS (
    SELECT
        wait_type,
        wait_time_ms / 1000.0           AS wait_time_s,
        signal_wait_time_ms / 1000.0    AS signal_wait_time_s,
        waiting_tasks_count,
        ROW_NUMBER() OVER (ORDER BY wait_time_ms DESC) AS rank,
        SUM(wait_time_ms) OVER ()       AS total_wait_ms
    FROM sys.dm_os_wait_stats
    WHERE waiting_tasks_count > 0
      AND wait_type NOT IN (
          'BROKER_EVENTHANDLER','BROKER_RECEIVE_WAITFOR','BROKER_TASK_STOP',
          'BROKER_TO_FLUSH','BROKER_TRANSMITTER','CHECKPOINT_QUEUE',
          'CHKPT','CLR_AUTO_EVENT','CLR_MANUAL_EVENT','DBMIRROR_EVENTS_QUEUE',
          'DIRTY_PAGE_POLL','DISPATCHER_QUEUE_SEMAPHORE',
          'FT_IFTS_SCHEDULER_IDLE_WAIT','FT_IFTSHC_MUTEX',
          'HADR_CLUSAPI_CALL','HADR_FILESTREAM_IOMGR_IOCOMPLETION',
          'HADR_LOGCAPTURE_WAIT','HADR_NOTIFICATION_DEQUEUE',
          'HADR_TIMER_TASK','HADR_WORK_QUEUE','LAZYWRITER_SLEEP',
          'LOGMGR_QUEUE','MEMORY_ALLOCATION_EXT',
          'ONDEMAND_TASK_QUEUE','PWAIT_ALL_COMPONENTS_INITIALIZED',
          'QDS_PERSIST_TASK_MAIN_LOOP_SLEEP','QDS_ASYNC_QUEUE',
          'REQUEST_FOR_DEADLOCK_SEARCH','SLEEP_DBSTARTUP','SLEEP_TASK',
          'SP_SERVER_DIAGNOSTICS_SLEEP','SQLTRACE_BUFFER_FLUSH',
          'WAITFOR','WAIT_XTP_HOST_WAIT','XE_DISPATCHER_WAIT',
          'XE_TIMER_EVENT',
          -- Added after a real run on 2022 in a container surfaced these as noise:
          'AZURE_IMDS_VERSIONS','SOS_WORK_DISPATCHER',
          'SQLTRACE_INCREMENTAL_FLUSH_SLEEP','SQLTRACE_WAIT_ENTRIES',
          'PWAIT_EXTENSIBILITY_CLEANUP_TASK','STARTUP_DEPENDENCY_MANAGER',
          'SLEEP_MASTERDBREADY','SLEEP_PHYSMASTERDBREADY','SLEEP_SYSTEMTASK',
          'SLEEP_MSDBSTARTUP','SLEEP_TEMPDBSTARTUP',
          'PREEMPTIVE_OS_FLUSHFILEBUFFERS','PREEMPTIVE_OS_WRITEFILEGATHER',
          'PREEMPTIVE_OS_DEVICEOPS','PREEMPTIVE_OS_GETPROCADDRESS',
          'PREEMPTIVE_OS_LOOKUPACCOUNTSID','PREEMPTIVE_OS_AUTHENTICATIONOPS',
          'LOGBUFFER'
      )
)
SELECT TOP 15
    rank,
    wait_type,
    wait_time_s,
    signal_wait_time_s,
    waiting_tasks_count,
    CAST(100.0 * (wait_time_s * 1000) / NULLIF(total_wait_ms, 0) AS DECIMAL(5,1))
        AS pct_total_wait
FROM ranked
ORDER BY rank;

-- A handful of memory-pressure metrics from sys.dm_os_performance_counters.
-- All cumulative; PLE is a point-in-time gauge.

SELECT 'page_life_expectancy' AS metric,
       cntr_value             AS value,
       'seconds'               AS unit
FROM sys.dm_os_performance_counters
WHERE counter_name = 'Page life expectancy'
  AND object_name LIKE '%Buffer Manager%'

UNION ALL

SELECT 'buffer_cache_hit_ratio',
       100.0 * a.cntr_value / NULLIF(b.cntr_value, 0),
       'percent'
FROM sys.dm_os_performance_counters a
JOIN sys.dm_os_performance_counters b
       ON b.counter_name = 'Buffer cache hit ratio base'
      AND b.object_name = a.object_name
WHERE a.counter_name = 'Buffer cache hit ratio'

UNION ALL

SELECT 'memory_grants_pending',
       cntr_value,
       'count'
FROM sys.dm_os_performance_counters
WHERE counter_name = 'Memory Grants Pending';

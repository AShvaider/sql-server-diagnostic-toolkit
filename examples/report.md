# shopdb diagnostic report

`9a6635a9bb2b` · Microsoft SQL Server 2022 (RTM-CU24-GDR) (KB5083252) - 16.0.4250.1 (X64) · scanned 2026-04-18 22:40 UTC

**Action required.** 3 critical, 14 warning, 25 info.

## Critical (3)

### No recent full backup: shopdb

Last FULL: never hours ago.

```sql
BACKUP DATABASE [shopdb] TO DISK='...' WITH CHECKSUM, COMPRESSION;
```

### Log backup gap > 24h: shopdb

Recovery model is FULL, last log backup never hours ago. Log will grow unbounded.

```sql
BACKUP LOG [shopdb] TO DISK='...' WITH COMPRESSION;
```

### 8,752 ms avg · 1 runs

WITH n AS (
    SELECT TOP (200000) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS i
    FROM sys.all_objects a CROSS JOIN sys.all_objects...

```
WITH n AS (
    SELECT TOP (200000) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS i
    FROM sys.all_objects a CROSS JOIN sys.all_objects b CROSS JOIN sys.all_objects c
)
INSERT audit_log (occurred_at, actor, action, payload)
SELECT
    DATEADD(SECOND, -ABS(CHECKSUM(NEWID())) % (60 * 60 * 24 * 30), SYSUTCDATETIME()),
    CONCAT('user', 1 + ABS(CHECKSUM(NEWID())) % 200),
    CASE ABS(CHECKSUM(NEWID())) % 4
         WHEN 0 THEN 'login' WHEN 1 THEN 'view'
         WHEN 2 THEN 'update' ELSE 'logout' END,
    REPLICATE('x', 200)
FROM n
```

## Warnings (14)

| Finding | ID |
| --- | --- |
| PLE low: 440s | `cap.mem.page_life_expectancy` |
| Plan: ImplicitConversion | `perf.plan.implicitconversion.19922F` |
| Plan: ImplicitConversion | `perf.plan.implicitconversion.23293B` |
| Plan: ImplicitConversion | `perf.plan.implicitconversion.310DE6` |
| Plan: ImplicitConversion | `perf.plan.implicitconversion.48F7E3` |
| Plan: ImplicitConversion | `perf.plan.implicitconversion.4B9367` |
| Plan: ImplicitConversion | `perf.plan.implicitconversion.6B190B` |
| Plan: ImplicitConversion | `perf.plan.implicitconversion.6EFBA4` |
| Plan: ImplicitConversion | `perf.plan.implicitconversion.8B12F4` |
| Plan: ImplicitConversion | `perf.plan.implicitconversion.9885C2` |
| Plan: ImplicitConversion | `perf.plan.implicitconversion.DC4ACD` |
| Plan: ImplicitConversion | `perf.plan.implicitconversion.F7F1E3` |
| 1,837 ms avg · 1 runs | `perf.query.b'\xe6\x02p\x1f\x91\x85'` |
| 2,158 ms avg · 1 runs | `perf.query.b'\xff\xe0\x8e\xb4\xba\xb7'` |

## Info (25)

| Finding | ID |
| --- | --- |
| CXPACKET: 8.8% | `bot.wait.cxpacket` |
| IO_COMPLETION: 2.1% | `bot.wait.io_completion` |
| LATCH_EX: 3.7% | `bot.wait.latch_ex` |
| LCK_M_S: 4.3% | `bot.wait.lck_m_s` |
| LCK_M_SCH_M: 16.8% | `bot.wait.lck_m_sch_m` |
| LCK_M_SCH_S: 8.5% | `bot.wait.lck_m_sch_s` |
| LCK_M_U: 14.3% | `bot.wait.lck_m_u` |
| PAGEIOLATCH_SH: 5.4% | `bot.wait.pageiolatch_sh` |
| PAGEIOLATCH_UP: 2.6% | `bot.wait.pageiolatch_up` |
| PAGELATCH_UP: 4.0% | `bot.wait.pagelatch_up` |
| PREEMPTIVE_OS_CRYPTOPS: 2.2% | `bot.wait.preemptive_os_cryptops` |
| PREEMPTIVE_OS_FILEOPS: 2.9% | `bot.wait.preemptive_os_fileops` |
| PREEMPTIVE_OS_WRITEFILE: 4.2% | `bot.wait.preemptive_os_writefile` |
| SLEEP_MASTERUPGRADED: 7.0% | `bot.wait.sleep_masterupgraded` |
| WRITELOG: 4.7% | `bot.wait.writelog` |
| 1 × NT AUTHORITY\SYSTEM from 9a6635a9bb2b | `cap.sess.NT AUTHORITY\SYSTEM.9a6635a9bb2b` |
| 1 × sa from npidev-script | `cap.sess.sa.npidev-script` |
| shopdb: 126 MB data, 1 MB log | `hlt.size.shopdb` |
| 1 indexes below 10% fragmentation | `perf.frag.summary` |
| Missing index on dbo.customers ([email]) | `perf.missing_idx.customers.[email]` |
| Missing index on dbo.orders ([customer_id]) | `perf.missing_idx.orders.[customer_id]` |
| 87 ms avg · 3 runs | `perf.query.b';\xdcnW\x14\xd2'` |
| 295 ms avg · 1 runs | `perf.query.b'\xc2\x9a\xa4\xd2\x11}'` |
| 412 ms avg · 1 runs | `perf.query.b'\xe3\xee\xd5L\x9a\xde'` |
| 596 ms avg · 1 runs | `perf.query.b'_\xde\xba\xad:,'` |

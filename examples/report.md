# shopdb diagnostic report

`prod-sql-01.internal,1433` · SQL Server 2022 (RTM-CU10) Standard Edition · scanned 2026-04-18 22:19 UTC

**Action required.** 6 critical, 22 warning, 29 info.

## Critical (6)

### PLE critically low: 278s

Buffer pool is churning. Add memory or reduce IO.

### Log backup gap > 24h: shopdb

Recovery model is FULL, last log backup 34.7 hours ago. Log will grow unbounded.

```sql
BACKUP LOG [shopdb] TO DISK='...' WITH COMPRESSION;
```

### VLF count 14,820 on shopdb

Startup, log backups, and crash recovery will be slow.

```sql
USE shopdb; DBCC SHRINKFILE (shopdb_log, 100); ALTER DATABASE shopdb MODIFY FILE (NAME = shopdb_log, SIZE = 8192MB, FILEGROWTH = 8192MB);
```

### Heavily fragmented: IX_audit_log_created_at on dbo.audit_log

87.3% over 185,400 pages. Rebuild.

```sql
ALTER INDEX [IX_audit_log_created_at] ON [dbo].[audit_log] REBUILD;
```

### Missing index on dbo.customers (email)

Improvement measure 2,540,000, avg impact 92%, 0 seeks.

```sql
CREATE NONCLUSTERED INDEX IX_customers_email ON dbo.customers (email) INCLUDE (first_name, last_name, created_at);
```

### 7,200 ms avg · 18,400 runs

SELECT o.id, o.customer_id, SUM(oi.quantity * oi.unit_price) AS total FROM dbo.orders o JOIN dbo.order_items oi ON oi.order_id = o.id WHE...

```sql
SELECT o.id, o.customer_id, SUM(oi.quantity * oi.unit_price) AS total FROM dbo.orders o JOIN dbo.order_items oi ON oi.order_id = o.id WHERE o.created_at > DATEADD(day, -30, GETDATE()) GROUP BY o.id, o.customer_id
```

## Warnings (22)

| Finding | ID |
| --- | --- |
| Session 104 blocking 227 (12,800 ms) | `bot.block.104_227` |
| Session 87 blocking 192 (45,300 ms) | `bot.block.87_192` |
| tempdb: 2 data file(s), recommended 8 | `bot.tempdb` |
| PAGEIOLATCH_SH: 32.1% | `bot.wait.pageiolatch_sh` |
| Buffer cache hit ratio 93.8% | `cap.mem.buffer_cache_hit_ratio` |
| Fragmented: IX_events_user_time (25%) | `perf.frag.IX_events_user_time` |
| Fragmented: IX_order_items_product (22%) | `perf.frag.IX_order_items_product` |
| Fragmented: PK_orders (12%) | `perf.frag.PK_orders` |
| Fragmented: PK_products (28%) | `perf.frag.PK_products` |
| Fragmented: PK_sessions (19%) | `perf.frag.PK_sessions` |
| Missing index on dbo.order_items (order_id) | `perf.missing_idx.order_items.order_id` |
| Missing index on dbo.orders (customer_id) | `perf.missing_idx.orders.customer_id` |
| Plan: ImplicitConversion | `perf.plan.implicitconversion.A1B2C3` |
| Plan: MissingStatistics | `perf.plan.missingstatistics.B7C8D9` |
| Plan: SpillToTempDB | `perf.plan.spilltotempdb.3F9A8B` |
| Plan: TableScan | `perf.plan.tablescan.3F9A8B` |
| 1,500 ms avg · 8,900 runs | `perf.query.7B3C2A1E` |
| 2,100 ms avg · 42,800 runs | `perf.query.A1B2C3D4` |
| Unused index: IX_audit_log_source | `perf.unused_idx.IX_audit_log_source` |
| Unused index: IX_customers_phone_alt | `perf.unused_idx.IX_customers_phone_alt` |
| Unused index: IX_orders_referral_code | `perf.unused_idx.IX_orders_referral_code` |
| Unused index: IX_products_sku_legacy | `perf.unused_idx.IX_products_sku_legacy` |

## Info (29)

| Finding | ID |
| --- | --- |
| ASYNC_NETWORK_IO: 7.2% | `bot.wait.async_network_io` |
| CXCONSUMER: 2.1% | `bot.wait.cxconsumer` |
| CXPACKET: 22.5% | `bot.wait.cxpacket` |
| LCK_M_S: 3.2% | `bot.wait.lck_m_s` |
| LCK_M_X: 8.5% | `bot.wait.lck_m_x` |
| PAGELATCH_EX: 4.8% | `bot.wait.pagelatch_ex` |
| RESOURCE_SEMAPHORE: 1.2% | `bot.wait.resource_semaphore` |
| SOS_SCHEDULER_YIELD: 6.1% | `bot.wait.sos_scheduler_yield` |
| WRITELOG: 12.3% | `bot.wait.writelog` |
| 184 × app_service from web-prod-02 | `cap.sess.app_service.web-prod-02` |
| 42 × app_service from web-prod-03 | `cap.sess.app_service.web-prod-03` |
| 3 × dba_readonly from ops-laptop | `cap.sess.dba_readonly.ops-laptop` |
| 8 × etl_pipeline from etl-01 | `cap.sess.etl_pipeline.etl-01` |
| 12 × reporting_user from bi-01 | `cap.sess.reporting_user.bi-01` |
| shopdb: 102,400 MB data, 12,100 MB log | `hlt.size.shopdb` |
| 9 indexes below 10% fragmentation | `perf.frag.summary` |
| Missing index on dbo.audit_log (created_at) | `perf.missing_idx.audit_log.created_at` |
| Missing index on dbo.events (user_id) | `perf.missing_idx.events.user_id` |
| Missing index on dbo.products (category_id) | `perf.missing_idx.products.category_id` |
| Plan: ColumnsWithNoStatistics | `perf.plan.columnswithnostatistics.55AA66` |
| Plan: ColumnsWithNoStatistics | `perf.plan.columnswithnostatistics.66AA77` |
| Plan: ColumnsWithNoStatistics | `perf.plan.columnswithnostatistics.77AA88` |
| 10 ms avg · 12,400 runs | `perf.query.11223344` |
| 15 ms avg · 38,900 runs | `perf.query.9988AABB` |
| 20 ms avg · 54,200 runs | `perf.query.AA55BB66` |
| 8 ms avg · 6,200 runs | `perf.query.ABCDEF01` |
| 90 ms avg · 215,000 runs | `perf.query.CC11AA22` |
| 40 ms avg · 184,000 runs | `perf.query.DEAD0001` |
| 35 ms avg · 97,500 runs | `perf.query.FEED0003` |

## Probes that failed

- `query_store_top_queries`: Query Store is not enabled on this database (falling back to sys.dm_exec_query_stats)

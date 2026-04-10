"""Hand-rolled fixture of probe output, shaped like what a real scan returns.

The underlying "database" is an e-commerce schema (customers, orders,
order_items, products, sessions, audit_log, events, ...). Numbers were chosen
to produce a realistic distribution of findings for the sample report.
"""

SERVER_INFO = {
    "server_name": "prod-sql-01.internal,1433",
    "database_name": "shopdb",
    "sql_version": "SQL Server 2022 (RTM-CU10) Standard Edition",
    "scan_duration_s": 3.8,
}


FIXTURE = {
    "top_slow_queries": [
        {
            "query_hash": "0x3F9A8B1C2D4E5F60",
            "execution_count": 18_400,
            "total_worker_time_ms": 132_480_000,
            "avg_worker_time_ms": 7_200,
            "avg_logical_reads": 1_240_000,
            "query_text": (
                "SELECT o.id, o.customer_id, SUM(oi.quantity * oi.unit_price) AS total "
                "FROM dbo.orders o JOIN dbo.order_items oi ON oi.order_id = o.id "
                "WHERE o.created_at > DATEADD(day, -30, GETDATE()) "
                "GROUP BY o.id, o.customer_id"
            ),
            "last_execution_time": "2026-04-17 08:12:33",
        },
        {
            "query_hash": "0xA1B2C3D4E5F60718",
            "execution_count": 42_800,
            "total_worker_time_ms": 89_880_000,
            "avg_worker_time_ms": 2_100,
            "avg_logical_reads": 312_000,
            "query_text": (
                "SELECT TOP 50 p.* FROM dbo.products p "
                "WHERE p.name LIKE @search OR p.description LIKE @search "
                "ORDER BY p.updated_at DESC"
            ),
            "last_execution_time": "2026-04-17 08:14:02",
        },
        {
            "query_hash": "0x7B3C2A1E4F5D6082",
            "execution_count": 8_900,
            "total_worker_time_ms": 13_350_000,
            "avg_worker_time_ms": 1_500,
            "avg_logical_reads": 84_500,
            "query_text": (
                "SELECT c.id, c.email, COUNT(DISTINCT o.id) AS orders "
                "FROM dbo.customers c LEFT JOIN dbo.orders o ON o.customer_id = c.id "
                "GROUP BY c.id, c.email HAVING COUNT(DISTINCT o.id) > 5"
            ),
            "last_execution_time": "2026-04-17 08:10:41",
        },
        {
            "query_hash": "0xCC11AA22BB3344F0",
            "execution_count": 215_000,
            "total_worker_time_ms": 19_350_000,
            "avg_worker_time_ms": 90,
            "avg_logical_reads": 340,
            "query_text": "SELECT * FROM dbo.customers WHERE id = @id",
            "last_execution_time": "2026-04-17 08:14:59",
        },
        {
            "query_hash": "0xDEAD0001BEEF0002",
            "execution_count": 184_000,
            "total_worker_time_ms": 7_360_000,
            "avg_worker_time_ms": 40,
            "avg_logical_reads": 120,
            "query_text": "SELECT id, total, status FROM dbo.orders WHERE customer_id = @cid",
            "last_execution_time": "2026-04-17 08:14:58",
        },
        {
            "query_hash": "0xFEED0003CAFE0004",
            "execution_count": 97_500,
            "total_worker_time_ms": 3_412_500,
            "avg_worker_time_ms": 35,
            "avg_logical_reads": 88,
            "query_text": (
                "UPDATE dbo.sessions SET last_seen = SYSUTCDATETIME() WHERE token = @t"
            ),
            "last_execution_time": "2026-04-17 08:14:59",
        },
        {
            "query_hash": "0xAA55BB66CC77DD80",
            "execution_count": 54_200,
            "total_worker_time_ms": 1_084_000,
            "avg_worker_time_ms": 20,
            "avg_logical_reads": 42,
            "query_text": "INSERT INTO dbo.events (user_id, type, created_at) VALUES (?, ?, ?)",
            "last_execution_time": "2026-04-17 08:14:57",
        },
        {
            "query_hash": "0x9988AABB77665544",
            "execution_count": 38_900,
            "total_worker_time_ms": 583_500,
            "avg_worker_time_ms": 15,
            "avg_logical_reads": 29,
            "query_text": "SELECT token, user_id FROM dbo.sessions WHERE token = @t AND expires_at > SYSUTCDATETIME()",
            "last_execution_time": "2026-04-17 08:14:55",
        },
        {
            "query_hash": "0x1122334455667788",
            "execution_count": 12_400,
            "total_worker_time_ms": 124_000,
            "avg_worker_time_ms": 10,
            "avg_logical_reads": 18,
            "query_text": "SELECT id, name, price FROM dbo.products WHERE id IN (?, ?, ?, ?, ?)",
            "last_execution_time": "2026-04-17 08:14:30",
        },
        {
            "query_hash": "0xABCDEF0102030405",
            "execution_count": 6_200,
            "total_worker_time_ms": 49_600,
            "avg_worker_time_ms": 8,
            "avg_logical_reads": 12,
            "query_text": "SELECT * FROM dbo.carts WHERE customer_id = @cid AND status = 'open'",
            "last_execution_time": "2026-04-17 08:13:22",
        },
    ],

    "plan_warnings": [
        {
            "warning_type": "ImplicitConversion",
            "query_hash": "0xA1B2C3D4E5F60718",
            "query_text": "SELECT * FROM dbo.customers WHERE email = @email",
            "detail": "Converting varchar(255) to nvarchar(4000). Index IX_customers_email not used.",
            "column_ref": "dbo.customers.email",
        },
        {
            "warning_type": "MissingStatistics",
            "query_hash": "0xB7C8D9E0F1A20304",
            "query_text": "SELECT COUNT(*) FROM dbo.events WHERE user_id = ? AND type = ?",
            "detail": "Statistics missing on (user_id, type). Cardinality estimate off by 40x.",
            "column_ref": "dbo.events.type",
        },
        {
            "warning_type": "TableScan",
            "query_hash": "0x3F9A8B1C2D4E5F60",
            "query_text": "SELECT * FROM dbo.audit_log WHERE actor_id = ? ORDER BY created_at DESC",
            "detail": "Full table scan over 42M rows. No useful index on actor_id.",
            "column_ref": "dbo.audit_log.actor_id",
        },
        {
            "warning_type": "SpillToTempDB",
            "query_hash": "0x3F9A8B1C2D4E5F60",
            "query_text": "... GROUP BY o.id, o.customer_id",
            "detail": "Hash match spilled 450 MB to tempdb during aggregation.",
            "column_ref": None,
        },
        {
            "warning_type": "ColumnsWithNoStatistics",
            "query_hash": "0x55AA66BB77CC88DD",
            "query_text": "SELECT * FROM dbo.reviews WHERE is_moderated = 0",
            "detail": "Column dbo.reviews.is_moderated has no statistics.",
            "column_ref": "dbo.reviews.is_moderated",
        },
        {
            "warning_type": "ColumnsWithNoStatistics",
            "query_hash": "0x66AA77BB88CC99EE",
            "query_text": "SELECT * FROM dbo.shipments WHERE carrier = ?",
            "detail": "Column dbo.shipments.carrier has no statistics.",
            "column_ref": "dbo.shipments.carrier",
        },
        {
            "warning_type": "ColumnsWithNoStatistics",
            "query_hash": "0x77AA88BB99CCAAFF",
            "query_text": "SELECT * FROM dbo.notifications WHERE channel = ?",
            "detail": "Column dbo.notifications.channel has no statistics.",
            "column_ref": "dbo.notifications.channel",
        },
    ],

    "missing_indexes": [
        {
            "schema_name": "dbo", "table_name": "customers",
            "equality_columns": "email", "inequality_columns": None,
            "included_columns": "first_name, last_name, created_at",
            "improvement_measure": 2_540_000,
            "user_seeks": 0, "user_scans": 18_400,
            "avg_user_impact": 92.4,
            "create_index_statement":
                "CREATE NONCLUSTERED INDEX IX_customers_email "
                "ON dbo.customers (email) "
                "INCLUDE (first_name, last_name, created_at);",
        },
        {
            "schema_name": "dbo", "table_name": "orders",
            "equality_columns": "customer_id", "inequality_columns": "created_at",
            "included_columns": "status, total",
            "improvement_measure": 480_000,
            "user_seeks": 8_200, "user_scans": 120,
            "avg_user_impact": 71.8,
            "create_index_statement":
                "CREATE NONCLUSTERED INDEX IX_orders_customer_created "
                "ON dbo.orders (customer_id, created_at) "
                "INCLUDE (status, total);",
        },
        {
            "schema_name": "dbo", "table_name": "order_items",
            "equality_columns": "order_id", "inequality_columns": None,
            "included_columns": "product_id, quantity, unit_price",
            "improvement_measure": 215_000,
            "user_seeks": 14_800, "user_scans": 0,
            "avg_user_impact": 58.3,
            "create_index_statement":
                "CREATE NONCLUSTERED INDEX IX_order_items_order "
                "ON dbo.order_items (order_id) "
                "INCLUDE (product_id, quantity, unit_price);",
        },
        {
            "schema_name": "dbo", "table_name": "events",
            "equality_columns": "user_id", "inequality_columns": "created_at",
            "included_columns": "type",
            "improvement_measure": 42_000,
            "user_seeks": 4_200, "user_scans": 42,
            "avg_user_impact": 64.1,
            "create_index_statement":
                "CREATE NONCLUSTERED INDEX IX_events_user_created "
                "ON dbo.events (user_id, created_at) "
                "INCLUDE (type);",
        },
        {
            "schema_name": "dbo", "table_name": "audit_log",
            "equality_columns": None, "inequality_columns": "created_at",
            "included_columns": "actor_id, action, target_type",
            "improvement_measure": 38_000,
            "user_seeks": 180, "user_scans": 640,
            "avg_user_impact": 28.5,
            "create_index_statement":
                "CREATE NONCLUSTERED INDEX IX_audit_log_created "
                "ON dbo.audit_log (created_at) "
                "INCLUDE (actor_id, action, target_type);",
        },
        {
            "schema_name": "dbo", "table_name": "products",
            "equality_columns": "category_id", "inequality_columns": None,
            "included_columns": "name, price",
            "improvement_measure": 7_800,
            "user_seeks": 1_200, "user_scans": 0,
            "avg_user_impact": 18.2,
            "create_index_statement":
                "CREATE NONCLUSTERED INDEX IX_products_category "
                "ON dbo.products (category_id) "
                "INCLUDE (name, price);",
        },
    ],

    "unused_indexes": [
        {
            "schema_name": "dbo", "table_name": "orders", "index_name": "IX_orders_referral_code",
            "size_mb": 182,
            "user_seeks": 0, "user_scans": 0, "user_lookups": 0,
            "user_updates": 4_218_400,
            "drop_statement": "DROP INDEX IX_orders_referral_code ON dbo.orders;",
        },
        {
            "schema_name": "dbo", "table_name": "customers", "index_name": "IX_customers_phone_alt",
            "size_mb": 94,
            "user_seeks": 0, "user_scans": 0, "user_lookups": 0,
            "user_updates": 1_820_500,
            "drop_statement": "DROP INDEX IX_customers_phone_alt ON dbo.customers;",
        },
        {
            "schema_name": "dbo", "table_name": "audit_log", "index_name": "IX_audit_log_source",
            "size_mb": 312,
            "user_seeks": 0, "user_scans": 2, "user_lookups": 0,
            "user_updates": 8_400_200,
            "drop_statement": "DROP INDEX IX_audit_log_source ON dbo.audit_log;",
        },
        {
            "schema_name": "dbo", "table_name": "products", "index_name": "IX_products_sku_legacy",
            "size_mb": 28,
            "user_seeks": 0, "user_scans": 0, "user_lookups": 0,
            "user_updates": 215_400,
            "drop_statement": "DROP INDEX IX_products_sku_legacy ON dbo.products;",
        },
    ],

    "index_fragmentation": [
        {"schema_name": "dbo", "table_name": "audit_log",  "index_name": "IX_audit_log_created_at",
         "avg_fragmentation_in_percent": 87.3, "page_count": 185_400, "fragment_count": 14_820,
         "index_type_desc": "NONCLUSTERED INDEX"},
        {"schema_name": "dbo", "table_name": "events",     "index_name": "IX_events_user_time",
         "avg_fragmentation_in_percent": 24.6, "page_count": 92_100, "fragment_count": 3_140,
         "index_type_desc": "NONCLUSTERED INDEX"},
        {"schema_name": "dbo", "table_name": "products",   "index_name": "PK_products",
         "avg_fragmentation_in_percent": 28.4, "page_count": 18_200, "fragment_count": 880,
         "index_type_desc": "CLUSTERED INDEX"},
        {"schema_name": "dbo", "table_name": "order_items","index_name": "IX_order_items_product",
         "avg_fragmentation_in_percent": 22.1, "page_count": 64_500, "fragment_count": 2_310,
         "index_type_desc": "NONCLUSTERED INDEX"},
        {"schema_name": "dbo", "table_name": "sessions",   "index_name": "PK_sessions",
         "avg_fragmentation_in_percent": 18.7, "page_count": 24_800, "fragment_count": 1_020,
         "index_type_desc": "CLUSTERED INDEX"},
        {"schema_name": "dbo", "table_name": "orders",     "index_name": "PK_orders",
         "avg_fragmentation_in_percent": 12.4, "page_count": 128_400, "fragment_count": 3_940,
         "index_type_desc": "CLUSTERED INDEX"},
        {"schema_name": "dbo", "table_name": "customers",  "index_name": "PK_customers",
         "avg_fragmentation_in_percent": 3.2, "page_count": 42_800, "fragment_count": 280,
         "index_type_desc": "CLUSTERED INDEX"},
        {"schema_name": "dbo", "table_name": "customers",  "index_name": "IX_customers_email",
         "avg_fragmentation_in_percent": 4.1, "page_count": 8_400, "fragment_count": 72,
         "index_type_desc": "NONCLUSTERED INDEX"},
        {"schema_name": "dbo", "table_name": "payments",   "index_name": "PK_payments",
         "avg_fragmentation_in_percent": 1.8, "page_count": 31_200, "fragment_count": 110,
         "index_type_desc": "CLUSTERED INDEX"},
        {"schema_name": "dbo", "table_name": "reviews",    "index_name": "PK_reviews",
         "avg_fragmentation_in_percent": 6.4, "page_count": 4_800, "fragment_count": 52,
         "index_type_desc": "CLUSTERED INDEX"},
        {"schema_name": "dbo", "table_name": "carts",      "index_name": "PK_carts",
         "avg_fragmentation_in_percent": 2.1, "page_count": 2_400, "fragment_count": 22,
         "index_type_desc": "CLUSTERED INDEX"},
        {"schema_name": "dbo", "table_name": "cart_items", "index_name": "PK_cart_items",
         "avg_fragmentation_in_percent": 4.8, "page_count": 5_600, "fragment_count": 84,
         "index_type_desc": "CLUSTERED INDEX"},
        {"schema_name": "dbo", "table_name": "shipments",  "index_name": "PK_shipments",
         "avg_fragmentation_in_percent": 5.2, "page_count": 9_200, "fragment_count": 110,
         "index_type_desc": "CLUSTERED INDEX"},
        {"schema_name": "dbo", "table_name": "addresses",  "index_name": "PK_addresses",
         "avg_fragmentation_in_percent": 3.4, "page_count": 3_200, "fragment_count": 44,
         "index_type_desc": "CLUSTERED INDEX"},
        {"schema_name": "dbo", "table_name": "notifications","index_name": "PK_notifications",
         "avg_fragmentation_in_percent": 7.8, "page_count": 12_800, "fragment_count": 205,
         "index_type_desc": "CLUSTERED INDEX"},
    ],

    "wait_stats": [
        {"wait_type": "PAGEIOLATCH_SH",      "pct_total_wait": 32.1, "wait_time_s": 185_400, "signal_wait_time_s": 5_200,  "waiting_tasks_count": 14_800_000, "rank": 1},
        {"wait_type": "CXPACKET",            "pct_total_wait": 22.5, "wait_time_s": 129_800, "signal_wait_time_s": 3_800,  "waiting_tasks_count":  8_200_000, "rank": 2},
        {"wait_type": "WRITELOG",            "pct_total_wait": 12.3, "wait_time_s":  71_000, "signal_wait_time_s": 2_100,  "waiting_tasks_count": 22_400_000, "rank": 3},
        {"wait_type": "LCK_M_X",             "pct_total_wait":  8.5, "wait_time_s":  49_100, "signal_wait_time_s":   820,  "waiting_tasks_count":    182_400, "rank": 4},
        {"wait_type": "ASYNC_NETWORK_IO",    "pct_total_wait":  7.2, "wait_time_s":  41_600, "signal_wait_time_s":   480,  "waiting_tasks_count":  6_100_000, "rank": 5},
        {"wait_type": "SOS_SCHEDULER_YIELD", "pct_total_wait":  6.1, "wait_time_s":  35_200, "signal_wait_time_s":   420,  "waiting_tasks_count": 28_400_000, "rank": 6},
        {"wait_type": "PAGELATCH_EX",        "pct_total_wait":  4.8, "wait_time_s":  27_700, "signal_wait_time_s":   340,  "waiting_tasks_count":  3_200_000, "rank": 7},
        {"wait_type": "LCK_M_S",             "pct_total_wait":  3.2, "wait_time_s":  18_500, "signal_wait_time_s":   210,  "waiting_tasks_count":     84_100, "rank": 8},
        {"wait_type": "CXCONSUMER",          "pct_total_wait":  2.1, "wait_time_s":  12_100, "signal_wait_time_s":   140,  "waiting_tasks_count":  1_800_000, "rank": 9},
        {"wait_type": "RESOURCE_SEMAPHORE",  "pct_total_wait":  1.2, "wait_time_s":   6_900, "signal_wait_time_s":    85,  "waiting_tasks_count":      4_200, "rank": 10},
    ],

    "current_blocking": [
        {
            "blocker_session_id": 87, "blocked_session_id": 192,
            "wait_type": "LCK_M_X", "wait_time_ms": 45_300,
            "blocker_login": "app_service", "blocked_login": "reporting_user",
            "resource_description": "keylock hobtid=72057594045923328",
            "blocker_query": "UPDATE dbo.orders SET status = 'shipped' WHERE id = 1234567",
            "blocked_query": "SELECT * FROM dbo.orders WHERE customer_id = 42100",
        },
        {
            "blocker_session_id": 104, "blocked_session_id": 227,
            "wait_type": "LCK_M_S", "wait_time_ms": 12_800,
            "blocker_login": "etl_pipeline", "blocked_login": "app_service",
            "resource_description": "objectlock OBJECT: 5:1093578934",
            "blocker_query": "BEGIN TRAN; SELECT TOP (10000) * FROM dbo.events WITH (TABLOCKX); ...",
            "blocked_query": "INSERT INTO dbo.events (user_id, type, created_at) VALUES (?, ?, ?)",
        },
    ],

    "tempdb_contention": [
        {
            "file_count": 2, "recommended_file_count": 8,
            "file_count_imbalance_mb": 1_450,
            "pagelatch_contention_s": 820,
            "top_contention_resource": "2:1:3 (SGAM page)",
        }
    ],

    "database_sizes": [
        {
            "database_name": "shopdb",
            "data_size_mb": 145_000, "data_used_mb": 102_400,
            "log_size_mb": 28_000,  "log_used_mb": 12_100,
            "largest_table": "dbo.audit_log", "largest_table_mb": 42_100,
        },
    ],

    "backup_status": [
        {
            "database_name": "shopdb",
            "recovery_model": "FULL",
            "hours_since_full": 9.2,
            "hours_since_log": 34.7,
        },
        {
            "database_name": "shopdb_reports",
            "recovery_model": "SIMPLE",
            "hours_since_full": 22.5,
            "hours_since_log": None,
        },
        {
            "database_name": "shopdb_staging",
            "recovery_model": "SIMPLE",
            "hours_since_full": 6.8,
            "hours_since_log": None,
        },
    ],

    "vlf_counts": [
        {
            "database_name": "shopdb",
            "vlf_count": 14_820, "log_size_mb": 28_000,
            "recommendation_statement":
                "USE shopdb; DBCC SHRINKFILE (shopdb_log, 100); "
                "ALTER DATABASE shopdb MODIFY FILE "
                "(NAME = shopdb_log, SIZE = 8192MB, FILEGROWTH = 8192MB);",
        },
        {
            "database_name": "shopdb_reports",
            "vlf_count": 180, "log_size_mb": 2_048,
            "recommendation_statement": "",
        },
        {
            "database_name": "shopdb_staging",
            "vlf_count": 42, "log_size_mb": 512,
            "recommendation_statement": "",
        },
    ],

    "sessions": [
        {"login_name": "app_service",     "database_name": "shopdb", "host_name": "web-prod-02", "program_name": "Node.js Driver", "status": "running",  "session_count": 184},
        {"login_name": "app_service",     "database_name": "shopdb", "host_name": "web-prod-03", "program_name": "Node.js Driver", "status": "sleeping", "session_count":  42},
        {"login_name": "reporting_user",  "database_name": "shopdb", "host_name": "bi-01",       "program_name": "Power BI",      "status": "running",  "session_count":  12},
        {"login_name": "etl_pipeline",    "database_name": "shopdb", "host_name": "etl-01",      "program_name": ".Net SqlClient Data Provider", "status": "running", "session_count": 8},
        {"login_name": "dba_readonly",    "database_name": "shopdb", "host_name": "ops-laptop",  "program_name": "SSMS",          "status": "sleeping", "session_count":   3},
    ],

    "memory_pressure": [
        {"metric": "page_life_expectancy", "value": 278,   "unit": "seconds"},
        {"metric": "buffer_cache_hit_ratio","value": 93.8,  "unit": "percent"},
        {"metric": "memory_grants_pending","value": 0,     "unit": "count"},
    ],

    "_errors": [
        {"probe": "query_store_top_queries",
         "error": "Query Store is not enabled on this database (falling back to sys.dm_exec_query_stats)"},
    ],
}

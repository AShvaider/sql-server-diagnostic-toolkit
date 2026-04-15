/*
  Seed for the diagnostic toolkit's docker stack.

  Builds a small e-commerce schema, inserts ~100k rows total, and runs a few
  workload-shaped queries on purpose to make probes light up:
    - missing index suggestions on customers.email and orders.created_at
    - one heavily fragmented nonclustered index (audit_log_idx_ts)
    - one truly unused index that still takes writes (orders_idx_legacy_status)
    - a slow query (cross join into order_items)
    - DB in FULL recovery model with no log backup
    - small log file shrunk + grown a few times to inflate VLF count

  Tested against the docker-compose mssql:2022-latest image. Re-runnable: drops
  shopdb at the top.
*/

USE master;
IF DB_ID('shopdb') IS NOT NULL
BEGIN
    ALTER DATABASE shopdb SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE shopdb;
END

CREATE DATABASE shopdb;
ALTER DATABASE shopdb SET RECOVERY FULL;
GO

USE shopdb;
GO

-- Tables ---------------------------------------------------------------

CREATE TABLE customers (
    customer_id INT IDENTITY PRIMARY KEY,
    email       NVARCHAR(256) NOT NULL,
    full_name   NVARCHAR(128) NOT NULL,
    created_at  DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME()
);
-- Note: deliberately no index on email. The workload queries by email, which
-- is what produces the missing-index recommendation.

CREATE TABLE products (
    product_id INT IDENTITY PRIMARY KEY,
    sku        NVARCHAR(32) NOT NULL UNIQUE,
    name       NVARCHAR(256) NOT NULL,
    price_cents INT NOT NULL
);

CREATE TABLE orders (
    order_id    INT IDENTITY PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(customer_id),
    status      NVARCHAR(32) NOT NULL,
    total_cents INT NOT NULL,
    created_at  DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
-- Only the FK is implicitly indexable (no auto-index in MSSQL though).
-- The workload filters by created_at without an index.

CREATE TABLE order_items (
    order_item_id INT IDENTITY PRIMARY KEY,
    order_id      INT NOT NULL REFERENCES orders(order_id),
    product_id    INT NOT NULL REFERENCES products(product_id),
    quantity      INT NOT NULL,
    unit_cents    INT NOT NULL
);
CREATE INDEX orders_items_idx_order ON order_items(order_id);

CREATE TABLE audit_log (
    audit_id   BIGINT IDENTITY PRIMARY KEY,
    occurred_at DATETIME2 NOT NULL,
    actor      NVARCHAR(64),
    action     NVARCHAR(32),
    payload    NVARCHAR(MAX)
);
CREATE INDEX audit_log_idx_ts ON audit_log(occurred_at);
-- We will fragment this index later by deleting random rows.

-- An index nothing reads. The workload doesn't touch status much, but writes
-- all hit it because every INSERT/UPDATE on orders maintains it.
CREATE INDEX orders_idx_legacy_status ON orders(status) INCLUDE (total_cents, created_at);

GO

-- Seed data ------------------------------------------------------------

SET NOCOUNT ON;

-- 5,000 customers
;WITH n AS (
    SELECT TOP (5000) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS i
    FROM sys.all_objects a CROSS JOIN sys.all_objects b
)
INSERT customers (email, full_name, created_at)
SELECT
    CONCAT('user', i, '@example.com'),
    CONCAT('Customer ', i),
    DATEADD(DAY, -ABS(CHECKSUM(NEWID())) % 720, SYSUTCDATETIME())
FROM n;

-- 500 products
;WITH n AS (
    SELECT TOP (500) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS i
    FROM sys.all_objects
)
INSERT products (sku, name, price_cents)
SELECT
    CONCAT('SKU-', RIGHT('00000' + CAST(i AS VARCHAR(5)), 5)),
    CONCAT('Product ', i),
    100 + (ABS(CHECKSUM(NEWID())) % 9900)
FROM n;

-- 25,000 orders across the customer base
;WITH n AS (
    SELECT TOP (25000) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS i
    FROM sys.all_objects a CROSS JOIN sys.all_objects b
)
INSERT orders (customer_id, status, total_cents, created_at)
SELECT
    1 + ABS(CHECKSUM(NEWID())) % 5000,
    CASE ABS(CHECKSUM(NEWID())) % 5
         WHEN 0 THEN 'pending'
         WHEN 1 THEN 'paid'
         WHEN 2 THEN 'shipped'
         WHEN 3 THEN 'delivered'
         ELSE 'cancelled' END,
    500 + (ABS(CHECKSUM(NEWID())) % 50000),
    DATEADD(MINUTE, -ABS(CHECKSUM(NEWID())) % (60 * 24 * 365), SYSUTCDATETIME())
FROM n;

-- 75,000 order items (avg 3 per order)
;WITH n AS (
    SELECT TOP (75000) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS i
    FROM sys.all_objects a CROSS JOIN sys.all_objects b
)
INSERT order_items (order_id, product_id, quantity, unit_cents)
SELECT
    1 + ABS(CHECKSUM(NEWID())) % 25000,
    1 + ABS(CHECKSUM(NEWID())) % 500,
    1 + ABS(CHECKSUM(NEWID())) % 5,
    100 + (ABS(CHECKSUM(NEWID())) % 9900)
FROM n;

-- 200,000 audit rows
;WITH n AS (
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
FROM n;
GO

-- Fragment the audit log index --------------------------------------------

-- Delete every fifth row scattered through the table, then reinsert. This
-- splits pages and inflates avg_fragmentation_in_percent on audit_log_idx_ts.
DELETE FROM audit_log WHERE audit_id % 5 = 0;

;WITH n AS (
    SELECT TOP (40000) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS i
    FROM sys.all_objects a CROSS JOIN sys.all_objects b
)
INSERT audit_log (occurred_at, actor, action, payload)
SELECT
    DATEADD(SECOND, -ABS(CHECKSUM(NEWID())) % (60 * 60 * 24 * 7), SYSUTCDATETIME()),
    CONCAT('user', 1 + ABS(CHECKSUM(NEWID())) % 200),
    'view',
    REPLICATE('y', 200)
FROM n;
GO

-- Inflate VLF count on the log -------------------------------------------

-- Quick and dirty: shrink + grow several times in tiny increments.
-- This is exactly what the VLF probe is meant to flag.
DECLARE @i INT = 0;
WHILE @i < 12
BEGIN
    DBCC SHRINKFILE (N'shopdb_log', 8) WITH NO_INFOMSGS;
    ALTER DATABASE shopdb MODIFY FILE (NAME = N'shopdb_log', SIZE = 64MB);
    SET @i += 1;
END
GO

-- Workload to populate DMVs ---------------------------------------------

-- Run a few representative queries so the plan cache and usage stats have
-- something for the probes to find.

-- Slow query: filters by email (no index) and joins items
SELECT TOP 10 o.order_id, o.total_cents, oi.quantity
FROM customers c
JOIN orders o      ON o.customer_id = c.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
WHERE c.email = N'user1234@example.com';

-- Same shape, different param to make it look like a real workload
SELECT TOP 10 o.order_id, o.total_cents, oi.quantity
FROM customers c
JOIN orders o      ON o.customer_id = c.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
WHERE c.email = N'user2222@example.com';

-- Range scan on created_at without a supporting index
SELECT COUNT(*), SUM(total_cents)
FROM orders
WHERE created_at >= DATEADD(DAY, -7, SYSUTCDATETIME());

SELECT COUNT(*), AVG(total_cents)
FROM orders
WHERE created_at >= DATEADD(DAY, -30, SYSUTCDATETIME());

-- A genuinely slow one: cross-join shape that ignores indexes
SELECT TOP 5 c.full_name, p.name, COUNT(*) AS n
FROM customers c, products p
JOIN orders o      ON o.customer_id = c.customer_id
JOIN order_items oi ON oi.order_id = o.order_id AND oi.product_id = p.product_id
GROUP BY c.full_name, p.name
ORDER BY n DESC;

-- A few more reads to give plan_warnings something to chew on
SELECT TOP 100 status, COUNT(*) FROM orders GROUP BY status;
SELECT TOP 50  product_id, SUM(quantity) FROM order_items GROUP BY product_id ORDER BY 2 DESC;
GO

PRINT 'shopdb seeded. Recovery model is FULL with no log backup taken; that is intentional.';

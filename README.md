# sqlserver-diagnostic

Read-only health and performance scanner for SQL Server. Connects with `pyodbc`,
runs a battery of DMV queries, classifies the rows into critical / warning /
info findings, and writes an HTML, Markdown and JSON report.

I built this for myself after running the same `sp_*` scripts and a wall of
queries by hand on a dozen instances. It is not a replacement for sp_Blitz or
First Responder Kit. The point is to get a one-pager I can hand to a developer
or a client without having to explain what `RESOURCE_SEMAPHORE` means.

A sample report generated from the bundled fixture lives at
[`examples/report.html`](examples/report.html). That is what the output looks
like. The same fixture also produces [`report.md`](examples/report.md) and
[`report.json`](examples/report.json).

## Install

```
pip install .
```

You also need the Microsoft ODBC Driver 17 or 18 installed on the host running
the scan. On Debian/Ubuntu:

```
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

If you already have ODBC 17 installed pass `--driver "ODBC Driver 17 for SQL Server"`.

## Run

```
sqlserver-diagnostic \
    --server "prod-sql-01.internal,1433" \
    --database "shopdb" \
    --user "diag_reader" \
    --password "$MSSQL_PASSWORD" \
    --trust-cert \
    --output ./scan-2026-04-19
```

That writes `scan-2026-04-19.html`, `scan-2026-04-19.md`, `scan-2026-04-19.json`.
Open the HTML in a browser, hand the Markdown to whoever asked, keep the JSON
if you want to diff future scans.

The login needs `VIEW SERVER STATE` and read on `msdb` for the backup history
probe. A normal `db_datareader` is not enough.

```sql
CREATE LOGIN diag_reader WITH PASSWORD = '...';
CREATE USER  diag_reader FOR LOGIN diag_reader;
GRANT VIEW SERVER STATE TO diag_reader;
USE msdb;
CREATE USER diag_reader FOR LOGIN diag_reader;
GRANT SELECT ON dbo.backupset TO diag_reader;
```

If a probe fails (missing permission, wrong edition, older version of SQL
Server) the run continues. The error is recorded in a "Probes that failed"
section at the bottom of the report.

## Probe selection

By default every category runs. To restrict:

```
sqlserver-diagnostic ... --categories performance,bottlenecks
```

Available categories: `performance`, `bottlenecks`, `health`, `capacity`.

## What it covers

Performance: top 25 slowest cached statements, plan warnings (implicit
conversions, missing stats, table scans, spills), missing index suggestions
ranked by `improvement_measure`, unused nonclustered indexes that still take
writes, fragmentation in SAMPLED mode for indexes over 1000 pages.

Bottlenecks: top wait stats with the usual benign-wait blacklist, current
blocking chain snapshot, tempdb file count + allocation contention.

Health: per-DB data and log size with the largest table, hours since last full
and log backup per DB, VLF count via `sys.dm_db_log_info`.

Capacity: session counts grouped by login + host, page life expectancy, buffer
cache hit ratio, pending memory grants.

Severity thresholds live in `src/sqlserver_diagnostic/severity.py`. They are
defaults that work for OLTP workloads on small to medium instances. Edit the
file if your environment is different (for instance, PLE thresholds are useless
on systems where you've configured a fixed buffer pool).

## Try it locally without a real instance

There is a Docker compose file under `docker/` that brings up SQL Server 2022
with a small e-commerce schema and seeds enough activity to make most probes
emit real findings. From the repo root:

```
docker compose -f docker/docker-compose.yml up -d
# wait ~30 seconds for the seed to finish
sqlserver-diagnostic -s "localhost,14333" -d shopdb -U sa -P "Diag_pwd_42!" --trust-cert -o /tmp/scan
```

The seed deliberately builds fragmented indexes, queries without supporting
indexes, and skipped log backups. You will get something close to the bundled
example report.

## Known limitations

`plan_warnings.sql` shreds the cached plan XML with a single XPath and only
catches `PlanAffectingConvert`. The fixture pretends the probe also catches
`MissingStatistics`, `TableScan` and `SpillToTempDB`. These are wired into the
classifier and the report renders them, but the actual SQL probe is partial.
This is the next thing on the list.

`tempdb_contention.sql` reads `sys.dm_os_waiting_tasks` once. To know whether
contention is sustained you'd want to sample over a window. Treat the output
as a yes/no.

`vlf_counts.sql` uses `sys.dm_db_log_info` which exists on SQL Server 2016 SP2+
and 2017+. On older versions you'd have to fall back to `DBCC LOGINFO` per DB.
Tested on 2019 and 2022.

The CLI takes a single connection. There is no inventory mode that loops over
a list of servers. For a fleet, run the CLI in a shell loop and merge the JSON
files yourself.

The HTML is single-page and inlines its CSS. No screenshots are embedded, so
you can paste the file into an email or a Slack DM without broken links.

## Tests

```
pip install -e ".[dev]"
pytest
```

The tests run the classifier and the renderers against the bundled fixture.
There is no test that connects to a real database. If you want to validate the
SQL itself, the docker compose seed is the closest thing to a fixture.

## License

MIT. See `LICENSE`.

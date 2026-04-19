from __future__ import annotations

import sys
from pathlib import Path

import click

from . import __version__
from .classifier import classify
from .connection import Connection, ConnectionConfig
from .report import summarise, write_all
from .scanner import PROBES_BY_CATEGORY, scan


# Server metadata probe. Runs regardless of category selection.
_SERVER_INFO_SQL = """
SELECT
    @@SERVERNAME                                  AS server_name,
    DB_NAME()                                     AS database_name,
    CAST(SERVERPROPERTY('ProductVersion') AS NVARCHAR(128))   AS product_version,
    CAST(SERVERPROPERTY('Edition')        AS NVARCHAR(128))   AS edition,
    CAST(SERVERPROPERTY('ProductLevel')   AS NVARCHAR(128))   AS product_level,
    CAST(@@VERSION AS NVARCHAR(512))              AS sql_version
"""


def _fetch_server_info(conn):
    try:
        rows = conn.query(_SERVER_INFO_SQL)
        if not rows:
            return {}
        r = rows[0]
        # Trim the multi-line @@VERSION banner to the first line.
        banner = (r.get("sql_version") or "").splitlines()[0].strip()
        return {
            "server_name":    r.get("server_name") or "",
            "database_name":  r.get("database_name") or "",
            "edition":        r.get("edition") or "",
            "product_version": r.get("product_version") or "",
            "sql_version":    banner,
        }
    except Exception as e:
        # Don't abort the run if the banner probe fails; we can still produce a report.
        return {"server_name": "unknown", "database_name": "", "sql_version": f"(server info unavailable: {e})"}


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--server", "-s", required=True, help="host[,port] or host\\instance")
@click.option("--database", "-d", required=True, help="Database to scan (DMVs are server-scoped; this sets the default context).")
@click.option("--user", "-U", default=None, help="SQL login. If omitted, uses Windows auth (Trusted_Connection).")
@click.option("--password", "-P", default=None, help="Password for --user. You can also pass MSSQL_PASSWORD env var.", envvar="MSSQL_PASSWORD")
@click.option("--driver", default="ODBC Driver 18 for SQL Server", show_default=True)
@click.option("--trust-cert", is_flag=True, help="TrustServerCertificate=yes. Needed with self-signed certs in dev.")
@click.option("--output", "-o", default="report", show_default=True,
              help="Output prefix. Writes <prefix>.html, <prefix>.md, <prefix>.json.")
@click.option("--categories", "-c", default=None,
              help=f"Comma-separated subset of {','.join(PROBES_BY_CATEGORY)}. Default: all.")
@click.version_option(__version__, prog_name="sqlserver-diagnostic")
def main(server, database, user, password, driver, trust_cert, output, categories):
    """Read-only SQL Server health/performance scan.

    Connects, runs a battery of DMV probes, classifies findings, and writes
    HTML/Markdown/JSON reports next to the --output prefix.
    """
    cats = [c.strip() for c in categories.split(",")] if categories else None
    if cats:
        unknown = [c for c in cats if c not in PROBES_BY_CATEGORY]
        if unknown:
            raise click.BadParameter(f"unknown categories: {', '.join(unknown)}")

    cfg = ConnectionConfig(
        server=server, database=database,
        user=user, password=password,
        driver=driver, trust_cert=trust_cert,
    )

    click.echo(f"connecting to {server}/{database} ...", err=True)
    try:
        conn = Connection(cfg)
    except Exception as e:
        click.echo(f"connection failed: {e}", err=True)
        sys.exit(2)

    with conn:
        server_info = _fetch_server_info(conn)
        click.echo(f"  {server_info.get('sql_version', '')}", err=True)
        click.echo("running probes ...", err=True)
        raw = scan(conn, cats)

    errors = raw.pop("_errors", [])
    findings = classify(raw)
    summary = summarise(findings, server_info, errors=errors)

    paths = write_all(summary, Path(output))

    t = summary["totals"]
    by = t["by_severity"]
    click.echo(
        f"{t['finding_count']} findings "
        f"(critical={by.get('critical', 0)}, warning={by.get('warning', 0)}, info={by.get('info', 0)})"
    )
    for kind in ("html", "md", "json"):
        click.echo(f"  {kind}: {paths[kind]}")

    if errors:
        click.echo(f"{len(errors)} probe(s) failed; see the 'Probes that failed' section.", err=True)


if __name__ == "__main__":
    main()

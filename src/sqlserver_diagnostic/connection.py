from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ConnectionConfig:
    server: str
    database: str
    user: str | None = None
    password: str | None = None
    driver: str = "ODBC Driver 18 for SQL Server"
    trust_cert: bool = False

    def to_odbc(self) -> str:
        parts = [
            f"DRIVER={{{self.driver}}}",
            f"SERVER={self.server}",
            f"DATABASE={self.database}",
        ]
        if self.user:
            parts.append(f"UID={self.user}")
            parts.append(f"PWD={self.password or ''}")
        else:
            parts.append("Trusted_Connection=yes")
        if self.trust_cert:
            parts.append("TrustServerCertificate=yes")
        return ";".join(parts)


class Connection:
    def __init__(self, config: ConnectionConfig):
        import pyodbc
        self._conn = pyodbc.connect(config.to_odbc())

    def query(self, sql: str) -> list[dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute(sql)
        cols = [c[0] for c in cur.description] if cur.description else []
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def close(self) -> None:
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

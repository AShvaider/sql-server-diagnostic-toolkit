import json

from sqlserver_diagnostic.classifier import classify
from sqlserver_diagnostic.report import summarise, write_all

from .fixtures import FIXTURE, SERVER_INFO


def _summary():
    return summarise(classify(FIXTURE), SERVER_INFO, errors=FIXTURE.get("_errors"))


def test_summary_has_severity_breakdown():
    s = _summary()
    by = s["totals"]["by_severity"]
    # Fixture is calibrated to produce a non-trivial mix.
    assert by.get("critical", 0) >= 1
    assert by.get("warning", 0) >= 5
    assert s["totals"]["finding_count"] == sum(by.values())


def test_write_all_creates_three_files(tmp_path):
    paths = write_all(_summary(), tmp_path / "scan")
    for kind in ("html", "md", "json"):
        assert paths[kind].exists()
        assert paths[kind].stat().st_size > 0


def test_html_contains_database_name_and_verdict(tmp_path):
    paths = write_all(_summary(), tmp_path / "scan")
    html = paths["html"].read_text(encoding="utf-8")
    assert SERVER_INFO["database_name"] in html
    assert "Action required" in html or "Needs attention" in html or "Healthy" in html


def test_json_round_trip(tmp_path):
    paths = write_all(_summary(), tmp_path / "scan")
    data = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert data["totals"]["finding_count"] >= 1
    # Severity buckets are stable shape.
    assert {"critical", "warning", "info"} <= set(data["by_severity"])


def test_markdown_uses_sql_fence_for_create_index(tmp_path):
    paths = write_all(_summary(), tmp_path / "scan")
    md = paths["md"].read_text(encoding="utf-8")
    if "CREATE NONCLUSTERED" in md:
        assert "```sql" in md, "SQL recommendations should render as SQL fences"

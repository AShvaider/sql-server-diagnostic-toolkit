from sqlserver_diagnostic.classifier import classify
from sqlserver_diagnostic.findings import Severity

from .fixtures import FIXTURE


def test_classify_runs_without_crash():
    findings = classify(FIXTURE)
    assert findings, "fixture should produce at least one finding"


def test_critical_includes_log_backup_gap():
    findings = classify(FIXTURE)
    crit = [f for f in findings if f.severity is Severity.CRITICAL]
    titles = " | ".join(f.title for f in crit)
    assert "Log backup gap" in titles or "No recent full backup" in titles


def test_missing_index_recommendation_is_a_create_index():
    findings = classify(FIXTURE)
    rec = next(f for f in findings if f.id.startswith("perf.missing_idx."))
    assert rec.recommendation.upper().startswith("CREATE NONCLUSTERED INDEX")


def test_healthy_branches_do_not_emit_findings():
    # The classifier intentionally skips "VLF healthy" and "PLE healthy" notes.
    # If you change that, this test should change with it.
    findings = classify(FIXTURE)
    titles = [f.title for f in findings]
    assert not any("healthy" in t.lower() for t in titles), \
        "healthy-branch findings reintroduce noise"


def test_unknown_probe_keys_are_ignored():
    # Sanity: classify shouldn't choke if scan() returns extra keys it doesn't
    # know how to handle.
    bogus = dict(FIXTURE)
    bogus["future_probe_we_havent_written"] = [{"x": 1}]
    classify(bogus)  # must not raise

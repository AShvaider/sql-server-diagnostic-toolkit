"""Regenerate the sample reports under examples/ from the fixture.

Run from the project root:
    python examples/generate.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from sqlserver_diagnostic.classifier import classify
from sqlserver_diagnostic.report import summarise, write_all
from tests.fixtures import FIXTURE, SERVER_INFO


def main():
    errors = FIXTURE.get("_errors", [])
    summary = summarise(classify(FIXTURE), SERVER_INFO, errors=errors)
    paths = write_all(summary, ROOT / "examples" / "report")

    t = summary["totals"]["by_severity"]
    print(f"findings: {summary['totals']['finding_count']} "
          f"(critical={t.get('critical', 0)}, warning={t.get('warning', 0)}, info={t.get('info', 0)})")
    for kind, p in paths.items():
        print(f"{kind}: {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
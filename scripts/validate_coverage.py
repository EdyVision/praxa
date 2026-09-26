"""Fail if line+branch coverage is below the required threshold.

Usage:
  uv run python scripts/validate_coverage.py
  make coverage.check
"""

from __future__ import annotations

import subprocess
import sys

THRESHOLD = 85.0


def main() -> None:
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "coverage",
            "run",
            "-m",
            "pytest",
            "tests",
            "-q",
        ],
        check=False,
    )
    if run.returncode != 0:
        raise SystemExit(run.returncode)

    report = subprocess.run(
        [
            sys.executable,
            "-m",
            "coverage",
            "report",
            f"--fail-under={THRESHOLD:g}",
        ],
        check=False,
    )
    raise SystemExit(report.returncode)


if __name__ == "__main__":
    main()

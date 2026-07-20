#!/usr/bin/env python3
"""machine_summary.py — parse/validate a report's `## Machine Summary` block.

An application report is prose for a human. The optional `## Machine Summary`
block at its end is the same run's key signals in a flat, machine-readable form,
so downstream scripts (analytics, the eval layer, a future baseline remeasure)
read structured data instead of re-parsing prose — the "emit structured once,
never re-read prose with a model" idea. The block is stdlib-parseable
`key: value` lines, no YAML dependency:

    ## Machine Summary

        verdict: CLEAN
        verify_rounds: 1
        claims_traced: 3
        claims_total: 3
        ats_covered: 4
        ats_unverified: 1
        ats_gap: 1
        ledger_preverified: 0

The block is optional: a report without one is fine. A report WITH one must be
well-formed — `--check` enforces that (verdict in CLEAN/FINDINGS, counts
non-negative, claims_traced <= claims_total). Format spec: lifecycle/analytics.md.

Usage:
  machine_summary.py <report.md>            print the parsed block (or note absence)
  machine_summary.py <report.md> --json     parsed block as JSON
  machine_summary.py <report.md> --check     exit 1 if a present block is invalid

Exit codes: 0 valid/absent · 1 present-but-invalid · 2 usage/IO error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HEADING = re.compile(r"^##\s+Machine Summary\s*$", re.IGNORECASE)
NEXT_HEADING = re.compile(r"^#{1,6}\s")
FIELD = re.compile(r"^\s*([a-z_]+):\s*(.+?)\s*$")

REQUIRED = ("verdict", "claims_traced", "claims_total")
VERDICTS = ("CLEAN", "FINDINGS")
COUNT_FIELDS = (
    "verify_rounds", "claims_traced", "claims_total",
    "ats_covered", "ats_unverified", "ats_gap", "ledger_preverified",
)


def parse(text: str):
    """Return the Machine Summary as a dict (ints where numeric), or None."""
    lines = text.splitlines()
    i = 0
    while i < len(lines) and not HEADING.match(lines[i]):
        i += 1
    if i >= len(lines):
        return None
    fields = {}
    for line in lines[i + 1:]:
        if NEXT_HEADING.match(line):
            break
        m = FIELD.match(line)
        if not m:
            continue
        key, raw = m.group(1), m.group(2)
        fields[key] = int(raw) if re.fullmatch(r"-?\d+", raw) else raw
    return fields or None


def validate(summary: dict) -> list[str]:
    errors = []
    for key in REQUIRED:
        if key not in summary:
            errors.append(f"missing required field: {key}")
    if "verdict" in summary and summary["verdict"] not in VERDICTS:
        errors.append(f"verdict must be one of {VERDICTS}, got {summary['verdict']!r}")
    for key in COUNT_FIELDS:
        if key in summary:
            v = summary[key]
            if not isinstance(v, int) or v < 0:
                errors.append(f"{key} must be a non-negative integer, got {v!r}")
    if isinstance(summary.get("claims_traced"), int) and isinstance(summary.get("claims_total"), int):
        if summary["claims_traced"] > summary["claims_total"]:
            errors.append(
                f"claims_traced ({summary['claims_traced']}) exceeds claims_total ({summary['claims_total']})")
    return errors


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("report", help="path to an application report .md")
    ap.add_argument("--check", action="store_true", help="exit 1 if a present block is invalid")
    ap.add_argument("--json", action="store_true", help="print the parsed block as JSON")
    args = ap.parse_args(argv)

    path = Path(args.report)
    if not path.is_file():
        print(f"machine_summary: not found: {path}", file=sys.stderr)
        return 2

    summary = parse(path.read_text(encoding="utf-8"))
    if summary is None:
        if args.json:
            print("null")
        else:
            print(f"machine_summary: no `## Machine Summary` block in {path}", file=sys.stderr)
        return 0  # optional artifact

    if args.json:
        print(json.dumps(summary, indent=1, sort_keys=True))

    errors = validate(summary)
    if errors:
        for e in errors:
            print(f"{path}: {e}", file=sys.stderr)
        print(f"machine_summary: {len(errors)} error(s)", file=sys.stderr)
        return 1 if args.check else 0
    print(f"machine_summary: valid block ({len(summary)} fields)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

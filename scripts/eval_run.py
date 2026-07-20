#!/usr/bin/env python3
"""eval_run.py — Tier-1 golden-fixture harness (zero-LLM, deterministic).

Dossier's quality is guarded live, per run, by the application-verifier gate —
but nothing protects against a *regression*: an edit that silently changes what
the deterministic pipeline emits. This harness is the regression net for the
zero-LLM half. Each fixture under `eval/fixtures/<case>/` is a tiny, synthetic
job-folder (no PII); the harness runs the deterministic scripts over it and
asserts their output is byte-identical to a blessed `expected/` snapshot.

It catches: a changed bucket label in ats_coverage, a reworded trace_check
result, a master_diff format shift — and drift in the trace-file *contract* the
writer agents must emit. When a change is intentional, `--bless` rewrites the
snapshots so the diff is one reviewable step.

The LLM half (agent quality) is Tier 2 — run on demand, not here.

Usage:
  eval_run.py                 check every fixture (exit 1 on any drift)
  eval_run.py --bless         re-record every fixture's expected/ snapshot
  eval_run.py --fixtures DIR  fixtures root (default: eval/fixtures)

Exit codes: 0 clean · 1 drift found · 2 no fixtures / usage error.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# Each check is one deterministic script invoked with fixture-relative paths, so
# the paths echoed in its output stay location-independent across machines.
Check = __import__("collections").namedtuple("Check", "name argv")

CHECKS = [
    Check("ats_coverage", ["ats_coverage.py", "jd.md", "--kb-dir", "knowledge"]),
    Check("trace_check", ["trace_check.py", "cv_trace.md", "cover_trace.md", "--kb-dir", "knowledge"]),
    Check("master_diff", ["master_diff.py", "cv.md", "--master", "master_cv.md"]),
]

EXPECTED_DIR = "expected"


@dataclass(frozen=True)
class Diff:
    fixture: str
    check: str
    expected: str
    actual: str


def render(exit_code: int, stdout: str) -> str:
    """Golden snapshot format: exit code on line 1, then the captured stdout."""
    return f"exit {exit_code}\n{stdout}"


def discover_fixtures(fixtures_root) -> list[Path]:
    root = Path(fixtures_root)
    if not root.is_dir():
        return []
    return sorted(p for p in root.iterdir() if p.is_dir() and (p / "jd.md").is_file())


def subprocess_runner(scripts_dir):
    """Build a runner that invokes a check's script with cwd=fixture_dir."""
    scripts_dir = Path(scripts_dir)

    def run(fixture_dir, check: Check):
        script = scripts_dir / check.argv[0]
        proc = subprocess.run(
            [sys.executable, str(script), *check.argv[1:]],
            cwd=str(fixture_dir),
            capture_output=True,
            text=True,
        )
        return proc.returncode, proc.stdout

    return run


def _expected_path(fixture_dir: Path, check: Check) -> Path:
    return Path(fixture_dir) / EXPECTED_DIR / f"{check.name}.txt"


def compare_fixture(fixture_dir, checks, run_fn) -> list[Diff]:
    fixture_dir = Path(fixture_dir)
    diffs = []
    for check in checks:
        exit_code, stdout = run_fn(fixture_dir, check)
        actual = render(exit_code, stdout)
        ep = _expected_path(fixture_dir, check)
        expected = ep.read_text(encoding="utf-8") if ep.is_file() else "<no expected snapshot>\n"
        if actual != expected:
            diffs.append(Diff(fixture_dir.name, check.name, expected, actual))
    return diffs


def bless_fixture(fixture_dir, checks, run_fn) -> None:
    fixture_dir = Path(fixture_dir)
    (fixture_dir / EXPECTED_DIR).mkdir(exist_ok=True)
    for check in checks:
        exit_code, stdout = run_fn(fixture_dir, check)
        _expected_path(fixture_dir, check).write_text(render(exit_code, stdout), encoding="utf-8")


def _format_drift(d: Diff) -> str:
    return (
        f"DRIFT {d.fixture}/{d.check}\n"
        f"  --- expected\n" + "".join(f"  | {l}\n" for l in d.expected.splitlines()) +
        f"  +++ actual\n" + "".join(f"  | {l}\n" for l in d.actual.splitlines())
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fixtures", default="eval/fixtures", help="fixtures root (default: eval/fixtures)")
    ap.add_argument("--bless", action="store_true", help="re-record expected/ snapshots")
    args = ap.parse_args(argv)

    scripts_dir = Path(__file__).resolve().parent
    run_fn = subprocess_runner(scripts_dir)

    fixtures = discover_fixtures(args.fixtures)
    if not fixtures:
        print(f"eval_run: no fixtures under {args.fixtures}", file=sys.stderr)
        return 2

    if args.bless:
        for fx in fixtures:
            bless_fixture(fx, CHECKS, run_fn)
        print(f"eval_run: blessed {len(fixtures)} fixture(s)", file=sys.stderr)
        return 0

    all_diffs = []
    for fx in fixtures:
        all_diffs.extend(compare_fixture(fx, CHECKS, run_fn))

    if not all_diffs:
        print(f"eval_run: pass ({len(fixtures)} fixture(s), {len(CHECKS)} checks each)", file=sys.stderr)
        return 0

    for d in all_diffs:
        print(_format_drift(d), file=sys.stderr)
    print(f"eval_run: {len(all_diffs)} drift(s) — re-bless with --bless if intended", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

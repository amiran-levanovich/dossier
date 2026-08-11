#!/usr/bin/env python3
"""eval_run.py — Tier-1 golden-fixture harness (zero-LLM, deterministic).

Dossier's quality is guarded live, per run, by the application-verifier gate —
but nothing protects against a *regression*: an edit that silently changes what
the deterministic pipeline emits. This harness is the regression net for the
zero-LLM half. Each fixture under `eval/fixtures/<case>/` is a tiny, synthetic
job-folder (no PII); the harness runs the deterministic scripts over it and
asserts their output is byte-identical to a blessed `expected/` snapshot.

It covers the v4 deterministic half end to end: the slot map `cv.py map` hands
the writer, the assembly `cv.py build` renders from an edit plan, the alias swap
applied after the verbatim self-test, and the three-way coverage report. So it
catches a renamed slot id, a rendering change the verbatim counts would hide, a
swap that stopped firing, a changed bucket label — and, on the rejection
fixture, a build that starts writing a file it must refuse to write.

When a change is intentional, `--bless` rewrites the snapshots so the diff is
one reviewable step.

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

@dataclass(frozen=True)
class Check:
    """One deterministic script invoked with fixture-relative paths, so the paths
    echoed in its output stay location-independent across machines.

    `artifacts` are files the script writes, whose content joins the snapshot.
    A report saying "verbatim: 9/9" does not prove what landed in `cv.md`, and a
    rejected build's whole contract is that the file is *absent* — neither is
    visible on stdout, so both are pinned here.
    """
    name: str
    argv: list[str]
    artifacts: tuple[str, ...] = ()


CHECKS = [
    Check("cv_map", ["cv.py", "map", "master_cv.md"]),
    Check("cv_build", ["cv.py", "build", "plan.json", "--exemplar", "master_cv.md",
                       "--out-dir", "out"],
          artifacts=("out/cv.md",)),
    Check("cv_build_aliased", ["cv.py", "build", "plan.json", "--exemplar", "master_cv.md",
                               "--out-dir", "out-aliased", "--posting", "jd.md"],
          artifacts=("out-aliased/cv.md", "out-aliased/alias_log.md")),
    Check("ats_coverage", ["ats_coverage.py", "jd.md", "--exemplar", "master_cv.md",
                           "--bank", "story_bank.md"]),
]

EXPECTED_DIR = "expected"
MISSING = "<not written>"


@dataclass(frozen=True)
class Diff:
    fixture: str
    check: str
    expected: str
    actual: str


def render(exit_code: int, stdout: str, artifacts=()) -> str:
    """Golden snapshot: exit code, the captured stdout, then each artifact.

    An artifact the script did not write is recorded as absent rather than
    skipped, so "this build wrote no file" is an assertion and not a silence.
    """
    out = f"exit {exit_code}\n{stdout}"
    for label, content in artifacts:
        out += f"\n--- {label} ---\n{MISSING if content is None else content}"
    return out


def _clear_artifacts(fixture_dir: Path, check: Check) -> None:
    """Remove a previous run's outputs before running.

    Without this a rejected build would inherit the last successful run's
    `cv.md` and its snapshot would record a file the run never wrote — which is
    precisely the atomicity failure the fixture exists to catch.
    """
    for rel in check.artifacts:
        path = fixture_dir / rel
        if path.is_file():
            path.unlink()


def _read_artifacts(fixture_dir: Path, check: Check) -> list[tuple[str, str | None]]:
    out = []
    for rel in check.artifacts:
        path = fixture_dir / rel
        out.append((rel, path.read_text(encoding="utf-8") if path.is_file() else None))
    return out


def _run(fixture_dir: Path, check: Check, run_fn) -> str:
    _clear_artifacts(fixture_dir, check)
    exit_code, stdout = run_fn(fixture_dir, check)
    return render(exit_code, stdout, _read_artifacts(fixture_dir, check))


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
        actual = _run(fixture_dir, check, run_fn)
        ep = _expected_path(fixture_dir, check)
        expected = ep.read_text(encoding="utf-8") if ep.is_file() else "<no expected snapshot>\n"
        if actual != expected:
            diffs.append(Diff(fixture_dir.name, check.name, expected, actual))
    return diffs


def bless_fixture(fixture_dir, checks, run_fn) -> None:
    fixture_dir = Path(fixture_dir)
    (fixture_dir / EXPECTED_DIR).mkdir(exist_ok=True)
    for check in checks:
        _expected_path(fixture_dir, check).write_text(
            _run(fixture_dir, check, run_fn), encoding="utf-8")


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

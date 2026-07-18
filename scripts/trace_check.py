#!/usr/bin/env python3
"""Trace-map pre-check — a deterministic gate before application-verifier.

Every line in a trace file (cv_trace.md / cover_trace.md) maps one claim to a
source, in the format from core/tailoring_method.md:

    - "<claim, abbreviated>" → roles/acme.md#achievements
    - "<...>" → skills.md#databases
    - "<...>" → overrides.md (user-directed, 2026-07-07)

This script answers only the bookkeeping half of verification: does every trace
target point at a file that exists and, when an #anchor is given, a heading that
exists? It does NOT judge whether the source honestly supports the claim — that
judgment is the application-verifier's job. Running this first lets the verifier
spend its context on judgment instead of chasing dangling references.

KB targets (roles/*.md, skills.md, ...) resolve against --kb-dir. The special
target `overrides.md` resolves against --app-dir (the application folder) and is
existence-checked only; overrides are user-directed and need no anchor.

Exit code: 0 if every target resolves, 1 if any dangle or any line is malformed,
2 on a usage/IO error. Nonzero is a gate failure — fix before the verifier runs.
"""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402


class TraceLine:
    def __init__(self, lineno: int, claim: str, path: str, anchor: str | None):
        self.lineno = lineno
        self.claim = claim
        self.path = path
        self.anchor = anchor


def parse_trace_file(text: str):
    """Yield (TraceLine | None, raw) for every bullet that looks like a trace.

    A None TraceLine flags a bullet that has claim text but no parseable target.
    Non-bullet lines (headings, blanks, prose) are skipped entirely.
    """
    for i, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped.startswith("- "):
            continue
        claim = stripped[2:].strip()
        # Split at the LAST arrow — the claim text itself may contain one
        # ("migrated Redis → Kafka"), but the target separator is always the
        # rightmost arrow on the line.
        idx, arrow = max((claim.rfind(a), a) for a in _common.TRACE_ARROWS)
        if idx < 0:
            # A bullet with a quoted claim but no arrow is a malformed trace
            # line; a plain prose bullet (no quotes) is just prose — skip it.
            if claim.startswith('"') or claim.startswith("“"):
                yield None, (i, claim)
            continue
        left = claim[:idx]
        target = claim[idx + len(arrow):].strip()
        # target is `path[#anchor]` optionally followed by ` (note)`.
        target = target.split("(")[0].strip()
        if not target:
            yield None, (i, left.strip())
            continue
        path, _, anchor = target.partition("#")
        yield TraceLine(i, left.strip(), path.strip(), anchor.strip() or None), None


def check_file(trace_path: Path, kb_dir: Path, app_dir: Path):
    text = _common.read_text(trace_path)
    findings = []
    n_lines = 0
    n_ok = 0
    heading_cache: dict[Path, set[str]] = {}

    for tline, malformed in parse_trace_file(text):
        if malformed is not None:
            lineno, claim = malformed
            findings.append((lineno, "MALFORMED", claim, "no `→ target` on this trace line"))
            continue
        n_lines += 1
        is_override = tline.path == "overrides.md"
        base = app_dir if is_override else kb_dir
        target_file = base / tline.path

        if not target_file.is_file():
            findings.append(
                (tline.lineno, "FILE", tline.claim, f"source file not found: {tline.path}")
            )
            continue
        if tline.anchor and not is_override:
            if target_file not in heading_cache:
                heading_cache[target_file] = _common.heading_slugs(_common.read_text(target_file))
            slugs = heading_cache[target_file]
            if tline.anchor not in slugs:
                hint = difflib.get_close_matches(tline.anchor, slugs, n=1)
                suffix = f"; did you mean #{hint[0]}" if hint else ""
                findings.append(
                    (
                        tline.lineno,
                        "ANCHOR",
                        tline.claim,
                        f"no heading in {tline.path} slugs to #{tline.anchor}{suffix}",
                    )
                )
                continue
        n_ok += 1
    return n_lines, n_ok, findings


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("trace_files", nargs="+", help="cv_trace.md / cover_trace.md paths")
    ap.add_argument("--kb-dir", required=True, help="path to the knowledge/ directory")
    ap.add_argument(
        "--app-dir",
        default=None,
        help="application folder (for overrides.md); defaults to each trace file's dir",
    )
    args = ap.parse_args(argv)

    kb_dir = Path(args.kb_dir)
    if not kb_dir.is_dir():
        print(f"error: --kb-dir not found: {kb_dir}", file=sys.stderr)
        return 2

    total_dangling = 0
    for tf in args.trace_files:
        tf_path = Path(tf)
        if not tf_path.is_file():
            print(f"TRACE-CHECK {tf}\n  error: file not found", file=sys.stderr)
            total_dangling += 1
            continue
        app_dir = Path(args.app_dir) if args.app_dir else tf_path.parent
        n_lines, n_ok, findings = check_file(tf_path, kb_dir, app_dir)
        bad = len(findings)
        total_dangling += bad
        print(f"TRACE-CHECK {tf}")
        print(f"  lines: {n_lines}   ok: {n_ok}   problems: {bad}")
        for lineno, kind, claim, msg in findings:
            short = (claim[:60] + "…") if len(claim) > 61 else claim
            print(f"  [{kind}] line {lineno}: {short} — {msg}")

    if total_dangling:
        print(f"\nRESULT: FAIL — {total_dangling} unresolved trace target(s)")
        return 1
    print("\nRESULT: PASS — every trace target resolves to a real file and anchor")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

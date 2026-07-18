#!/usr/bin/env python3
"""Verified-claim ledger — memoize claim judgments across applications.

The application-verifier's expensive work is judging whether a KB source
honestly supports a claim. That judgment is stable as long as neither side
moves: the exact same claim text citing the exact same section of an unchanged
KB file was already judged sound in a previous CLEAN round. This script is the
filesystem memo of those judgments:

    claim_ledger.py record cv_trace.md cover_trace.md --kb-dir knowledge/
    claim_ledger.py check  cv_trace.md cover_trace.md --kb-dir knowledge/

`record` runs after (and only after) a CLEAN verdict: each resolved KB-sourced
trace line is stored keyed by (claim text, resolved source path, normalized
anchor) with a content hash of the source file. `check` runs before the
verifier: exact matches whose source file is byte-identical are reported
PRE-VERIFIED; the verifier judges only the NEW/changed remainder.

Invalidation is automatic, never manual: edit the claim wording, the cited
anchor, or the KB file itself and the entry simply stops matching.
Application-local sources (jd.md, notes.md, overrides.md) are never recorded —
they are per-application by definition, so a past CLEAN cannot carry over.

The ledger lives at the job-folder root (default: `.claim_ledger.json` beside
`knowledge/`), shared across that search's applications. Like every script
here it is advisory and degrades gracefully: missing or corrupt ledger means
"everything is NEW", exit 0. Exit 2 only on unusable inputs (--kb-dir gone).
The judgment itself stays with the verifier — this only tells it where a past
judgment still applies verbatim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402
import trace_check  # noqa: E402

LEDGER_NAME = ".claim_ledger.json"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def resolve_kb_target(tline, kb_dir: Path):
    """Resolve a trace line to a (key, source file) pair, or classify why not.

    Returns (status, key, target_file): status is 'kb' (resolvable KB source),
    'app-local' (never ledgered), or 'unresolved' (file missing).
    """
    if tline.path in trace_check.APP_LOCAL:
        return "app-local", None, None
    rel = tline.path
    prefix = kb_dir.name + "/"
    if rel.startswith(prefix):
        rel = rel[len(prefix):]
    target_file = kb_dir / rel
    if not target_file.is_file():
        return "unresolved", None, None
    anchor = _common.normalize_anchor(tline.anchor) if tline.anchor else ""
    key = _sha256("\x00".join((tline.claim, rel, anchor)))
    return "kb", key, target_file


def load_ledger(path: Path) -> dict:
    """Load the ledger, degrading to empty on a missing or corrupt file."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = data.get("entries")
        return entries if isinstance(entries, dict) else {}
    except (OSError, ValueError):
        return {}


def save_ledger(path: Path, entries: dict) -> None:
    payload = {"version": 1, "entries": entries}
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def record(trace_files, kb_dir: Path, ledger_path: Path) -> int:
    entries = load_ledger(ledger_path)
    for tf in trace_files:
        n_rec = n_local = n_unres = 0
        for tline, malformed in trace_check.parse_trace_file(_common.read_text(tf)):
            if malformed is not None:
                n_unres += 1
                continue
            status, key, target_file = resolve_kb_target(tline, kb_dir)
            if status == "app-local":
                n_local += 1
            elif status == "unresolved":
                n_unres += 1
            else:
                entries[key] = {
                    "claim": tline.claim,
                    "source": f"{target_file.relative_to(kb_dir)}"
                    + (f"#{tline.anchor}" if tline.anchor else ""),
                    "source_hash": _sha256(_common.read_text(target_file)),
                    "recorded": date.today().isoformat(),
                }
                n_rec += 1
        print(f"CLAIM-LEDGER record {tf}")
        print(
            f"  recorded: {n_rec}   skipped (app-local): {n_local}   "
            f"skipped (unresolved): {n_unres}"
        )
    save_ledger(ledger_path, entries)
    print(f"ledger: {ledger_path} ({len(entries)} entries)")
    return 0


def check(trace_files, kb_dir: Path, ledger_path: Path) -> int:
    entries = load_ledger(ledger_path)
    hash_cache: dict[Path, str] = {}
    total_pre = total_new = 0
    for tf in trace_files:
        pre = 0
        new: list[tuple[int, str, str]] = []
        for tline, malformed in trace_check.parse_trace_file(_common.read_text(tf)):
            if malformed is not None:
                lineno, claim = malformed
                new.append((lineno, claim, "malformed trace line"))
                continue
            status, key, target_file = resolve_kb_target(tline, kb_dir)
            if status == "app-local":
                new.append((tline.lineno, tline.claim, "app-local source (per-application)"))
            elif status == "unresolved":
                new.append((tline.lineno, tline.claim, f"unresolved source: {tline.path}"))
            elif key not in entries:
                new.append((tline.lineno, tline.claim, "not in ledger"))
            else:
                if target_file not in hash_cache:
                    hash_cache[target_file] = _sha256(_common.read_text(target_file))
                if hash_cache[target_file] == entries[key]["source_hash"]:
                    pre += 1
                else:
                    new.append(
                        (tline.lineno, tline.claim, "source changed since last CLEAN")
                    )
        total_pre += pre
        total_new += len(new)
        print(f"CLAIM-LEDGER check {tf}")
        print(f"  pre-verified: {pre}   new: {len(new)}")
        for lineno, claim, why in new:
            short = (claim[:60] + "…") if len(claim) > 61 else claim
            print(f"  [NEW] line {lineno}: {short} — {why}")
    if total_pre or total_new:
        print(
            f"\nRESULT: {total_pre}/{total_pre + total_new} pre-verified — "
            f"the verifier judges only the {total_new} NEW claim(s)"
        )
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("command", choices=("record", "check"))
    ap.add_argument("trace_files", nargs="+", help="cv_trace.md / cover_trace.md paths")
    ap.add_argument("--kb-dir", required=True, help="path to the knowledge/ directory")
    ap.add_argument(
        "--ledger",
        default=None,
        help=f"ledger file (default: {LEDGER_NAME} beside the knowledge/ directory)",
    )
    args = ap.parse_args(argv)

    kb_dir = Path(args.kb_dir)
    if not kb_dir.is_dir():
        print(f"error: --kb-dir not found: {kb_dir}", file=sys.stderr)
        return 2
    ledger_path = Path(args.ledger) if args.ledger else kb_dir.resolve().parent / LEDGER_NAME

    if args.command == "record":
        return record(args.trace_files, kb_dir, ledger_path)
    return check(args.trace_files, kb_dir, ledger_path)


if __name__ == "__main__":
    raise SystemExit(main())

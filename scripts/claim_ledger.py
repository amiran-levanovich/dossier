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

Exemplar documents (v2.5.0): `record --document master_cv.md` additionally
stores a verified document's content hash on CLEAN; `check --document …`
answers whether the file is still byte-identical to the one that was verified
(VERIFIED / CHANGED / not recorded). The verifier's VERBATIM shortcut for
master-derived lines (see master_diff.py) is only valid while the document
checks VERIFIED. Documents are keyed by basename — the exemplars live at the
job-folder root beside the ledger.

The ledger lives at the job-folder root (default: `.claim_ledger.json` beside
`knowledge/`), shared across that search's applications. Like every script
here it is advisory and degrades gracefully: missing or corrupt ledger means
"everything is NEW", exit 0. Exit 2 only on unusable inputs (--kb-dir gone,
nothing to process). The judgment itself stays with the verifier — this only
tells it where a past judgment still applies verbatim.
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


def load_ledger(path: Path) -> tuple[dict, dict]:
    """Load (entries, documents), degrading to empty on missing/corrupt files.

    A v2.4.0 ledger has no "documents" key — that degrades to "no document
    recorded", never an error.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}, {}
    entries = data.get("entries")
    documents = data.get("documents")
    return (
        entries if isinstance(entries, dict) else {},
        documents if isinstance(documents, dict) else {},
    )


def save_ledger(path: Path, entries: dict, documents: dict) -> None:
    payload = {"version": 1, "entries": entries, "documents": documents}
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def record(trace_files, doc_files, kb_dir: Path, ledger_path: Path) -> int:
    entries, documents = load_ledger(ledger_path)
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
    for doc in doc_files:
        doc_path = Path(doc)
        if not doc_path.is_file():
            print(f"  document {doc_path.name}: not found — not recorded")
            continue
        documents[doc_path.name] = {
            "hash": _sha256(_common.read_text(doc_path)),
            "recorded": date.today().isoformat(),
        }
        print(f"  document {doc_path.name}: recorded")
    save_ledger(ledger_path, entries, documents)
    print(f"ledger: {ledger_path} ({len(entries)} entries, {len(documents)} documents)")
    return 0


def check(trace_files, doc_files, kb_dir: Path, ledger_path: Path) -> int:
    entries, documents = load_ledger(ledger_path)
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
    for doc in doc_files:
        doc_path = Path(doc)
        rec = documents.get(doc_path.name)
        if rec is None:
            print(f"document {doc_path.name}: not recorded — full judgment applies")
        elif not doc_path.is_file():
            print(f"document {doc_path.name}: file missing — full judgment applies")
        elif _sha256(_common.read_text(doc_path)) == rec["hash"]:
            print(f"document {doc_path.name}: VERIFIED (recorded {rec['recorded']})")
        else:
            print(
                f"document {doc_path.name}: CHANGED since verification — "
                "re-verify before using the verbatim shortcut"
            )
    if total_pre or total_new:
        print(
            f"\nRESULT: {total_pre}/{total_pre + total_new} pre-verified — "
            f"the verifier judges only the {total_new} NEW claim(s)"
        )
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("command", choices=("record", "check"))
    ap.add_argument("trace_files", nargs="*", help="cv_trace.md / cover_trace.md paths")
    ap.add_argument("--kb-dir", required=True, help="path to the knowledge/ directory")
    ap.add_argument(
        "--document",
        action="append",
        default=[],
        help="exemplar document (master_cv.md / cover_frame.md) to record/check by content hash",
    )
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
    if not args.trace_files and not args.document:
        print("error: nothing to process — give trace files and/or --document", file=sys.stderr)
        return 2
    ledger_path = Path(args.ledger) if args.ledger else kb_dir.resolve().parent / LEDGER_NAME

    if args.command == "record":
        return record(args.trace_files, args.document, kb_dir, ledger_path)
    return check(args.trace_files, args.document, kb_dir, ledger_path)


if __name__ == "__main__":
    raise SystemExit(main())

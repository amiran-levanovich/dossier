#!/usr/bin/env python3
"""Master-CV subset check — prove which cv.md lines are verbatim from master.

With a verified `master_cv.md` (see lifecycle/master_documents.md), cv-tailor's
contract is subtract + bounded edits: dropping and reordering master bullets is
always safe (no new claims can appear), while anything reworded is new content
that must be judged. This script draws that line mechanically:

    master_diff.py cv.md --master master_cv.md

Every content-bearing line of cv.md (headings and blanks skipped) is either
VERBATIM — present in the master after whitespace/bullet-marker normalisation —
or CHANGED. There is deliberately **no semantic tolerance**: a 95%-similar
rewording is CHANGED, because "almost the same claim" is exactly what needs
judgment. CHANGED lines are reported with the closest master line (difflib) as
a hint so the verifier sees what was edited, or "no close match" for genuinely
new content.

The verifier may skip claim judgment on VERBATIM lines only while the master
itself is hash-valid (`claim_ledger.py check --document master_cv.md`) — this
script proves subset membership, the ledger proves the master is still the one
that was verified.

Advisory, never a gate: exit 0 even with changes; a missing master means every
line is CHANGED (full judgment — the pre-master pipeline). Exit 2 only when
cv.md itself can't be read.
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402


def normalize_line(line: str) -> str:
    """Whitespace/bullet-marker normalisation — the only tolerance we allow."""
    text = line.strip()
    text = re.sub(r"^[-*+]\s+", "", text)
    return re.sub(r"\s+", " ", text)


def content_lines(text: str):
    """Yield (lineno, normalized) for every content-bearing line."""
    for i, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        yield i, normalize_line(raw)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cv", help="path to the tailored cv.md")
    ap.add_argument("--master", required=True, help="path to master_cv.md")
    args = ap.parse_args(argv)

    cv_path = Path(args.cv)
    if not cv_path.is_file():
        print(f"error: cv not found: {cv_path}", file=sys.stderr)
        return 2

    master_text = _common.read_text(args.master)
    master_lines = list(content_lines(master_text))
    master_set = {norm for _, norm in master_lines}

    n_verbatim = 0
    changed: list[tuple[int, str]] = []
    for lineno, norm in content_lines(cv_path.read_text(encoding="utf-8")):
        if norm in master_set:
            n_verbatim += 1
        else:
            changed.append((lineno, norm))

    total = n_verbatim + len(changed)
    print(f"MASTER-DIFF {args.cv} vs {args.master}")
    if not master_lines:
        print("  no master content — every line is new; full judgment applies")
    print(f"  lines: {total}   verbatim: {n_verbatim}   changed: {len(changed)}")
    for lineno, norm in changed:
        short = (norm[:70] + "…") if len(norm) > 71 else norm
        hint = difflib.get_close_matches(norm, sorted(master_set), n=1, cutoff=0.5)
        suffix = f'closest master line: "{hint[0]}"' if hint else "no close match in master"
        print(f'  [CHANGED] line {lineno}: {short} — {suffix}')
    if changed:
        print(
            f"\nRESULT: {n_verbatim}/{total} verbatim — "
            f"the verifier judges the {len(changed)} changed line(s)"
        )
    else:
        print(f"\nRESULT: {n_verbatim}/{total} verbatim — pure subtract/reorder of the master")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""ATS keyword coverage — the deterministic half of standards/ats_rules.md.

Reads the `## ATS keywords` block from an application's jd.md and reports, for
each keyword, whether a knowledge-base file names it. Matching is literal and
whole-token (case-insensitive) — exactly what an ATS does — with no language
understanding, so this replaces the inline LLM keyword sweep entirely.

Buckets, per ats_rules.md's covered / verifiable-gap / real-gap split:
  COVERED     — named on a verified KB line.
  UNVERIFIED  — named only on an `[unverified]` line (kb_schema.md): verify or drop.
  GAP         — not found in the KB at all.

This is advisory, not a gate: gaps are a normal, expected input to the
mini-interview / override decisions the orchestrator makes. Exit code is 0
unless the inputs can't be read (2). The `[unverified]` test is line-local — a
keyword whose only mentions sit on `[unverified]` lines is reported UNVERIFIED;
confirm borderline cases against the entry in the file.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402

# lessons.md is orchestrator-only context, never a source of CV claims
# (kb_schema.md), so a keyword found only there does not count as covered.
EXCLUDE_FILES = {"lessons.md", "INDEX.md", "interview_progress.md", "goals.md"}


def extract_keywords(jd_text: str) -> list[str]:
    """Pull the keyword list from the `## ATS keywords` section of jd.md."""
    lines = jd_text.splitlines()
    out: list[str] = []
    in_block = False
    for line in lines:
        if re.match(r"^#{1,6}\s", line):
            in_block = bool(re.match(r"^#{1,6}\s+ATS keywords\s*$", line, re.IGNORECASE))
            continue
        if not in_block:
            continue
        item = line.strip().lstrip("-*").strip()
        if not item:
            continue
        # A line may hold several comma-separated keywords.
        for kw in item.split(","):
            kw = kw.strip().strip("`")
            if kw and kw not in out:
                out.append(kw)
    return out


def kb_files(kb_dir: Path) -> list[Path]:
    return sorted(
        p
        for p in kb_dir.rglob("*.md")
        if p.name not in EXCLUDE_FILES
    )


def classify(keyword: str, files: list[Path]) -> tuple[str, list[str]]:
    pat = _common.keyword_pattern(keyword)
    verified_hits: list[str] = []
    unverified_hits: list[str] = []
    for f in files:
        rel = f.name if f.parent.name in ("", "knowledge") else f"{f.parent.name}/{f.name}"
        matched_verified = False
        matched_unverified = False
        for line in _common.read_text(f).splitlines():
            if pat.search(line):
                if "[unverified]" in line.lower():
                    matched_unverified = True
                else:
                    matched_verified = True
        if matched_verified:
            verified_hits.append(rel)
        elif matched_unverified:
            unverified_hits.append(rel)
    if verified_hits:
        return "COVERED", verified_hits
    if unverified_hits:
        return "UNVERIFIED", unverified_hits
    return "GAP", []


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("jd", help="path to the application's jd.md")
    ap.add_argument("--kb-dir", required=True, help="path to the knowledge/ directory")
    args = ap.parse_args(argv)

    jd_text = _common.read_text(args.jd)
    if not jd_text:
        print(f"error: jd not found or empty: {args.jd}", file=sys.stderr)
        return 2
    kb_dir = Path(args.kb_dir)
    if not kb_dir.is_dir():
        print(f"error: --kb-dir not found: {kb_dir}", file=sys.stderr)
        return 2

    keywords = extract_keywords(jd_text)
    files = kb_files(kb_dir)

    results = [(kw, *classify(kw, files)) for kw in keywords]
    covered = [r for r in results if r[1] == "COVERED"]
    unverified = [r for r in results if r[1] == "UNVERIFIED"]
    gaps = [r for r in results if r[1] == "GAP"]

    print(f"ATS-COVERAGE  jd={args.jd}  kb={kb_dir}")
    if not keywords:
        print("  no keywords found under a `## ATS keywords` heading in jd.md")
        return 0
    print(
        f"  keywords: {len(keywords)}   covered: {len(covered)}   "
        f"unverified: {len(unverified)}   gap: {len(gaps)}"
    )
    for kw, _, hits in covered:
        print(f"  [COVERED]    {kw} — {', '.join(hits)}")
    for kw, _, hits in unverified:
        print(f"  [UNVERIFIED] {kw} — {', '.join(hits)}  (only on [unverified] lines — verify or drop)")
    for kw, _, _ in gaps:
        print(f"  [GAP]        {kw} — not found in KB (mini-interview, or real gap → jd.md ## Fit)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

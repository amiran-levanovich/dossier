#!/usr/bin/env python3
"""ATS keyword coverage — the deterministic half of standards/ats_rules.md.

Reads the `## ATS keywords` block from an application's jd.md and buckets each
keyword against the two artifacts that hold the candidate's facts: the exemplar
(`master_cv.md`) and the story bank. Matching is literal and whole-token
(case-insensitive) — exactly what an ATS does — with no language understanding,
so this replaces the inline LLM keyword sweep entirely.

Three buckets, carrying the distinction the candidate acts on (ADR-0006):
  COVERED     — named in the exemplar, so trimming can already use it.
  PROMOTABLE  — in the story bank but not the exemplar: a promotion decision,
                not a gap. The bank is wider than the exemplar by design, and
                this is where that lag becomes visible.
  GAP         — in neither. Feeds the fit score, not the writing.

The bank is expected to be one free-form file; a directory is read whole if one
is given. Nothing inside what the caller named is skipped, because silently
ignoring part of the bank would report a fact the candidate has as a gap.

This is advisory, not a gate. Exit code is 0 unless the inputs can't be read (2).
Output is line-stable so `eval_run.py` can hold it as a fixture snapshot.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402
import aliases  # noqa: E402

# A locator is a pointer to the passage, not a concordance of every mention.
MAX_LOCATORS = 3
# What to call a hit above the exemplar's first section — the name, headline and
# contact row. Part of the report format, so `eval_run.py` snapshots it.
PREAMBLE_LABEL = "(header)"


def extract_keywords(jd_text: str) -> list[str]:
    """Pull the keyword list from the `## ATS keywords` section of jd.md.

    Line breaks carry no meaning here — a keyword is a keyword whether it sat
    alone or shared a comma-separated line — so the rows are flattened.
    """
    out: list[str] = []
    for row in _common.bulleted_section(jd_text, "ATS keywords"):
        for kw in row:
            if kw not in out:
                out.append(kw)
    return out


def read_bank(bank: Path) -> list[tuple[str, int, str]]:
    """The bank as (file, lineno, line), read once for every keyword to reuse.

    One free-form prose file is the expected shape; a directory is read whole.
    """
    files = sorted(bank.rglob("*.md")) if bank.is_dir() else [bank]
    return [(path.name, lineno, line)
            for path in files
            for lineno, line in enumerate(_common.read_text(path).splitlines(), start=1)]


def keyword_variants(keyword: str, groups: list[list[str]]) -> list[str]:
    """The keyword, then the alias spellings interchangeable with it.

    Assembly already swaps in the posting's spelling (ADR-0008), so a posting
    asking for "Postgres" against an exemplar saying "PostgreSQL" is covered —
    the delivered CV will say Postgres. Matching only the literal keyword would
    report that as a gap, lowering the fit score for a keyword the CV does match
    and prompting a promotion for a fact already on the exemplar.
    """
    fold = keyword.casefold()
    for group in groups:
        if any(m.casefold() == fold for m in group):
            return [keyword] + [m for m in group if m.casefold() != fold]
    return [keyword]


def _matched(keyword: str, variants: list[str], line: str) -> str | None:
    """Which spelling this line uses, if any.

    The keyword is matched case-insensitively, as an ATS would. Alias variants
    carry the alias table's own casing rule instead, which is what keeps `Go`
    from matching "decided to go with" and calling a gap covered.
    """
    for variant in variants:
        if variant == keyword:
            if _common.keyword_pattern(variant).search(line):
                return variant
        elif aliases.first_position(variant, line) is not None:
            return variant
    return None


def exemplar_sections(keyword: str, exemplar_text: str,
                      groups: list[list[str]] = ()) -> tuple[list[str], list[str]]:
    """The exemplar sections naming this keyword, and any alias spellings used.

    Where a keyword sits is the difference between evidence and assertion: in an
    Experience bullet it is backed by an achievement, in Skills it is a claim on
    its own. The preamble — name, headline, contact row — belongs to no section
    and is labelled as the header, so a headline keyword still counts as found.
    """
    variants = keyword_variants(keyword, list(groups))
    found: list[str] = []
    via: list[str] = []
    for title, lines in _common.split_sections(exemplar_text):
        label = title or PREAMBLE_LABEL
        for line in lines:
            hit = _matched(keyword, variants, line)
            if hit is None:
                continue
            if label not in found:
                found.append(label)
            if hit != keyword and hit not in via:
                via.append(hit)
    return found, via


def bank_locators(keyword: str, bank: list[tuple[str, int, str]],
                  groups: list[list[str]] = ()) -> tuple[list[str], list[str]]:
    """`file:line` for each mention in the bank, so a promotion can be judged."""
    variants = keyword_variants(keyword, list(groups))
    hits: list[str] = []
    via: list[str] = []
    for name, lineno, line in bank:
        hit = _matched(keyword, variants, line)
        if hit is None:
            continue
        hits.append(f"{name}:{lineno}")
        if hit != keyword and hit not in via:
            via.append(hit)
    return hits, via


class Row(NamedTuple):
    keyword: str
    bucket: str
    locators: list[str]
    via: list[str]


def classify(keyword: str, exemplar_text: str, bank: list[tuple[str, int, str]],
             groups: list[list[str]] = ()) -> Row:
    """Bucket one keyword, with the locators for acting on it."""
    sections, via = exemplar_sections(keyword, exemplar_text, groups)
    if sections:
        return Row(keyword, "COVERED", sections, via)
    hits, via = bank_locators(keyword, bank, groups)
    return Row(keyword, "PROMOTABLE" if hits else "GAP", hits, via)


def format_via(via: list[str]) -> str:
    """Name the spelling the artifact actually uses, so the match is auditable."""
    return "  (as " + ", ".join(f'"{v}"' for v in via) + ")" if via else ""


def format_locators(hits: list[str]) -> str:
    shown = hits[:MAX_LOCATORS]
    suffix = f"  (+{len(hits) - len(shown)} more)" if len(hits) > len(shown) else ""
    return ", ".join(shown) + suffix


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("jd", help="path to the application's jd.md")
    ap.add_argument("--exemplar", required=True, help="path to master_cv.md")
    ap.add_argument("--bank", required=True,
                    help="path to the story bank (a file, or a directory of .md)")
    ap.add_argument("--aliases", action="append",
                    help="extra alias table to merge with the shipped one (repeatable)")
    args = ap.parse_args(argv)

    jd_text = _common.read_text(args.jd)
    if not jd_text:
        print(f"error: jd not found or empty: {args.jd}", file=sys.stderr)
        return 2
    exemplar, bank = Path(args.exemplar), Path(args.bank)
    if not exemplar.is_file():
        print(f"error: --exemplar not found: {exemplar}", file=sys.stderr)
        return 2
    if not (bank.is_file() or bank.is_dir()):
        print(f"error: --bank not found: {bank}", file=sys.stderr)
        return 2

    exemplar_text = _common.read_text(exemplar)
    bank_lines = read_bank(bank)
    keywords = extract_keywords(jd_text)
    # A mistyped table degrades to literal matching out loud rather than killing
    # the report: this step is advisory, and the orchestrator is waiting on it.
    groups, alias_faults = aliases.load_table([aliases.PLUGIN_TABLE, *(args.aliases or [])])

    print(f"ATS-COVERAGE  jd={args.jd}  exemplar={exemplar}  bank={bank}")
    for fault in alias_faults:
        print(f"  warning: {fault} — matching literally for those spellings")
    if not keywords:
        print("  no keywords found under a `## ATS keywords` heading in jd.md")
        return 0

    rows = [classify(kw, exemplar_text, bank_lines, groups) for kw in keywords]
    buckets = {name: [r for r in rows if r.bucket == name]
               for name in ("COVERED", "PROMOTABLE", "GAP")}
    print(f"  keywords: {len(keywords)}   covered: {len(buckets['COVERED'])}   "
          f"promotable: {len(buckets['PROMOTABLE'])}   gap: {len(buckets['GAP'])}")
    for row in buckets["COVERED"]:
        print(f"  [COVERED]    {row.keyword} — {', '.join(row.locators)}"
              f"{format_via(row.via)}")
    for row in buckets["PROMOTABLE"]:
        print(f"  [PROMOTABLE] {row.keyword} — {format_locators(row.locators)}"
              f"{format_via(row.via)}"
              "  (in the bank, not the exemplar — promote it to use it)")
    for row in buckets["GAP"]:
        print(f"  [GAP]        {row.keyword} — in neither"
              " (feeds the fit score, not the writing)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

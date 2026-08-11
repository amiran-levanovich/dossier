"""Shared helpers for the dossier pipeline scripts.

These scripts are the deterministic, no-LLM steps of the job-apply pipeline
(ATS keyword coverage, tracker CSV writes, trace-map pre-check, session
metrics). They parse the plugin's *own* file formats — jd.md, the trace file
format from core/tailoring_method.md, the tracker schema from
lifecycle/tracking.md, the KB schema from core/kb_schema.md — so they live
with the method, not with any user's data.
"""

from __future__ import annotations

import re
from pathlib import Path

# The arrow used in trace files (core/tailoring_method.md). Accept the ASCII
# fallback too so a hand-edited trace file still parses.
TRACE_ARROWS = ("→", "->")


def read_text(path: str | Path) -> str:
    """Read a UTF-8 text file, returning '' for a missing file."""
    p = Path(path)
    if not p.is_file():
        return ""
    return p.read_text(encoding="utf-8")


def slugify_heading(heading: str) -> str:
    """Slugify a markdown heading the way GitHub anchors do.

    Lowercase, drop anything that isn't a word char / space / hyphen, then turn
    runs of spaces into single hyphens. '## Data & APIs' -> 'data--apis' is the
    GitHub behaviour (the '&' is dropped, leaving two spaces that each become a
    hyphen), and trace anchors are written to match it.
    """
    text = heading.lstrip("#").strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s", "-", text)
    return text


def normalize_anchor(anchor: str) -> str:
    """Slug rules + collapse runs of hyphens, for tolerant anchor matching.

    A trace anchor is written by hand and a heading slug is derived by GitHub's
    rules, so the same reference can be spelled several ways: 'Achievements'
    (title case), 'Data & infra' (raw heading text), 'data-infra' (single
    hyphen) vs the '&'-derived slug 'data--infra'. Passing both the cited anchor
    and each real heading slug through this makes those all compare equal, while
    still rejecting a reference to a heading that genuinely does not exist.
    """
    return re.sub(r"-{2,}", "-", slugify_heading(anchor))


def heading_slugs(text: str) -> set[str]:
    """Every heading anchor slug present in a markdown document."""
    slugs = set()
    for line in text.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            slugs.add(slugify_heading(m.group(2)))
    return slugs


def normalize_line(line: str) -> str:
    """Whitespace/bullet-marker normalisation — the only tolerance allowed when
    comparing a produced document against the exemplar it was cut from."""
    text = line.strip()
    text = re.sub(r"^[-*+]\s+", "", text)
    return re.sub(r"\s+", " ", text)


def content_lines(text: str):
    """Yield (lineno, normalized) for every content-bearing line.

    Headings are structural, not claims, so they are skipped — which is what
    lets a verbatim check compare claims without tripping over the skeleton.
    """
    for i, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        yield i, normalize_line(raw)


def bulleted_section(text: str, heading: str,
                     require_bullets: bool = False) -> list[list[str]]:
    """Comma-separated items under a named markdown heading, grouped by line.

    One of the plugin's own file formats, read by two callers that disagree about
    what a line means: jd.md's `## ATS keywords` wants every keyword regardless
    of how the lines were broken, while alias_groups.md's `## Alias groups`
    treats each line as one group. So this keeps the line structure and lets the
    caller flatten it.

    `require_bullets` is the other half of that disagreement. A keyword block is
    hand-pasted and a bare line in it is still a keyword; an alias group is data,
    where a sentence of prose that parsed as a group would put an unrelated word
    into a set of interchangeable spellings.
    """
    wanted = re.compile(rf"^#{{1,6}}\s+{re.escape(heading)}\s*$", re.IGNORECASE)
    rows: list[list[str]] = []
    in_block = False
    for line in text.splitlines():
        if re.match(r"^#{1,6}\s", line):
            in_block = bool(wanted.match(line.strip()))
            continue
        if not in_block:
            continue
        stripped = line.strip()
        if require_bullets and not re.match(r"^[-*+]\s", stripped):
            continue
        item = stripped.lstrip("-*").strip()
        if not item:
            continue
        row = [part.strip().strip("`") for part in item.split(",")]
        row = [part for part in row if part]
        if row:
            rows.append(row)
    return rows


def keyword_pattern(keyword: str) -> re.Pattern:
    """Whole-token, case-insensitive matcher tolerant of tech punctuation.

    Uses non-alphanumeric lookarounds instead of \\b so that names like 'C++',
    '.NET' and 'Node.js' match as whole tokens rather than fragments.
    """
    esc = re.escape(keyword.strip())
    return re.compile(rf"(?<![A-Za-z0-9]){esc}(?![A-Za-z0-9])", re.IGNORECASE)

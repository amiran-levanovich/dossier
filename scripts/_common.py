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


def heading_slugs(text: str) -> set[str]:
    """Every heading anchor slug present in a markdown document."""
    slugs = set()
    for line in text.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            slugs.add(slugify_heading(m.group(2)))
    return slugs


def keyword_pattern(keyword: str) -> re.Pattern:
    """Whole-token, case-insensitive matcher tolerant of tech punctuation.

    Uses non-alphanumeric lookarounds instead of \\b so that names like 'C++',
    '.NET' and 'Node.js' match as whole tokens rather than fragments.
    """
    esc = re.escape(keyword.strip())
    return re.compile(rf"(?<![A-Za-z0-9]){esc}(?![A-Za-z0-9])", re.IGNORECASE)

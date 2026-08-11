#!/usr/bin/env python3
"""Alias groups — the posting's spelling of a technology, not the exemplar's.

Pure trim (ADR-0005) sends whatever the exemplar says, so a posting asking for
"Postgres" against an exemplar saying "PostgreSQL" loses a real ATS keyword
match for no substantive reason. An **alias group** is a set of interchangeable
surface spellings for one technology; the trigger rule is judgment-free, as
everything in `scripts/` must be: the posting contains variant X, the document
contains variant Y, X and Y share a group, emit X.

Ordering is the whole design (ADR-0008). Slot ids hash slot text, so a swap
applied before the verbatim self-test would rename the slots it touched and void
the guarantee every application inherits. `apply` therefore demands the passed
self-test result as an argument and raises without one, so the sequence is
enforced here rather than described somewhere and hoped for.

Two rules keep string matching from turning into vandalism:

* **Whole tokens only** — `Kubernetes` does not fire inside `Kubernetesish`,
  while `PostgreSQL-backed` does swap, because a hyphen is a boundary.
* **A member carrying an uppercase letter is replaced case-sensitively**, which
  is what stops `Go` from rewriting "decided to go with a queue". Detection in
  the *posting* is looser: an exact-case hit wins if the posting has one, and a
  case-insensitive hit still counts otherwise, because postings are prose and
  "we use postgres daily" is a genuine mention of the technology.

Standard library only, like every script here.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterable, NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402

# The generic table shipped with the plugin. A user extension lives in the job
# folder and is passed alongside it; the two merge at read time.
PLUGIN_TABLE = Path(__file__).resolve().parent / "alias_groups.md"
# Groups are the bullets under this heading. Requiring the heading means a
# hand-written extension that forgot it fails loudly instead of parsing as empty.
GROUP_HEADING = "Alias groups"


class Swap(NamedTuple):
    lineno: int
    term: str
    replacement: str


class AliasOrderError(RuntimeError):
    """Raised when the alias pass is asked to run before a passed self-test."""


def parse_groups(text: str) -> list[list[str]]:
    """Alias groups from one table file — one group per line, prose ignored.

    Each line is one group, so a note that slipped into the section becomes a
    one-member group, which `load_table` reports rather than silently keeping.
    """
    groups: list[list[str]] = []
    for row in _common.bulleted_section(text, GROUP_HEADING, require_bullets=True):
        members: list[str] = []
        seen: set[str] = set()
        for member in row:
            if member.casefold() not in seen:
                seen.add(member.casefold())
                members.append(member)
        groups.append(members)
    return groups


def merge_groups(groups: Iterable[Iterable[str]]) -> list[list[str]]:
    """Fold groups sharing a member into one, first-seen spelling and order kept.

    Sharing a member is what lets a user extension *extend* a shipped group
    rather than compete with it: listing `Postgres, pg` next to the shipped
    `PostgreSQL, Postgres` widens one group instead of creating a second one
    whose winner would depend on iteration order.
    """
    merged: list[list[str]] = []
    owner: dict[str, int] = {}

    def absorb(home: int, members: Iterable[str]) -> None:
        for member in members:
            key = member.casefold()
            if key not in owner or owner[key] != home:
                merged[home].append(member)
            owner[key] = home

    for group in groups:
        members = [m for m in group if m]
        homes = sorted({owner[m.casefold()] for m in members if m.casefold() in owner})
        if not homes:
            merged.append([])
            absorb(len(merged) - 1, members)
            continue
        home, *rest = homes
        for other in rest:
            absorbed, merged[other] = merged[other], []
            absorb(home, absorbed)
        absorb(home, members)
    return [g for g in merged if g]


def load_table(paths: Iterable[str | Path]) -> tuple[list[list[str]], list[str]]:
    """Merged groups from every table path, plus every reason to distrust them.

    A missing file or a missing section is a fault rather than an empty table: a
    user who wrote an extension and got silence would keep believing their
    spellings were in play.
    """
    collected: list[list[str]] = []
    faults: list[str] = []
    for path in paths:
        p = Path(path)
        if not p.is_file():
            faults.append(f"alias table not found: {p}")
            continue
        text = _common.read_text(p)
        groups = parse_groups(text)
        if not groups:
            faults.append(f"{p} has no `## Alias groups` section with member bullets")
            continue
        for group in groups:
            if len(group) < 2:
                faults.append(f"{p}: alias group {group[0]!r} has one member —"
                              " it can never fire, so this is a dropped comma")
        collected.extend(groups)
    return merge_groups(collected), faults


def _case_ok(member: str, matched: str) -> bool:
    """Whether this match counts, given the member's own casing rule.

    A member carrying an uppercase letter must match exactly; an all-lowercase
    member matches any casing.
    """
    return not any(c.isupper() for c in member) or matched == member


def first_position(member: str, text: str) -> int | None:
    """Where `member` first appears as a whole token, honouring its own casing."""
    for m in _common.keyword_pattern(member).finditer(text):
        if _case_ok(member, m.group(0)):
            return m.start()
    return None


def _loose_position(member: str, text: str) -> int | None:
    """Same, ignoring case — used only to read the posting, never to rewrite."""
    m = _common.keyword_pattern(member).search(text)
    return m.start() if m else None


def posting_variant(group: Iterable[str], posting_text: str) -> str | None:
    """Which member of this group the posting uses, in the table's spelling.

    Exact casing wins over an earlier loose hit, so "we go fast. Golang
    throughout." resolves to `Golang` rather than to the English verb. The
    table's spelling is what gets emitted, so a posting shouting "POSTGRESQL" in
    a heading cannot put that on the CV.
    """
    best_key: tuple[int, int] | None = None
    winner: str | None = None
    for member in group:
        exact = first_position(member, posting_text)
        pos = exact if exact is not None else _loose_position(member, posting_text)
        if pos is None:
            continue
        key = (0 if exact is not None else 1, pos)
        if best_key is None or key < best_key:
            best_key, winner = key, member
    return winner


def _swap_table(groups: Iterable[Iterable[str]],
                posting_text: str) -> tuple[re.Pattern | None, dict[str, tuple[str, str]]]:
    """One combined pattern over every replaceable spelling, and its lookup.

    One pattern, one pass, longest spelling first: replacing member by member
    would rescan text it had just inserted, and `RoR` → `Ruby on Rails` would
    then match its own `Rails` and yield "Ruby on Ruby on Rails".
    """
    lookup: dict[str, tuple[str, str]] = {}
    for group in groups:
        winner = posting_variant(group, posting_text)
        if winner is None:
            continue
        for member in group:
            if member.casefold() != winner.casefold():
                lookup[member.casefold()] = (member, winner)
    if not lookup:
        return None, lookup
    alternation = "|".join(re.escape(m) for _, (m, _w) in
                           sorted(lookup.items(), key=lambda kv: -len(kv[1][0])))
    pattern = re.compile(rf"(?<![A-Za-z0-9])({alternation})(?![A-Za-z0-9])",
                         re.IGNORECASE)
    return pattern, lookup


def apply(doc_lines: list[str], posting_text: str,
          groups: Iterable[Iterable[str]], verbatim) -> tuple[list[str], list[Swap]]:
    """Rewrite the assembled document into the posting's spellings.

    `verbatim` is the self-test result from the assembly step and must have no
    changed lines. Refusing to run without it is ADR-0008 enforced rather than
    documented: aliasing a document that was never proven verbatim would produce
    an artifact with no provenance at all, and the swap log would read as though
    the only differences from the exemplar were the deliberate ones.
    """
    if verbatim is None or getattr(verbatim, "changed", None):
        raise AliasOrderError(
            "the alias pass runs only on a document that passed the verbatim"
            " self-test (ADR-0008) — assemble, prove, then alias")

    pattern, lookup = _swap_table(groups, posting_text)
    if pattern is None:
        return list(doc_lines), []

    out: list[str] = []
    swaps: list[Swap] = []
    for lineno, line in enumerate(doc_lines, start=1):
        def replace(m: re.Match) -> str:
            matched = m.group(1)
            member, winner = lookup[matched.casefold()]
            if not _case_ok(member, matched):
                return matched
            swaps.append(Swap(lineno, matched, winner))
            return winner

        out.append(pattern.sub(replace, line))
    return out, swaps


def log_document(swaps: Iterable[Swap], sources: Iterable[str], exemplar: str) -> str:
    """The audit trail for every difference between `cv.md` and the exemplar."""
    swaps = list(swaps)
    lines = [
        "# Alias swap log",
        "",
        f"The assembled CV was proven verbatim against `{exemplar}` **before**"
        " these swaps were applied (ADR-0008), so this list is the complete set"
        " of differences between the delivered `cv.md` and the exemplar's text.",
        "",
        "Tables read: " + ", ".join(f"`{s}`" for s in sources),
        "",
    ]
    if not swaps:
        lines.append("No swaps: the posting used no spelling the exemplar does not"
                     " already use, so `cv.md` is byte-identical to the assembly"
                     " output.")
    else:
        lines.append(f"## Swaps ({len(swaps)})")
        lines.append("")
        lines.extend(f"- line {s.lineno}: `{s.term}` → `{s.replacement}`" for s in swaps)
    return "\n".join(lines) + "\n"

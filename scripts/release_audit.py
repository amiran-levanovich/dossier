#!/usr/bin/env python3
"""release_audit.py — enforce TOKEN_ECONOMY.md's release checklist as a gate.

TOKEN_ECONOMY.md §5 (doc-weight budgets) and §6 (the grep checklist) are the
plugin's defense against cost creep, but they were a *manual* routine a human
runs — or forgets. This script makes the deterministic parts a tested,
stdlib-only gate so a regression fails loud instead of shipping.

Checks:
  C1  no `.claude/agents/*.md` sets `model: inherit` — a model-tier leak runs
      mechanical work on a frontier model (TOKEN_ECONOMY.md §1 C1, v2.2.0).
  C3  every skill/core doc that mentions WebSearch/WebFetch carries a numeric
      search budget somewhere in the file (v2.2.0 unbudgeted-search incident).
  C4  every agent/core doc with fix/verify-loop language names continuation
      (SendMessage / "continue") somewhere (v2.1.0 respawn incident).
  C7  each budgeted doc is at or under its word budget. The budgets are parsed
      FROM the §5 table in TOKEN_ECONOMY.md, so the doc stays the single source
      of truth and the script can never drift from it.

C3/C4 are file-level presence checks (line-level proximity is too false-positive
prone: many mentions are descriptive). They catch the whole-doc regression — a
search/loop doc with no budget/continuation anywhere — not per-line rigor, which
stays a human/verifier concern. An overview that intentionally defers detail to
another doc opts out with a file-level `audit-ok: <CHECK>` marker (greppable).

Usage:
  release_audit.py            human report, exit 1 if any violation
  release_audit.py --json     findings as JSON on stdout
  release_audit.py --root DIR audit a repo at DIR (default: cwd)

Exit codes: 0 clean · 1 violations present · 2 usage/IO error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

TOKEN_ECONOMY = "TOKEN_ECONOMY.md"
AGENTS_GLOB = ".claude/agents/*.md"
SKILLS_GLOB = ".claude/skills/*/SKILL.md"
CORE_GLOB = "job_docs/core/*.md"

_BACKTICKED = re.compile(r"`([^`]+)`")
_MODEL_INHERIT = re.compile(r"^\s*model:\s*inherit\s*$", re.MULTILINE)
_SECTION5 = re.compile(r"^##\s*5\b")
_NEXT_SECTION = re.compile(r"^##\s")

# C3: a web-tool mention, and a numeric budget nearby. "Nearby" = a count within
# ~25 chars of a budget word (quer/max/default), either order — matches "2
# queries default", "5 max", and "2 WebSearch queries by default" (where the
# number and "queries" are split by "WebSearch"). Budget words are kept to the
# real budget vocabulary so a bare "WebSearch" mention never self-satisfies.
_WEB_MENTION = re.compile(r"WebSearch|WebFetch")
_WEB_BUDGET = re.compile(
    r"\d+[^\n]{0,25}?(?:quer|max|default)|(?:quer|max|default)[^\n]{0,25}?\d+",
    re.IGNORECASE,
)

# C4: fix/verify-loop language, and a continuation cue.
_LOOP_TRIGGER = re.compile(r"re-verify|fix round|relaunch|respawn", re.IGNORECASE)
_CONTINUATION = re.compile(r"SendMessage|continu", re.IGNORECASE)


def _audit_ok(text: str, check: str) -> bool:
    """A file opts out of one check with a greppable `audit-ok: <CHECK>` marker."""
    return re.search(rf"audit-ok:[^\n]*\b{check}\b", text) is not None


@dataclass(frozen=True)
class Violation:
    check: str
    path: str
    message: str


def word_count(text: str) -> int:
    """Whitespace-token count, matching `wc -w` (the §2 sweep command)."""
    return len(text.split())


def parse_budgets(token_economy_text: str) -> list[tuple[str, int]]:
    """Parse the §5 doc-weight table into (glob, budget) pairs.

    Only rows inside the "## 5 …" section whose first cell contains a
    backticked path are budgets — that discriminator excludes the §3 tool-call
    table (whose first cells are prose like "Writer agent, first pass").
    """
    lines = token_economy_text.splitlines()
    budgets: list[tuple[str, int]] = []
    in_section = False
    for line in lines:
        if _SECTION5.match(line):
            in_section = True
            continue
        if in_section and _NEXT_SECTION.match(line):
            break
        if not in_section or not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        m = _BACKTICKED.search(cells[0])
        if not m:
            continue  # header, separator, or a non-path row
        glob = m.group(1)
        digits = re.sub(r"[^\d]", "", cells[-1])
        if not digits:
            continue
        budgets.append((glob, int(digits)))
    return budgets


def check_model_inherit(root: Path) -> list[Violation]:
    violations = []
    for path in sorted(Path(root).glob(AGENTS_GLOB)):
        if _MODEL_INHERIT.search(path.read_text(encoding="utf-8")):
            rel = path.relative_to(root).as_posix()
            violations.append(Violation("C1", rel, "agent runs on `model: inherit` (pin the cheapest model that survives the gate)"))
    return violations


def check_doc_weights(budgets: list[tuple[str, int]], root: Path) -> list[Violation]:
    violations = []
    root = Path(root)
    for glob, budget in budgets:
        for path in sorted(root.glob(glob)):
            if not path.is_file():
                continue
            count = word_count(path.read_text(encoding="utf-8"))
            if count > budget:
                rel = path.relative_to(root).as_posix()
                violations.append(Violation("C7", rel, f"{count} words > budget {budget} (over by {count - budget})"))
    return violations


def check_web_budget(root: Path) -> list[Violation]:
    """C3: a doc that mentions a web tool must carry a numeric budget somewhere."""
    root = Path(root)
    violations = []
    seen = set()
    for glob in (SKILLS_GLOB, CORE_GLOB):
        for path in sorted(root.glob(glob)):
            if path in seen:
                continue
            seen.add(path)
            text = path.read_text(encoding="utf-8")
            if not _WEB_MENTION.search(text) or _audit_ok(text, "C3"):
                continue
            if not _WEB_BUDGET.search(text):
                rel = path.relative_to(root).as_posix()
                violations.append(Violation("C3", rel, "mentions WebSearch/WebFetch but states no numeric budget (or add an `audit-ok: C3` marker if it defers)"))
    return violations


def check_loop_continuation(root: Path) -> list[Violation]:
    """C4: a doc with fix/verify-loop language must name continuation somewhere."""
    root = Path(root)
    violations = []
    seen = set()
    for glob in (AGENTS_GLOB, CORE_GLOB):
        for path in sorted(root.glob(glob)):
            if path in seen:
                continue
            seen.add(path)
            text = path.read_text(encoding="utf-8")
            if not _LOOP_TRIGGER.search(text) or _audit_ok(text, "C4"):
                continue
            if not _CONTINUATION.search(text):
                rel = path.relative_to(root).as_posix()
                violations.append(Violation("C4", rel, "has fix/verify-loop language but never names continuation (SendMessage/continue) — or add an `audit-ok: C4` marker if it defers"))
    return violations


def run_audit(root: Path) -> list[Violation]:
    root = Path(root)
    te = root / TOKEN_ECONOMY
    budgets = parse_budgets(te.read_text(encoding="utf-8")) if te.is_file() else []
    return (
        check_model_inherit(root)
        + check_web_budget(root)
        + check_loop_continuation(root)
        + check_doc_weights(budgets, root)
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=".", help="repo root to audit (default: cwd)")
    ap.add_argument("--json", action="store_true", help="emit findings as JSON on stdout")
    args = ap.parse_args(argv)

    root = Path(args.root)
    try:
        violations = run_audit(root)
    except OSError as e:
        print(f"release_audit: {e}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps([v.__dict__ for v in violations], indent=1))

    if not violations:
        print("release_audit: pass (no violations)", file=sys.stderr)
        return 0

    for v in violations:
        print(f"{v.path}: {v.check}: {v.message}", file=sys.stderr)
    print(f"release_audit: {len(violations)} violation(s)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

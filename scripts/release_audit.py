#!/usr/bin/env python3
"""release_audit.py — enforce TOKEN_ECONOMY.md's release checklist as a gate.

TOKEN_ECONOMY.md §5 (doc-weight budgets) and §6 (the grep checklist) are the
plugin's defense against cost creep, but they were a *manual* routine a human
runs — or forgets. This script makes the deterministic parts a tested,
stdlib-only gate so a regression fails loud instead of shipping.

Checks:
  C1  no `.claude/agents/*.md` sets `model: inherit` — a model-tier leak runs
      mechanical work on a frontier model (TOKEN_ECONOMY.md §1 C1, v2.2.0).
  C2  a per-item read instruction (a quantifier on the same line as a read tool)
      is answered by a batch discipline AND a numeric call budget in the same
      file (v2.2.0 Read/Grep-per-trace-line, v2.4.0 re-read-per-finding).
  C3  every skill/core doc that mentions WebSearch/WebFetch carries a numeric
      search budget somewhere in the file (v2.2.0 unbudgeted-search incident).
  C4  every agent/core doc with fix/verify-loop language names continuation
      (SendMessage / "continue") somewhere (v2.1.0 respawn incident).
  C7  each budgeted doc is at or under its token budget. The budgets are parsed
      FROM the §5 table in TOKEN_ECONOMY.md, so the doc stays the single source
      of truth and the script can never drift from it. A missing or malformed
      table is itself a C7 violation: C1-C4 read the repo and cannot silently
      vanish, but C7's input is parsed, so every way it can go wrong is a way
      the check would otherwise disappear at exit 0.

C3/C4 are file-level presence checks (line-level proximity is too false-positive
prone: many mentions are descriptive). They catch the whole-doc regression — a
search/loop doc with no budget/continuation anywhere — not per-line rigor, which
stays a human/verifier concern. An overview that intentionally defers detail to
another doc opts out with a file-level `audit-ok: <CHECK>` marker (greppable).

C2 splits the difference: its *trigger* is line-level because "every" and "Read"
are ordinary words that co-occur innocently across a whole doc, and only their
collision on one line reads as "one tool call per item". Its *mitigation* stays
file-level like C3/C4, and it requires both halves of the §6 wording ("a batch
discipline and call budget") because the two incidents needed both fixes.

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
_BUDGET_CELL = re.compile(r"^\d{1,3}(?:[,\s]\d{3})*$|^\d+$")
_TOKEN_PIECE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?|\d{1,3}|\s+|[^\sA-Za-z\d]")
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

# C2: a quantifier on the same line as a read tool = "one call per item".
# Demonstratives are excluded because "per that doc" / "per this rule" quantify a
# reference, not a loop over items.
_C2_QUANT = re.compile(
    r"\b(?:every|each|per\s+(?!the\b|that\b|this\b|these\b|those\b|our\b|its\b)\w+)\b",
    re.IGNORECASE,
)
_C2_TOOL = re.compile(r"\b(?:Read|Grep|Glob|WebSearch|WebFetch)\b")
_C2_BATCH = re.compile(
    r"batch|one pass|single read|at once|in one call|exactly once|in-context",
    re.IGNORECASE,
)
_C2_BUDGET = re.compile(
    r"\d+[^\n]{0,20}?(?:calls?|quer)|(?:calls?|quer)[^\n]{0,20}?\d+|call budget",
    re.IGNORECASE,
)


def _audit_ok(text: str, check: str) -> bool:
    """A file opts out of one check with a greppable `audit-ok: <CHECK>` marker."""
    return re.search(rf"audit-ok:[^\n]*\b{check}\b", text) is not None


@dataclass(frozen=True)
class Violation:
    check: str
    path: str
    message: str


def estimate_tokens(text: str) -> int:
    """Estimate the tokens a doc costs when loaded. Not exact — deliberately.

    Budgets are in tokens because tokens are what a run pays, and words price
    the wrong thing: markdown-free prose runs about 1.3 tokens per word, a table
    row of backticked paths nearer 4, and the docs in the §5 table 1.9-3.2 since
    they mix both. A word budget under-prices exactly that dense markup.

    No tokenizer ships in the standard library and `scripts/` takes no
    dependencies, so this approximates a BPE pre-tokenizer: letter runs, digit
    groups of up to three, each symbol on its own, runs over six letters split
    further, and whitespace runs priced. A lone space is free because BPE folds
    it into the following token; longer runs are not, since leaving them free
    would let any doc be padded past its budget at zero cost.

    A drift detector, not a billing meter. Deterministic, monotonic, and right
    about which text is expensive is the whole specification.
    """
    total = 0
    for piece in _TOKEN_PIECE.findall(text):
        if piece[:1].isalpha() and len(piece) > 6:
            total += -(-len(piece) // 5)  # ceil: long words split into sub-tokens
        elif piece.isspace():
            total += 0 if piece == " " else max(1, -(-len(piece) // 8))
        else:
            total += 1
    return total


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
        budget = _parse_budget_cell(cells[-1])
        if budget is None:
            continue  # malformed — check_budget_table reports it loudly
        budgets.append((glob, budget))
    return budgets


def _parse_budget_cell(cell: str) -> int | None:
    """A budget cell is a bare number, thousands separators allowed.

    Strict on purpose. Stripping non-digits would read "1,400 (was 500)" as
    1400500 — a row that looks fine and silently can never fail.
    """
    if not _BUDGET_CELL.match(cell.strip()):
        return None
    return int(re.sub(r"[,\s]", "", cell))


def budget_table_problems(token_economy_text: str) -> list[str]:
    """§5 rows that name a path but whose budget cell will not parse."""
    problems = []
    in_section = False
    for line in token_economy_text.splitlines():
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
        if m and _parse_budget_cell(cells[-1]) is None:
            problems.append(f"`{m.group(1)}` has an unparseable budget cell {cells[-1]!r}")
    return problems


def check_budget_table(root: Path) -> list[Violation]:
    """C7's input must fail loudly.

    C1-C4 read the repo, so they cannot silently vanish. C7 reads a parsed
    table, so a missing file or a malformed row would otherwise disable the
    check while the audit still exits 0.
    """
    root = Path(root)
    te = root / TOKEN_ECONOMY
    if not te.is_file():
        return [Violation("C7", TOKEN_ECONOMY,
                          "budget source is missing — C7 cannot run (restore the file, "
                          "or drop C7 from the §6 checklist)")]
    return [Violation("C7", TOKEN_ECONOMY, p)
            for p in budget_table_problems(te.read_text(encoding="utf-8"))]


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
            text = path.read_text(encoding="utf-8")
            if _audit_ok(text, "C7"):
                continue
            count = estimate_tokens(text)
            if count > budget:
                rel = path.relative_to(root).as_posix()
                violations.append(Violation("C7", rel, f"{count} tokens > budget {budget} (over by {count - budget}) — cut substance, or add an `audit-ok: C7` marker with the reason"))
    return violations


def check_batch_discipline(root: Path) -> list[Violation]:
    """C2: a per-item read instruction needs a batch discipline and a call budget.

    Trigger is line-level (quantifier + read tool on one line); mitigation is
    file-level, matching C3/C4. Reports the offending line numbers so the finding
    is actionable rather than "somewhere in this file".
    """
    root = Path(root)
    violations = []
    seen = set()
    for glob in (AGENTS_GLOB, CORE_GLOB, SKILLS_GLOB):
        for path in sorted(root.glob(glob)):
            if path in seen:
                continue
            seen.add(path)
            text = path.read_text(encoding="utf-8")
            if _audit_ok(text, "C2"):
                continue
            hits = [
                n for n, line in enumerate(text.splitlines(), 1)
                if _C2_QUANT.search(line) and _C2_TOOL.search(line)
            ]
            if not hits:
                continue
            missing = []
            if not _C2_BATCH.search(text):
                missing.append("batch discipline")
            if not _C2_BUDGET.search(text):
                missing.append("call budget")
            if not missing:
                continue
            rel = path.relative_to(root).as_posix()
            where = ", ".join(f"line {n}" for n in hits[:3])
            if len(hits) > 3:
                where += f" (+{len(hits) - 3} more)"
            violations.append(Violation(
                "C2", rel,
                f"per-item tool instruction at {where} but the file states no "
                f"{' or '.join(missing)} (or add an `audit-ok: C2` marker if it defers)",
            ))
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
        + check_batch_discipline(root)
        + check_web_budget(root)
        + check_loop_continuation(root)
        + check_budget_table(root)
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

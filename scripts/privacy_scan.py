#!/usr/bin/env python3
"""privacy_scan.py — personal-data (PII) boundary scanner for the dossier repo.

The dossier repo is the *system layer*: generic method, docs, and helper
scripts. A candidate's data (name, employers, emails, salaries, application
material) belongs only in the separate, git-ignored job folder — never here.
CLAUDE.md states this as a rule enforced by a manual "sweep before committing";
this script makes the sweep a machine-checked gate (run in CI and, optionally,
before a commit) so the one irreversible mistake — PII in git history — fails
loud instead of relying on a human remembering.

Detectors (each maps a match to `path:line: category`):
  email     real addresses, EXCLUDING example/placeholder domains and locals.
  salary    an amount anchored to an explicit currency (€/EUR/USD/$/CHF/GBP/£).
            Deliberately NOT a bare "Nk" — the docs are full of "60k tokens".
  phone     international format only (leading +CC) — never an ISO date/range.
  denylist  whole-token, case-insensitive terms from an untracked config file
            (default `.privacy-denylist`, one term per line, '#' comments).
            The candidate's real name/employers live there, so the file itself
            is git-ignored and never scanned. Absent file => category skipped.

Modes:
  (default)        scan all git-tracked text files (via `git ls-files`).
  --staged         scan the staged content of files in the git index.
  --paths P [P...] scan the given files directly (used by tests / ad-hoc).

A line carrying the marker `pii-ok` (e.g. an HTML comment
`<!-- pii-ok: reason -->`) is exempt — the escape hatch for a genuinely generic
illustrative example in a method doc, e.g. a salary-format range. It is
line-scoped and greppable, so every suppression stays auditable.

Findings are printed to stderr as `path:line: category: <masked>` — the match
is masked so the scanner never echoes full PII into a log. `--json` prints the
findings (also masked) to stdout.

Exit codes: 0 clean · 1 findings present · 2 usage/IO error.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

DENYLIST_NAME = ".privacy-denylist"

# --- email -----------------------------------------------------------------
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Placeholder domains/locals that are template text, not a real person.
_EXAMPLE_DOMAINS = ("example.com", "example.org", "example.net", "example.edu", "localhost")
_PLACEHOLDER_LOCALS = ("you", "name", "firstname.lastname", "your.email", "email", "user")

# --- salary ----------------------------------------------------------------
# A currency token must sit right against a 5-6 digit amount, in either order.
_CUR = r"(?:€|£|\$|EUR|USD|GBP|CHF)"
_AMT = r"\d{2,3}[.,]?\d{3}"
_SALARY_RE = re.compile(rf"(?:{_CUR}\s?{_AMT}|{_AMT}\s?{_CUR})")

# --- phone -----------------------------------------------------------------
# Leading +CC, then 3+ digit groups. An ISO date (no '+') can never match.
_PHONE_RE = re.compile(r"\+\d{1,3}(?:[\s./-]?\(?\d{2,4}\)?){3,5}")

# --- suppression ------------------------------------------------------------
# A line with this marker opts out (like '# noqa'): the escape hatch for a
# generic illustrative example. Line-scoped and greppable for audit.
_SUPPRESS_RE = re.compile(r"pii-ok", re.IGNORECASE)


@dataclass(frozen=True)
class Finding:
    line: int
    category: str
    match: str


def mask(s: str) -> str:
    """Mask a matched substring so findings never echo raw PII.

    Keeps the first two and last one characters visible for locating; the
    middle becomes '*'. Strings of length <= 3 are fully masked.
    """
    if len(s) <= 3:
        return "*" * len(s)
    return s[:2] + "*" * (len(s) - 3) + s[-1]


def _iter_lines(text: str):
    for i, line in enumerate(text.splitlines(), start=1):
        yield i, line


def find_emails(text: str) -> list[tuple[int, str]]:
    hits = []
    for lineno, line in _iter_lines(text):
        for m in _EMAIL_RE.finditer(line):
            addr = m.group(0)
            local, _, domain = addr.partition("@")
            domain_l = domain.lower()
            if any(domain_l == d or domain_l.endswith("." + d) for d in _EXAMPLE_DOMAINS):
                continue
            if local.lower() in _PLACEHOLDER_LOCALS:
                continue
            hits.append((lineno, addr))
    return hits


def find_salaries(text: str) -> list[tuple[int, str]]:
    hits = []
    for lineno, line in _iter_lines(text):
        for m in _SALARY_RE.finditer(line):
            hits.append((lineno, m.group(0)))
    return hits


def find_phones(text: str) -> list[tuple[int, str]]:
    hits = []
    for lineno, line in _iter_lines(text):
        for m in _PHONE_RE.finditer(line):
            hits.append((lineno, m.group(0)))
    return hits


def find_denylist(text: str, terms: list[str]) -> list[tuple[int, str]]:
    if not terms:
        return []
    # Whole-token, case-insensitive; tech-punctuation tolerant (same lookaround
    # rule as _common.keyword_pattern) so 'Straiv' never fires in 'Straivision'.
    patterns = [
        (t, re.compile(rf"(?<![A-Za-z0-9]){re.escape(t)}(?![A-Za-z0-9])", re.IGNORECASE))
        for t in terms
    ]
    hits = []
    for lineno, line in _iter_lines(text):
        for term, pat in patterns:
            if pat.search(line):
                hits.append((lineno, term))
    return hits


def scan_text(text: str, denylist: list[str]) -> list[Finding]:
    suppressed = {i for i, line in _iter_lines(text) if _SUPPRESS_RE.search(line)}
    findings: list[Finding] = []
    for lineno, m in find_emails(text):
        findings.append(Finding(lineno, "email", m))
    for lineno, m in find_salaries(text):
        findings.append(Finding(lineno, "salary", m))
    for lineno, m in find_phones(text):
        findings.append(Finding(lineno, "phone", m))
    for lineno, m in find_denylist(text, denylist):
        findings.append(Finding(lineno, "denylist", m))
    findings = [f for f in findings if f.line not in suppressed]
    findings.sort(key=lambda f: (f.line, f.category))
    return findings


def load_denylist(path: str | Path) -> list[str]:
    p = Path(path)
    if not p.is_file():
        return []
    terms = []
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        terms.append(line)
    return terms


def is_binary(data: bytes) -> bool:
    return b"\x00" in data[:8192]


def _is_denylist_file(path: Path) -> bool:
    return path.name == DENYLIST_NAME or path.name.startswith(DENYLIST_NAME)


def scan_paths(paths, denylist: list[str]) -> list[tuple[Path, Finding]]:
    results: list[tuple[Path, Finding]] = []
    for path in paths:
        p = Path(path)
        if _is_denylist_file(p) or not p.is_file():
            continue
        try:
            data = p.read_bytes()
        except OSError:
            continue
        if is_binary(data):
            continue
        text = data.decode("utf-8", errors="replace")
        for finding in scan_text(text, denylist):
            results.append((p, finding))
    return results


def _git_files(staged: bool) -> list[Path]:
    if staged:
        cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"]
    else:
        cmd = ["git", "ls-files"]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return [Path(line) for line in out.stdout.splitlines() if line.strip()]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--paths", nargs="+", help="scan these files directly")
    ap.add_argument("--staged", action="store_true", help="scan the git index (staged) files")
    ap.add_argument("--denylist", default=DENYLIST_NAME, help=f"denylist file (default: {DENYLIST_NAME})")
    ap.add_argument("--json", action="store_true", help="emit findings as JSON on stdout")
    args = ap.parse_args(argv)

    denylist = load_denylist(args.denylist)

    try:
        if args.paths:
            paths = args.paths
        else:
            paths = _git_files(args.staged)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"privacy_scan: cannot list git files: {e}", file=sys.stderr)
        return 2

    results = scan_paths(paths, denylist)

    if args.json:
        print(json.dumps(
            [{"path": str(p), "line": f.line, "category": f.category, "match": mask(f.match)}
             for p, f in results],
            indent=1,
        ))

    file_count = len(set(str(p) for p in paths))
    if not results:
        print(f"privacy_scan: clean ({file_count} file(s) scanned)", file=sys.stderr)
        return 0

    for p, f in results:
        print(f"{p}:{f.line}: {f.category}: {mask(f.match)}", file=sys.stderr)
    n_files = len(set(str(p) for p, _ in results))
    print(f"privacy_scan: {len(results)} finding(s) across {n_files} file(s)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

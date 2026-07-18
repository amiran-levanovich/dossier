#!/usr/bin/env python3
"""tracker.csv writer — the mechanical half of lifecycle/tracking.md.

Appends and updates rows in the application tracker with the correct column
order, CSV quoting, and header migration handled deterministically, so the
orchestrator never has to read the whole CSV back, reason about column order,
and re-emit it by hand. The *judgment* — what status, what fit_score, how to
word next_action, generic-vs-human rejection — stays with the orchestrator and
is passed in as flags; this script only does the safe write.

Schema (lifecycle/tracking.md):
  company,role,date_applied,status,next_action,link,notes,stage_reached,date_closed,fit_score

Commands:
  add     append a new row (one row per application)
  update  set fields on the row matching --company (+ --role if ambiguous)
  show    print matching row(s)

A file with an older, shorter header is migrated to the full column set in
place on the first write (per tracking.md's migration rule). Exit 0 on success;
1 on a no-match / ambiguous-match / bad-column error; 2 on IO/usage error.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
from pathlib import Path

COLUMNS = [
    "company",
    "role",
    "date_applied",
    "status",
    "next_action",
    "link",
    "notes",
    "stage_reached",
    "date_closed",
    "fit_score",
]
TERMINAL = {"offer", "rejected", "withdrawn"}


def today() -> str:
    return dt.date.today().isoformat()


def load(path: Path) -> list[dict]:
    """Read rows as dicts keyed by the full COLUMNS set (missing -> '')."""
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = []
        for raw in reader:
            rows.append({c: (raw.get(c) or "").strip() for c in COLUMNS})
        return rows


def save(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        for r in rows:
            writer.writerow({c: r.get(c, "") for c in COLUMNS})


def find(rows: list[dict], company: str, role: str | None):
    matches = [
        i
        for i, r in enumerate(rows)
        if r["company"].lower() == company.lower()
        and (role is None or r["role"].lower() == role.lower())
    ]
    return matches


def cmd_add(args) -> int:
    path = Path(args.file)
    rows = load(path)
    status = args.status or "to_apply"
    date_applied = args.date_applied or (today() if status == "applied" else "")
    row = {
        "company": args.company,
        "role": args.role or "",
        "date_applied": date_applied,
        "status": status,
        "next_action": args.next_action or "",
        "link": args.link or "",
        "notes": args.notes or "",
        "stage_reached": args.stage_reached or "",
        "date_closed": args.date_closed or "",
        "fit_score": args.fit_score or "",
    }
    rows.append(row)
    save(path, rows)
    print(f"added: {row['company']} | {row['role']} | {row['status']}")
    _warn_row(row)
    return 0


def cmd_update(args) -> int:
    path = Path(args.file)
    rows = load(path)
    if not rows:
        print(f"error: no rows in {path}", file=sys.stderr)
        return 1
    idxs = find(rows, args.company, args.role)
    if not idxs:
        who = args.company + (f" / {args.role}" if args.role else "")
        print(f"error: no row matches {who}", file=sys.stderr)
        return 1
    if len(idxs) > 1 and not args.all:
        print(
            f"error: {len(idxs)} rows match '{args.company}' — add --role or --all",
            file=sys.stderr,
        )
        return 1

    updates = {}
    for pair in args.set or []:
        if "=" not in pair:
            print(f"error: --set expects col=value, got '{pair}'", file=sys.stderr)
            return 1
        col, val = pair.split("=", 1)
        col = col.strip()
        if col not in COLUMNS:
            print(f"error: unknown column '{col}'; valid: {', '.join(COLUMNS)}", file=sys.stderr)
            return 1
        updates[col] = val

    for i in idxs:
        rows[i].update(updates)
        # Convenience: a terminal status with no date_closed gets today's date,
        # matching tracking.md's "set date_closed in the same edit" rule.
        if rows[i]["status"] in TERMINAL and not rows[i]["date_closed"]:
            rows[i]["date_closed"] = today()
        _warn_row(rows[i])
    save(path, rows)
    print(f"updated {len(idxs)} row(s) for {args.company}")
    return 0


def cmd_show(args) -> int:
    path = Path(args.file)
    rows = load(path)
    idxs = find(rows, args.company, args.role) if args.company else list(range(len(rows)))
    if not idxs:
        print("(no matching rows)")
        return 1
    for i in idxs:
        r = rows[i]
        print(" | ".join(f"{c}={r[c]}" for c in COLUMNS if r[c]))
    return 0


def _warn_row(row: dict) -> None:
    """Nudge on the tracking.md defects a script can spot (not enforce)."""
    if row["status"] == "applied":
        for col in ("date_applied", "link", "next_action"):
            if not row[col]:
                print(f"  warning: applied row is missing {col} (tracking.md defect)", file=sys.stderr)
    if row["status"] in TERMINAL and not row["stage_reached"]:
        print("  warning: terminal status without stage_reached — invisible to analytics", file=sys.stderr)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--file", default="tracker.csv", help="path to tracker.csv")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="append a new application row")
    a.add_argument("--company", required=True)
    a.add_argument("--role")
    a.add_argument("--status", help="default: to_apply")
    a.add_argument("--date-applied", dest="date_applied")
    a.add_argument("--next-action", dest="next_action")
    a.add_argument("--link")
    a.add_argument("--notes")
    a.add_argument("--stage-reached", dest="stage_reached")
    a.add_argument("--date-closed", dest="date_closed")
    a.add_argument("--fit-score", dest="fit_score")
    a.set_defaults(func=cmd_add)

    u = sub.add_parser("update", help="set fields on a matching row")
    u.add_argument("--company", required=True)
    u.add_argument("--role")
    u.add_argument("--all", action="store_true", help="update every matching row")
    u.add_argument("--set", action="append", metavar="COL=VALUE", help="repeatable")
    u.set_defaults(func=cmd_update)

    s = sub.add_parser("show", help="print matching row(s)")
    s.add_argument("--company", nargs="?")
    s.add_argument("--role")
    s.set_defaults(func=cmd_show)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

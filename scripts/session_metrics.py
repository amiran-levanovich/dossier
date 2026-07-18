#!/usr/bin/env python3
"""Session metrics — turn a Claude Code transcript into TOKEN_ECONOMY.md §2 proxies.

TOKEN_ECONOMY.md §2 lists the observable proxies for pipeline burn (tool-call
counts, WebSearch/WebFetch counts, subagent spawns). Claude Code transcripts
(~/.claude/projects/<slug>/<session>.jsonl) also carry real per-turn `usage`
token counts, so this reports both: the proxies §2 asks for, plus actual token
totals when present.

This is the harness for the quick-win baseline. Point it at the .jsonl of a real
job-apply session to capture the per-run numbers the Phase 2 audit needs. Main
session and subagent (`isSidechain`) turns are counted separately so a heavy
agent shows up on its own line.

Usage: session_metrics.py <session.jsonl> [<session.jsonl> ...]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

TOKEN_FIELDS = [
    "input_tokens",
    "output_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
]


def analyze(path: Path) -> dict:
    stats = {
        "assistant_turns": 0,
        "sidechain_turns": 0,
        "tools": Counter(),
        "sidechain_tools": Counter(),
        "web_fetch": 0,
        "web_search": 0,
        "subagents": Counter(),
        "tokens": Counter(),
        "malformed": 0,
    }
    # Transcripts write one assistant entry PER CONTENT BLOCK; entries of the
    # same turn share message.id and each repeats the turn's `usage`. Count
    # turns and usage once per unique id or totals inflate ~3x.
    seen_ids: set[str] = set()
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                stats["malformed"] += 1
                continue
            if obj.get("type") != "assistant":
                continue
            sidechain = bool(obj.get("isSidechain"))
            msg = obj.get("message") or {}
            mid = msg.get("id")
            if mid is None or mid not in seen_ids:
                if mid is not None:
                    seen_ids.add(mid)
                stats["sidechain_turns" if sidechain else "assistant_turns"] += 1
                usage = msg.get("usage") or {}
                for f in TOKEN_FIELDS:
                    v = usage.get(f)
                    if isinstance(v, int):
                        stats["tokens"][f] += v
            content = msg.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                name = block.get("name", "?")
                (stats["sidechain_tools"] if sidechain else stats["tools"])[name] += 1
                if name == "WebFetch":
                    stats["web_fetch"] += 1
                elif name == "WebSearch":
                    stats["web_search"] += 1
                elif name in ("Task", "Agent"):
                    inp = block.get("input") or {}
                    label = inp.get("subagent_type") or inp.get("description") or "?"
                    stats["subagents"][label] += 1
    return stats


def report(path: Path, s: dict) -> None:
    main_calls = sum(s["tools"].values())
    side_calls = sum(s["sidechain_tools"].values())
    print(f"SESSION-METRICS {path}")
    print(f"  assistant turns: {s['assistant_turns']} main, {s['sidechain_turns']} subagent")
    print(f"  tool calls: {main_calls} main, {side_calls} subagent")
    if s["tools"]:
        top = ", ".join(f"{n}×{c}" for n, c in s["tools"].most_common(6))
        print(f"    main: {top}")
    if s["sidechain_tools"]:
        top = ", ".join(f"{n}×{c}" for n, c in s["sidechain_tools"].most_common(6))
        print(f"    subagent: {top}")
    print(f"  WebFetch: {s['web_fetch']}   WebSearch: {s['web_search']}")
    if s["subagents"]:
        spawns = ", ".join(f"{n}×{c}" for n, c in s["subagents"].most_common())
        print(f"  subagent spawns: {sum(s['subagents'].values())}  [{spawns}]")
    else:
        print("  subagent spawns: 0")
    t = s["tokens"]
    if any(t.values()):
        processed = t["input_tokens"] + t["output_tokens"] + t["cache_creation_input_tokens"]
        print(
            "  tokens: "
            f"input={t['input_tokens']:,}  output={t['output_tokens']:,}  "
            f"cache_write={t['cache_creation_input_tokens']:,}  "
            f"cache_read={t['cache_read_input_tokens']:,}"
        )
        print(
            f"    ~processed (input+output+cache_write): {processed:,}  "
            "(cache_read is cheap cache hits, repeated across turns)"
        )
    else:
        print("  tokens: not recorded in this transcript")
    if s["malformed"]:
        print(f"  ({s['malformed']} unparseable line(s) skipped)")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("sessions", nargs="+", help="path(s) to session .jsonl transcript(s)")
    args = ap.parse_args(argv)
    rc = 0
    for sp in args.sessions:
        p = Path(sp)
        if not p.is_file():
            print(f"error: not found: {sp}", file=sys.stderr)
            rc = 2
            continue
        report(p, analyze(p))
        print()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

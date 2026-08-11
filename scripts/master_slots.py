#!/usr/bin/env python3
"""Exemplar slot model — extract, stamp, assemble (ADR-0003).

With a verified exemplar (`master_cv.md`), `application-writer` stops emitting a
CV and emits an **edit plan** against a **slot map**. This script owns both ends
of that contract:

    master_slots.py extract  master_cv.md --out slots.json
    master_slots.py stamp    master_cv_trace.md --master master_cv.md
    master_slots.py assemble plan.json --master master_cv.md --out-dir app/

A **slot** is an addressable unit of the exemplar: a *block* (one experience,
project, education, skills or languages entry, inseparable from its heading,
dates and descriptor) or a *bullet* scoped inside a block. Bullet ids are
reachable only through their parent block, so a bullet cannot be assembled under
another employer's heading — a misattribution no trace file would catch, since a
trace maps claim → knowledge-base source, never claim → employer.

Slot ids hash the slot's own text, never its position: inserting or reordering
in the exemplar renames nothing, while editing a slot's text renames exactly
that slot — which is when its trace line needs re-judging anyway. This is the
invalidation doctrine claim_ledger.py already states: automatic, never manual.

Standard library only, like every script here.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402
import trace_check  # noqa: E402
from trace_check import SLOT_ID_PREFIX_RE  # noqa: E402

# The slot model itself lives in cv.py, which owns it going forward. Sharing it
# rather than keeping a second copy matters more than the import direction
# looks: slot_id *is* the id contract, and two copies that drifted would
# silently rename slots while both test suites stayed green.
import cv  # noqa: E402
from cv import (  # noqa: E402
    DATES_RE,
    ENTRY_HEADING_RE,
    ENTRY_SECTIONS,
    ID_PREFIX,
    SECTION_KINDS,
    build_slot_map,
    slot_id,
)

has_slots = cv.has_slots
_index_slots = cv._slots_by_id
_bullet_parents = cv._bullet_parents

_ = (DATES_RE, ENTRY_HEADING_RE, ENTRY_SECTIONS, ID_PREFIX, SECTION_KINDS, slot_id, build_slot_map)


# Connectives an abbreviated claim may add or drop freely; they carry no claim
# content, so pairing compares only the tokens that do.
STOPWORDS = {
    "a", "an", "the", "of", "on", "in", "for", "to", "and", "with", "at", "by",
    "from", "as", "into", "over", "per", "via", "that", "this", "its", "our",
}


def content_tokens(text: str) -> list[str]:
    # `.` and `+` are inside the token class so 'Node.js' and 'C++' survive
    # whole; strip them at the edges so a sentence-final 'systems.' still equals
    # 'systems'.
    tokens = (t.strip(".") for t in re.findall(r"[\w+#.]+", text.lower()))
    return [t for t in tokens if t and t not in STOPWORDS]


def claim_supports(claim: str, slot_text: str) -> bool:
    """True when the claim's content tokens appear, in order, in the slot text.

    A trace claim is an *abbreviation* of the line it describes
    (core/tailoring_method.md), so it drops words and connectives — but it never
    reorders them and never introduces content the slot lacks.
    """
    wanted = content_tokens(claim.strip().strip('"“”'))
    if not wanted:
        return False
    have = content_tokens(slot_text)
    i = 0
    for token in have:
        if token == wanted[i]:
            i += 1
            if i == len(wanted):
                return True
    return False


def claim_bearing_slots(smap: dict) -> list[dict]:
    """Every slot that can carry a trace line, in document order."""
    out: list[dict] = []
    for block in smap["blocks"]:
        if block.get("bullets"):
            out.extend(block["bullets"])
        elif "text" in block:
            out.append(block)
    return out


def pair_trace_to_slots(trace_text: str, smap: dict):
    """Walk both sequences in order, pairing each trace line with a slot.

    Returns (pairs, error). Slots may be skipped — structural or neutral lines
    carry no trace line — but a trace line that matches nothing from the current
    position onward means the two files disagree, and stamping an id onto it
    would bind a claim to the wrong slot.
    """
    slots = claim_bearing_slots(smap)
    pairs: list[tuple[int, str, str, str]] = []
    cursor = 0
    for tline, malformed in trace_check.parse_trace_file(trace_text):
        if malformed is not None:
            lineno, claim = malformed
            return None, (lineno, claim, "malformed trace line")
        while cursor < len(slots) and not claim_supports(tline.claim, slots[cursor]["text"]):
            cursor += 1
        if cursor >= len(slots):
            return None, (tline.lineno, tline.claim,
                          "no slot supports this claim at or after this point")
        pairs.append((tline.lineno, slots[cursor]["id"], tline.claim, slots[cursor]["text"]))
        cursor += 1
    return pairs, None


def cmd_stamp(args) -> int:
    trace_path, master = Path(args.trace), Path(args.master)
    for path in (trace_path, master):
        if not path.is_file():
            print(f"error: not found: {path}", file=sys.stderr)
            return 2

    smap = build_slot_map(master.name, _common.read_text(master))
    if not has_slots(smap):
        print(f"PAIRING {trace_path} → {master}\n  ERROR: {UNSUPPORTED}")
        return 1
    trace_text = _common.read_text(trace_path)
    pairs, error = pair_trace_to_slots(trace_text, smap)

    print(f"PAIRING {trace_path} → {master}")
    if error is not None:
        lineno, claim, why = error
        print(f"  [UNPAIRED] line {lineno}: {claim} — {why}")
        print("\nRESULT: no ids written — the trace and the exemplar disagree")
        return 1

    by_lineno = {lineno: (sid, claim, text) for lineno, sid, claim, text in pairs}
    for _, sid, claim, text in pairs:
        short = (text[:60] + "…") if len(text) > 61 else text
        print(f"  {sid}  {claim}\n          ✓ {short}")

    out_lines = []
    for i, raw in enumerate(trace_text.splitlines(), start=1):
        if i in by_lineno:
            sid = by_lineno[i][0]
            body = SLOT_ID_PREFIX_RE.sub("", raw.strip()[2:].strip(), count=1)
            indent = raw[: len(raw) - len(raw.lstrip())]
            out_lines.append(f"{indent}- [{sid}] {body}")
        else:
            out_lines.append(raw)
    trace_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"\nRESULT: {len(pairs)}/{len(pairs)} paired — ids written")
    return 0


def cmd_extract(args) -> int:
    master = Path(args.master)
    if not master.is_file():
        print(f"error: exemplar not found: {master}", file=sys.stderr)
        return 2
    smap = build_slot_map(master.name, _common.read_text(master))
    if not has_slots(smap):
        print(f"SLOT-MAP {master}\n  ERROR: {UNSUPPORTED}", file=sys.stderr)
        return 1
    if args.trace:
        bodies = stamped_trace_bodies(_common.read_text(args.trace))
        for slot in _index_slots(smap).values():
            target = trace_target(bodies.get(slot["id"], ""))
            if target:
                slot["trace"] = target
    payload = json.dumps(smap, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    n_bullets = sum(len(b.get("bullets", [])) for b in smap["blocks"])
    print(f"SLOT-MAP {master}", file=sys.stderr)
    print(f"  blocks: {len(smap['blocks'])}   bullets: {n_bullets}", file=sys.stderr)
    return 0


def stamped_trace_bodies(trace_text: str) -> dict[str, str]:
    """slot id → the trace line body (`"claim" → target`) from a stamped file."""
    bodies: dict[str, str] = {}
    for raw in trace_text.splitlines():
        stripped = raw.strip()
        if not stripped.startswith("- "):
            continue
        body = stripped[2:].strip()
        m = SLOT_ID_PREFIX_RE.match(body)
        if m:
            bodies[m.group(0).strip()[1:-1]] = SLOT_ID_PREFIX_RE.sub("", body, count=1)
    return bodies




UNSUPPORTED = (
    "no slots found — this exemplar is not in the templates/cv_template.md shape\n"
    "  (`# Name` / `## Section` / `### Role — Company` headings). An exemplar the\n"
    "  parser cannot decompose would yield an empty slot map and assemble an empty\n"
    "  CV, so this stops here. Run the previous path instead: pass master_cv.md to\n"
    "  application-writer directly and check the result with master_diff.py, which\n"
    "  is line-based and format-agnostic."
)






def trace_target(body: str) -> str:
    """The target half of a trace line body, split at the rightmost arrow."""
    idx, arrow = max((body.rfind(a), a) for a in _common.TRACE_ARROWS)
    return body[idx + len(arrow):].strip() if idx >= 0 else ""


def render_document(smap: dict, plan: dict, resolved: dict[str, str]) -> list[str]:
    """Rebuild the CV skeleton, filling only the slots the plan ordered."""
    order = plan.get("order", [])
    index = _index_slots(smap)
    # Section order comes from the exemplar, never from the plan: the template's
    # section order is a standards rule, not a per-application choice.
    section_order: list[str] = []
    for block in smap["blocks"]:
        section = block.get("section")
        if section and section not in section_order:
            section_order.append(section)

    by_section: dict[str, list[dict]] = {s: [] for s in section_order}
    headline_id = None
    for entry in order:
        slot = index.get(entry["id"])
        if slot is None:
            continue
        if slot["kind"] == "headline":
            headline_id = entry["id"]
            continue
        by_section.setdefault(slot.get("section") or "", []).append(entry)

    lines: list[str] = [smap["header"]["name"]]
    if headline_id:
        lines.append(resolved[headline_id])
    if smap["header"]["contact"]:
        lines.extend(["", smap["header"]["contact"]])

    for section in section_order:
        entries = by_section.get(section) or []
        if not entries:
            continue
        lines.extend(["", f"## {section}"])
        for entry in entries:
            slot = index[entry["id"]]
            if slot.get("bullets") is not None:
                lines.extend(["", slot["heading"]])
                if slot["dates"]:
                    lines.append(slot["dates"])
                if slot["descriptor"]:
                    lines.append(slot["descriptor"])
                lines.append("")
                for bullet_id in entry.get("bullets", []):
                    lines.append(f"- {resolved[bullet_id]}")
            else:
                text = resolved[entry["id"]]
                lines.append(f"- {text}" if slot.get("bulleted") else text)
    return lines


def render_trace(smap: dict, plan: dict, resolved: dict[str, str],
                 inherited: dict[str, str], authored: dict[str, str]) -> list[str]:
    """One trace line per claim-bearing slot, in document order."""
    index = _index_slots(smap)
    out: list[str] = []
    for entry in plan.get("order", []):
        slot = index.get(entry["id"])
        is_block = slot is not None and slot.get("bullets") is not None
        ids = list(entry.get("bullets", [])) if is_block else [entry["id"]]
        for sid in ids:
            if sid in authored:
                out.append(f'- "{resolved[sid]}" → {authored[sid]}')
            elif sid in inherited:
                out.append(f"- {inherited[sid]}")
    return out


def cmd_assemble(args) -> int:
    plan_path, master = Path(args.plan), Path(args.master)
    for path in (plan_path, master):
        if not path.is_file():
            print(f"error: not found: {path}", file=sys.stderr)
            return 2
    try:
        plan = json.loads(_common.read_text(plan_path))
    except json.JSONDecodeError as exc:
        print(f"error: edit plan is not valid JSON: {exc}", file=sys.stderr)
        return 2

    smap = build_slot_map(master.name, _common.read_text(master))
    if not has_slots(smap):
        print(f"ASSEMBLE {master} + {plan_path}\n  ERROR: {UNSUPPORTED}\n\nno output written")
        return 1
    index = _index_slots(smap)
    inherited = stamped_trace_bodies(_common.read_text(args.trace))

    faults: list[str] = []
    resolved: dict[str, str] = {sid: slot["text"] for sid, slot in index.items() if "text" in slot}
    for slot in smap["blocks"]:
        resolved.setdefault(slot["id"], slot.get("heading", ""))

    authored: dict[str, str] = {}
    for item in plan.get("new", []):
        if not item.get("trace"):
            faults.append(f"new slot {item.get('id', '?')!r} has no trace target")
            continue
        resolved[item["id"]] = item["text"]
        authored[item["id"]] = item["trace"]
    n_patched = 0
    for item in plan.get("patch", []):
        if item["id"] not in index:
            faults.append(f"unknown slot id in patch[]: {item['id']}")
            continue
        resolved[item["id"]] = item["text"]
        authored[item["id"]] = item.get("trace") or trace_target(inherited.get(item["id"], ""))
        n_patched += 1

    ordered_ids: list[str] = []
    placed_bullets: set[str] = set()
    parents = _bullet_parents(smap)
    for entry in plan.get("order", []):
        ordered_ids.append(entry["id"])
        ordered_ids.extend(entry.get("bullets", []))
        placed_bullets.update(entry.get("bullets", []))
        # A bullet belongs to exactly one block. Placing it under a different
        # block's heading would attribute the achievement to another employer —
        # a fabrication a trace file cannot catch, since it maps claim → KB
        # source and never claim → employer.
        for bullet_id in entry.get("bullets", []):
            owner = parents.get(bullet_id)
            if owner is not None and owner != entry["id"]:
                faults.append(f"{bullet_id} does not belong to block {entry['id']}"
                              f" (it is a bullet of {owner})")
    for sid in ordered_ids:
        if sid not in index and sid not in resolved:
            faults.append(f"unknown slot id in order[]: {sid}")
    # A new slot is only ever a bullet inside a block. One that is never placed
    # would take a trace line for a claim that never reaches cv.md.
    for item in plan.get("new", []):
        # Items already faulted for a missing trace are not reported twice.
        if item.get("id") in authored and item["id"] not in placed_bullets:
            faults.append(f"new slot {item['id']} is never placed in a block's bullets[]")
    seen: set[str] = set()
    for sid in ordered_ids:
        if sid in seen:
            faults.append(f"duplicate slot id in order[]: {sid}")
        seen.add(sid)
    for sid in plan.get("drop", []):
        if sid in seen:
            faults.append(f"{sid} appears in both order[] and drop[]")

    print(f"ASSEMBLE {master} + {plan_path}")
    if faults:
        for fault in faults:
            print(f"  ERROR: {fault}")
        print(f"\n{len(faults)} fault(s) — no output written")
        return 1

    doc = render_document(smap, plan, resolved)
    trace_lines = render_trace(smap, plan, resolved, inherited, authored)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "cv.md").write_text("\n".join(doc).rstrip() + "\n", encoding="utf-8")
    (out_dir / "cv_trace.md").write_text("\n".join(trace_lines) + "\n", encoding="utf-8")

    n_new = len(plan.get("new", []))
    n_kept = len([sid for sid in ordered_ids if sid in index and sid not in authored])
    n_slots = len(index)
    n_dropped = n_slots - len([sid for sid in ordered_ids if sid in index])
    words = sum(len(line.split()) for line in doc)
    print(f"  kept: {n_kept}   patched: {n_patched}   new: {n_new}   dropped: {n_dropped}")
    print(f"  lines: {len(doc)}   words: {words}   est. pages: ~{max(1.0, round(words / 450, 1))}")
    print(f"\nRESULT: {out_dir / 'cv.md'} + {out_dir / 'cv_trace.md'}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_extract = sub.add_parser("extract", help="exemplar → slot map JSON")
    p_extract.add_argument("master", help="path to master_cv.md")
    p_extract.add_argument("--trace", help="stamped master_cv_trace.md, to carry trace targets inline")
    p_extract.add_argument("--out", help="write the slot map here (default: stdout)")
    p_extract.set_defaults(func=cmd_extract)

    p_stamp = sub.add_parser("stamp", help="write slot ids into an exemplar trace file")
    p_stamp.add_argument("trace", help="path to master_cv_trace.md")
    p_stamp.add_argument("--master", required=True, help="path to master_cv.md")
    p_stamp.set_defaults(func=cmd_stamp)

    p_asm = sub.add_parser("assemble", help="edit plan + exemplar → cv.md + cv_trace.md")
    p_asm.add_argument("plan", help="path to the edit plan JSON")
    p_asm.add_argument("--master", required=True, help="path to master_cv.md")
    p_asm.add_argument("--trace", required=True, help="path to the stamped master_cv_trace.md")
    p_asm.add_argument("--out-dir", required=True, help="application folder to write into")
    p_asm.set_defaults(func=cmd_assemble)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

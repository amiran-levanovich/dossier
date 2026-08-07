#!/usr/bin/env python3
"""Consolidated CV module — slot map out, verbatim CV in (ADR-0004, ADR-0005).

The exemplar (`master_cv.md`) is verified once, at build, and every application
inherits that verdict. What makes the inheritance valid is that an application
CV is *unchanged* from the exemplar: the writer selects and orders slots, and
has no mechanism to reword one. Two commands own both ends of that contract:

    cv.py map   master_cv.md --out slots.json
    cv.py build plan.json --exemplar master_cv.md --out-dir app/

A **slot** is an addressable unit of the exemplar: a *block* (one experience,
project, education, skills or languages entry, inseparable from its heading,
dates and descriptor) or a *bullet* scoped inside a block. Bullet ids are
reachable only through their parent block, so a bullet cannot be assembled under
another employer's heading — a misattribution nothing downstream would catch,
since the result reads as true.

Slot ids hash the slot's own text, never its position: inserting or reordering
in the exemplar renames nothing, while editing a slot's text renames exactly
that slot.

A **one-off slot** is the single exception to that: content the candidate
directed into one application because the exemplar lacked it, declared in the
plan's `one_off[]`. The declaration is the marker — it is what exempts the line
from the verbatim self-test and what tells the verifier there is something left
to judge. Undeclared content absent from the exemplar is a fault, which is what
makes an unmarked rewording impossible to ship.

`build` is atomic. Any fault — an unknown id, a duplicate, a keep/drop
contradiction, a bullet under the wrong block, a one-off reusing an exemplar id,
or a plan asking to reword — exits 1 and writes **no file**, because a partially
assembled CV reads as complete and would go out missing content. The
orchestrator hands the diagnostic back to the writer and re-dispatches.

Standard library only, like every script here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402

# Section heading → the kind of block it contains.
SECTION_KINDS = {
    "summary": "summary",
    "experience": "experience",
    "projects": "projects",
    "education": "education",
    "certifications": "education",
    "skills": "skills",
    "languages": "languages",
}
# Sections whose entries are `###` blocks carrying bullets.
ENTRY_SECTIONS = {"experience", "projects"}
# Id prefix per kind — short, so an id costs a handful of tokens in an edit plan.
ID_PREFIX = {
    "headline": "head",
    "summary": "sum",
    "experience": "exp",
    "projects": "proj",
    "education": "edu",
    "skills": "skills",
    "languages": "lang",
    "bullet": "b",
}
# `### Senior Engineer — Acme, Berlin` → role, company, location.
ENTRY_HEADING_RE = re.compile(r"^###\s+(?P<role>.+?)\s+[—-]\s+(?P<rest>.+?)\s*$")
# A dates line: starts with MM/YYYY or a year.
DATES_RE = re.compile(r"^\d{2}/\d{4}\s*[–-]|^\d{4}\s*[–-]")

UNSUPPORTED = (
    "no slots found — this exemplar is not in the templates/cv_template.md shape\n"
    "  (`# Name` / `## Section` / `### Role — Company` headings). An exemplar the\n"
    "  parser cannot decompose would yield an empty slot map and assemble an empty\n"
    "  CV, so this stops here."
)

# Edit-plan keys this module refuses, and why. Both refusals are permanent:
# rewording is the thing ADR-0005 removes, and `new` was the v3 spelling that
# carried a trace target, which no longer exists.
REFUSED_OPERATIONS = {
    "patch": ("the writer may not reword a slot (ADR-0005) — drop the slot and "
              "declare a one-off instead"),
    "new": ("the v3 spelling carried a trace target — declare a one-off in "
            "one_off[] instead"),
}


def slot_id(kind: str, text: str) -> str:
    """Content-hash id. Normalised so whitespace churn never renames a slot."""
    norm = re.sub(r"\s+", " ", text.strip())
    digest = hashlib.sha256(norm.encode("utf-8")).hexdigest()[:6]
    return f"{ID_PREFIX.get(kind, kind)}-{digest}"


def _split_sections(text: str):
    """Yield (title|None, [lines]) for the preamble and each `##` section."""
    title = None
    buf: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            yield title, buf
            title, buf = line[3:].strip(), []
        else:
            buf.append(line)
    yield title, buf


def _parse_entry_blocks(section: str, kind: str, lines: list[str]) -> list[dict]:
    """Parse `###` entries: heading + dates + descriptor atomic, bullets inside."""
    blocks: list[dict] = []
    current: dict | None = None
    for raw in lines:
        line = raw.strip()
        if raw.startswith("### "):
            m = ENTRY_HEADING_RE.match(raw)
            role = m.group("role").strip() if m else raw[4:].strip()
            rest = m.group("rest").strip() if m else ""
            company, _, location = rest.partition(",")
            current = {
                "kind": kind,
                "section": section,
                "heading": raw.rstrip(),
                "role": role,
                "company": company.strip(),
                "location": location.strip(),
                "dates": "",
                "descriptor": "",
                "bullets": [],
            }
            blocks.append(current)
        elif current is None or not line:
            continue
        elif line.startswith("- "):
            text = line[2:].strip()
            current["bullets"].append({"id": slot_id("bullet", text), "text": text})
        elif not current["dates"] and DATES_RE.match(line):
            current["dates"] = line
        elif not current["descriptor"]:
            current["descriptor"] = line
    for block in blocks:
        own = "\x00".join((block["heading"], block["dates"], block["descriptor"]))
        block["id"] = slot_id(block["kind"], own)
    return blocks


def build_slot_map(source: str, text: str) -> dict:
    """Decompose an exemplar into its slot map."""
    blocks: list[dict] = []
    header: dict = {"name": "", "contact": ""}

    for title, lines in _split_sections(text):
        if title is None:
            # Preamble: `# Name`, then the headline, then the contact row.
            body = [ln for ln in lines if ln.strip()]
            for i, line in enumerate(body):
                if line.startswith("# "):
                    header["name"] = line.rstrip()
                elif not any(b["kind"] == "headline" for b in blocks) and i and header["name"]:
                    blocks.append({
                        "id": slot_id("headline", line.strip()),
                        "kind": "headline",
                        "section": None,
                        "text": line.strip(),
                    })
                else:
                    header["contact"] = line.strip()
            continue

        kind = SECTION_KINDS.get(title.strip().lower())
        if kind is None:
            continue
        if kind in ENTRY_SECTIONS:
            blocks.extend(_parse_entry_blocks(title, kind, lines))
            continue
        if kind == "summary":
            body_lines = [ln.strip() for ln in lines if ln.strip()]
            body = " ".join(body_lines)
            if body:
                # The id hashes the joined text, so rewrapping the paragraph in
                # the exemplar does not rename the slot. `lines` keeps the
                # original breaks, because rendering a joined paragraph would
                # emit a line that appears nowhere in the exemplar and the
                # verbatim self-test would — correctly — refuse it.
                blocks.append({"id": slot_id("summary", body), "kind": "summary",
                               "section": title, "text": body, "lines": body_lines})
            continue
        for raw in lines:
            line = raw.strip()
            if not line:
                continue
            text_ = line[2:].strip() if line.startswith("- ") else line
            blocks.append({"id": slot_id(kind, text_), "kind": kind,
                           "section": title, "text": text_,
                           "bulleted": line.startswith("- ")})

    return {"source": source, "header": header, "blocks": blocks}


def has_slots(smap: dict) -> bool:
    """Whether the exemplar decomposed into anything addressable at all."""
    return any(block.get("bullets") or "text" in block for block in smap["blocks"])


def _slots_by_id(smap: dict) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for block in smap["blocks"]:
        index[block["id"]] = block
        for bullet in block.get("bullets", []):
            index[bullet["id"]] = bullet
    return index


def _bullet_parents(smap: dict) -> dict[str, str]:
    """bullet id → its block's id. A bullet exists only inside one block."""
    return {bullet["id"]: block["id"]
            for block in smap["blocks"]
            for bullet in block.get("bullets", [])}


def render_document(smap: dict, plan: dict) -> list[str]:
    """Rebuild the CV skeleton, filling only the slots the plan ordered."""
    index = dict(_slots_by_id(smap))
    # Declared one-offs join the addressable set for rendering only — they were
    # already checked against it, so nothing here can shadow an exemplar slot.
    for sid, item in one_offs_by_id(plan).items():
        section = item.get("section")
        # Follow the section's own convention rather than guessing: a one-off in
        # a bulleted section should be bulleted, and one in Skills should not.
        siblings = [b for b in smap["blocks"] if b.get("section") == section]
        index[sid] = {"id": sid, "kind": "bullet", "section": section,
                      "text": item["text"], "one_off": True,
                      "bulleted": any(b.get("bulleted") for b in siblings)}
    # Section order comes from the exemplar, never from the plan: the template's
    # section order is a standards rule, not a per-application choice.
    section_order: list[str] = []
    for block in smap["blocks"]:
        section = block.get("section")
        if section and section not in section_order:
            section_order.append(section)

    by_section: dict[str, list[dict]] = {s: [] for s in section_order}
    headline_id = None
    for entry in plan.get("order", []):
        slot = index.get(entry["id"])
        if slot is None:
            continue
        if slot["kind"] == "headline":
            headline_id = entry["id"]
            continue
        by_section.setdefault(slot.get("section") or "", []).append(entry)

    lines: list[str] = [smap["header"]["name"]]
    if headline_id:
        lines.append(index[headline_id]["text"])
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
                    lines.append(f"- {index[bullet_id]['text']}")
            elif slot.get("lines"):
                lines.extend(slot["lines"])
            else:
                text = slot["text"]
                lines.append(f"- {text}" if slot.get("bulleted") else text)
    return lines


def heading_faults(doc_lines: list[str], exemplar_text: str) -> list[str]:
    """Emitted headings that appear nowhere in the exemplar.

    `content_lines` skips headings, so the claim-level check below cannot see
    them — yet `### Role — Company` is exactly the line that says who an
    achievement belongs to. A heading the exemplar never carried would
    reattribute real bullets to an invented employer and read as true.
    """
    def norm(line: str) -> str:
        return re.sub(r"\s+", " ", line.strip())

    known = {norm(l) for l in exemplar_text.splitlines() if l.strip().startswith("#")}
    return [norm(l) for l in doc_lines
            if l.strip().startswith("#") and norm(l) not in known]


def verbatim_report(doc_lines: list[str], exemplar_text: str, exempt: set[str] | None = None):
    """Which produced lines are present in the exemplar, comparing against the
    exemplar's own text rather than the slot map the renderer worked from.

    Comparing the renderer's output back to its own input would be a tautology.
    Reading the exemplar again is what makes this a self-test: it catches the
    renderer corrupting a slot between reading it and emitting it.

    `exempt` holds the declared one-off texts — the only content allowed to be
    absent from the exemplar. Everything else absent is a fault, which is what
    makes an *undeclared* rewording impossible to ship.
    """
    exemplar_set = {norm for _, norm in _common.content_lines(exemplar_text)}
    exempt = exempt or set()
    verbatim, exempted, changed = 0, 0, []
    for lineno, norm in _common.content_lines("\n".join(doc_lines)):
        if norm in exemplar_set:
            verbatim += 1
        elif norm in exempt:
            exempted += 1
        else:
            changed.append((lineno, norm))
    return verbatim, exempted, changed


def one_offs_by_id(plan: dict) -> dict[str, dict]:
    """Declared one-off slots, keyed by id. The declaration is the marker."""
    return {item["id"]: item for item in plan.get("one_off", [])
            if isinstance(item, dict) and "id" in item}


def exemplar_sections(smap: dict) -> list[str]:
    """Section titles the exemplar actually has, in document order."""
    out: list[str] = []
    for block in smap["blocks"]:
        section = block.get("section")
        if section and section not in out:
            out.append(section)
    return out


def collect_faults(smap: dict, plan: dict) -> list[str]:
    """Every reason this plan may not be assembled. Empty means it may."""
    index = _slots_by_id(smap)
    parents = _bullet_parents(smap)
    one_offs = one_offs_by_id(plan)
    sections = exemplar_sections(smap)
    faults: list[str] = []

    for item in plan.get("one_off", []):
        if not isinstance(item, dict) or "id" not in item:
            faults.append(f"malformed one_off[] entry: {item!r}")
            continue
        sid = item["id"]
        # Reusing an exemplar id is how a rewording would sneak past ADR-0005:
        # same id, different text, and the slot map's own text is overwritten.
        if sid in index:
            faults.append(f"one-off {sid} is already a slot in the exemplar —"
                          " a one-off is new content, never a rewording")
        if not str(item.get("text", "")).strip():
            faults.append(f"one-off {sid} has no text")
        section = item.get("section")
        if section is not None and section not in sections:
            faults.append(f"one-off {sid} names section {section!r},"
                          f" which the exemplar does not have")
        elif section is not None and SECTION_KINDS.get(section.lower()) in ENTRY_SECTIONS:
            # Entries in these sections are `### Role — Company` blocks carrying
            # dates and a descriptor. A one-off has none of that, so it would
            # render as a bare line adrift between two employers.
            faults.append(f"one-off {sid} names section {section!r}, whose entries are"
                          " role blocks — a one-off can only be a bullet inside one")

    for key, why in REFUSED_OPERATIONS.items():
        if plan.get(key):
            faults.append(f"plan carries {key}[] — {why}")

    # A document with no claims still renders — name, contact, skeleton — and
    # would pass a 100% verbatim check vacuously. It is not a CV.
    if not plan.get("order"):
        faults.append("plan orders no slots — the result would carry no claims")

    ordered_ids: list[str] = []
    for entry in plan.get("order", []):
        if not isinstance(entry, dict) or "id" not in entry:
            faults.append(f"malformed order[] entry: {entry!r}")
            continue
        ordered_ids.append(entry["id"])
        ordered_ids.extend(entry.get("bullets", []))
        # A section-level one-off has no block to inherit a section from, so it
        # has to say which one it belongs in.
        if entry["id"] in one_offs and one_offs[entry["id"]].get("section") is None:
            faults.append(f"one-off {entry['id']} is placed at section level but"
                          " names no section")
        # A bullet belongs to exactly one block. Placing it under a different
        # block's heading would attribute the achievement to another employer —
        # a fabrication nothing downstream catches, because it reads as true.
        for bullet_id in entry.get("bullets", []):
            owner = parents.get(bullet_id)
            if owner is not None and owner != entry["id"]:
                faults.append(f"{bullet_id} does not belong to block {entry['id']}"
                              f" (it is a bullet of {owner})")

    for sid in ordered_ids:
        if sid not in index and sid not in one_offs:
            faults.append(f"unknown slot id in order[]: {sid}")
    # A declared one-off that reaches no document would take verifier judgment
    # for a claim nobody ever reads.
    for sid in one_offs:
        if sid not in ordered_ids:
            faults.append(f"one-off {sid} is declared but never placed")
    for sid in plan.get("drop", []):
        if sid not in index:
            faults.append(f"unknown slot id in drop[]: {sid}")

    seen: set[str] = set()
    for sid in ordered_ids:
        if sid in seen:
            faults.append(f"duplicate slot id in order[]: {sid}")
        seen.add(sid)
    for sid in plan.get("drop", []):
        if sid in seen:
            faults.append(f"{sid} appears in both order[] and drop[]")
    return faults


def cmd_map(args) -> int:
    exemplar = Path(args.exemplar)
    if not exemplar.is_file():
        print(f"error: exemplar not found: {exemplar}", file=sys.stderr)
        return 2
    smap = build_slot_map(exemplar.name, _common.read_text(exemplar))
    if not has_slots(smap):
        print(f"SLOT-MAP {exemplar}\n  ERROR: {UNSUPPORTED}", file=sys.stderr)
        return 1

    payload = json.dumps(smap, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    n_bullets = sum(len(b.get("bullets", [])) for b in smap["blocks"])
    print(f"SLOT-MAP {exemplar}", file=sys.stderr)
    print(f"  blocks: {len(smap['blocks'])}   bullets: {n_bullets}", file=sys.stderr)
    return 0


def cmd_build(args) -> int:
    plan_path, exemplar = Path(args.plan), Path(args.exemplar)
    for path in (plan_path, exemplar):
        if not path.is_file():
            print(f"error: not found: {path}", file=sys.stderr)
            return 2
    try:
        plan = json.loads(_common.read_text(plan_path))
    except json.JSONDecodeError as exc:
        print(f"error: edit plan is not valid JSON: {exc}", file=sys.stderr)
        return 2

    exemplar_text = _common.read_text(exemplar)
    smap = build_slot_map(exemplar.name, exemplar_text)

    print(f"BUILD {exemplar} + {plan_path}")
    if not has_slots(smap):
        print(f"  ERROR: {UNSUPPORTED}\n\nno output written")
        return 1

    faults = collect_faults(smap, plan)
    if faults:
        for fault in faults:
            print(f"  ERROR: {fault}")
        print(f"\n{len(faults)} fault(s) — no output written")
        return 1

    one_offs = one_offs_by_id(plan)
    exempt = {_common.normalize_line(item["text"]) for item in one_offs.values()}

    doc = render_document(smap, plan)
    verbatim, exempted, changed = verbatim_report(doc, exemplar_text, exempt)
    stray = heading_faults(doc, exemplar_text)
    total = verbatim + len(changed)
    if changed or stray:
        # Only kept slots can reach the document, so a non-verbatim line means
        # this module corrupted one. Refuse rather than ship it.
        for lineno, norm in changed:
            short = (norm[:70] + "…") if len(norm) > 71 else norm
            print(f"  ERROR: line {lineno} is not verbatim from the exemplar: {short}")
        for heading in stray:
            print(f"  ERROR: heading is not from the exemplar: {heading}")
        print(f"\n{len(changed) + len(stray)} non-verbatim line(s) — no output written")
        return 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "cv.md").write_text("\n".join(doc).rstrip() + "\n", encoding="utf-8")

    index = _slots_by_id(smap)
    placed = {sid for entry in plan.get("order", [])
              for sid in [entry["id"], *entry.get("bullets", [])]}
    kept = len(placed - set(one_offs))
    words = sum(len(line.split()) for line in doc)
    print(f"  kept: {kept}   dropped: {len(index) - kept}   one-off: {len(one_offs)}")
    print(f"  verbatim: {verbatim}/{total}   changed: {len(changed)}")
    print(f"  lines: {len(doc)}   words: {words}   est. pages: ~{max(1.0, round(words / 450, 1))}")
    if one_offs:
        # The exemplar's verdict does not cover these. They are the only claims
        # in the package the verifier still has to judge.
        print(f"\n  ONE-OFF — unverified, the verifier must judge these ({exempted} line(s)):")
        for item in one_offs.values():
            print(f"    - {item['text']}")
    print(f"\nRESULT: {out_dir / 'cv.md'}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_map = sub.add_parser("map", help="exemplar → slot map JSON")
    p_map.add_argument("exemplar", help="path to master_cv.md")
    p_map.add_argument("--out", help="write the slot map here (default: stdout)")
    p_map.set_defaults(func=cmd_map)

    p_build = sub.add_parser("build", help="edit plan + exemplar → cv.md")
    p_build.add_argument("plan", help="path to the edit plan JSON")
    p_build.add_argument("--exemplar", required=True, help="path to master_cv.md")
    p_build.add_argument("--out-dir", required=True, help="application folder to write into")
    p_build.set_defaults(func=cmd_build)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

# Master CV — build and maintain the exemplar

One exemplar document turns `application-writer` from a generator into an editor
for the CV half of its job. It is **user data**: it lives at the job-folder root
(a peer of `knowledge/`), never in the plugin.

| File | What it is |
|---|---|
| `master_cv.md` + `master_cv_trace.md` | The superset CV: every role, every bullet worth ever using, ATS-safe per `templates/cv_template.md`, canonical keyword spellings, every claim traced to the KB |

**The cover letter has no exemplar, deliberately.** A CV is a superset you
subtract from, so verbatim lines stay true across companies. A letter's stable
parts are exactly what makes it swappable between companies — the defect
`standards/cover_letter_rules.md` calls out. Every letter is written fresh, and
the per-letter anti-slop pass would strip a reused frame's phrasing anyway.

**Exactly one master, in the search's primary language.** An application in
another language still uses the master as its content source, but translated
lines are all CHANGED in the subset check and pay normal judgment — accepted.

## When to build

Offer the build at **job-intake's close**, once the KB is verified — the
user's call, never automatic. It is worth ~one application's worth of tokens
spent once, calmly, instead of per application under deadline.

## Build procedure

1. **Build**: dispatch `application-writer` with the whole KB selection (all role
   files, `skills.md`, `profile.md`, `constraints.md`, `goals.md`,
   `portfolio.md` if it exists), the CV standards docs, and the instruction:
   *master CV only, superset, not tailored* — include every role and every bullet
   worth ever using, canonical spellings from the KB, template skeleton, full
   trace. No jd.md exists; there is nothing to mirror or subtract yet, and no
   letter is written in this run.
2. **Verify like an application**: `scripts/trace_check.py` on the trace, then
   the full `application-verifier` gauntlet until CLEAN. The master gets
   no discount — it is the one document whose quality every application
   inherits.
3. **Record**: `scripts/claim_ledger.py record master_cv_trace.md
   --document master_cv.md --kb-dir knowledge/`. From now on the tailoring
   pipeline (`core/tailoring_method.md`) shrinks KB selection, runs the
   `master_diff.py` subset check, and the verifier judges only changed lines.
4. **Stamp**: `scripts/master_slots.py stamp master_cv_trace.md --master
   master_cv.md`. This writes a slot id onto each trace line so per-application
   assembly can inherit trace lines by id instead of the writer retyping them
   (ADR-0003). It pairs trace lines to slots **in document order** and validates
   each pairing, so a trace written out of order fails loudly (exit 1, nothing
   written) rather than binding a claim to the wrong slot — read the printed
   pairing table once before moving on. Safe for the ledger: `record` hashes
   `master_cv.md`, and stamping touches only the trace, so a VERIFIED exemplar
   stays VERIFIED. Re-running is idempotent.

**No overrides in the master.** User-directed claims
(`core/override_protocol.md`) are per-application by definition; the master
holds only KB-backed content.

## Rebuild — deliberate, never automatic

`claim_ledger.py check --document …` reporting CHANGED means the exemplar was
edited since verification; the verbatim shortcut is off until it is
re-verified (steps 2–4 — cheap: unchanged claims are already in the ledger, and
slot ids hash slot text, so an edit renames only the slots that actually
changed).
Triggers to offer a rebuild, always the user's call:

- The KB grew — a new role or a skill worth master inclusion (intake and
  mini-interviews should end with: "KB grew — should the master?").
- A standards doc materially changed (e.g. new CV rules).
- The user asks.

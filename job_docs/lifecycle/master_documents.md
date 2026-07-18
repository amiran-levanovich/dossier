# Master Documents — build and maintain the exemplars

Two exemplar documents turn the per-application writers from generators into
editors. They are **user data**: they live at the job-folder root (peers of
`knowledge/`), never in the plugin.

| File | What it is |
|---|---|
| `master_cv.md` + `master_cv_trace.md` | The superset CV: every role, every bullet worth ever using, ATS-safe per `templates/cv_template.md`, canonical keyword spellings, every claim traced to the KB |
| `cover_frame.md` + `cover_frame_trace.md` | The fixed scaffolding of every letter: salutation conventions, the 6-part skeleton with stable parts pre-written (pitch framing, logistics close from `profile.md`), sign-off, and marked slots for the generated paragraphs |

**Exactly one master, in the search's primary language.** An application in
another language still uses the master as its content source, but translated
lines are all CHANGED in the subset check and pay normal judgment — accepted.

## When to build

Offer the build at **job-intake's close**, once the KB is verified — the
user's call, never automatic. It is worth ~one application's worth of tokens
spent once, calmly, instead of per application under deadline.

## Build procedure

1. **Master CV**: dispatch `cv-tailor` with the whole KB selection (all role
   files, `skills.md`, `profile.md`, `constraints.md`, `goals.md`,
   `portfolio.md` if it exists), the standards docs, and the instruction:
   *superset, not tailored* — include every role and every bullet worth ever
   using, canonical spellings from the KB, template skeleton, full trace.
   No jd.md exists; there is nothing to mirror or subtract yet.
2. **Cover frame**: dispatch `cover-letter-writer` with `profile.md`,
   `goals.md`, `constraints.md` and `cover_letter_rules.md` (plus
   `dach_conventions.md` when the market applies), and the instruction: write
   only the fixed parts — salutation per market convention, the pitch
   framing, the logistics close, the sign-off — with `{company}`/`{role}`
   placeholders and clearly marked slots for the two generated paragraphs
   (why-this-company, value proposition). The value proposition is **always
   generated per application** — a canned one is the generic letter
   `cover_letter_rules.md` exists to prevent.
3. **Verify like an application**: `scripts/trace_check.py` on both traces,
   then the full `application-verifier` gauntlet until CLEAN. The master gets
   no discount — it is the one document whose quality every application
   inherits.
4. **Record**: `scripts/claim_ledger.py record master_cv_trace.md
   cover_frame_trace.md --document master_cv.md --document cover_frame.md
   --kb-dir knowledge/`. From now on the tailoring pipeline
   (`core/tailoring_method.md`) shrinks KB selection, runs the
   `master_diff.py` subset check, and the verifier judges only changed lines.

**No overrides in the master.** User-directed claims
(`core/override_protocol.md`) are per-application by definition; the master
holds only KB-backed content.

## Rebuild — deliberate, never automatic

`claim_ledger.py check --document …` reporting CHANGED means the exemplar was
edited since verification; the verbatim shortcut is off until it is
re-verified (step 3–4 — cheap: unchanged claims are already in the ledger).
Triggers to offer a rebuild, always the user's call:

- The KB grew — a new role or a skill worth master inclusion (intake and
  mini-interviews should end with: "KB grew — should the master?").
- A standards doc materially changed (e.g. new CV rules).
- The user asks.

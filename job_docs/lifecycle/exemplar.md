# The exemplar — build it once, sign it off, promote into it

`master_cv.md` is the superset CV: every role and every bullet any application may ever
make, in canonical spellings, ATS-safe per `templates/cv_template.md`. It is **user data** —
it lives at the job-folder root, never in the plugin.

The whole v4 method rests on this one document (ADR-0004). Full rigor is paid here, once,
calmly, outside any deadline — and every application inherits the verdict by trimming
verbatim from it (ADR-0005). Nothing else in the pipeline re-earns it.

| File | What it is |
|---|---|
| `story_bank.md` | The candidate's career in prose — the wider fact set the exemplar is drawn from |
| `master_cv.md` | The exemplar: the subset cleared for documents |
| `master_cv_signoff.md` | The append-only record of what the candidate has read and stood behind |

**Exactly one exemplar, in the search's primary language.** An application in another
language still draws its content from here; the translation happens at assembly and the
translated lines are what the gate judges.

**The cover letter has no exemplar, deliberately** (ADR-0001). A CV is a superset you
subtract from, so verbatim lines stay true across companies. A letter's stable parts are
exactly what makes it swappable between companies — the defect
`standards/cover_letter_rules.md` exists to prevent — and the per-letter anti-slop pass
would strip a reused frame's phrasing anyway.

## The superset invariant

The exemplar holds every claim any application may ever make. Trimming only removes, so a
claim absent from here cannot appear on any CV — which is why an exemplar built thin costs
applications later, and why the build is not the place to be modest.

The bank stays **wider** than the exemplar, and that is correct (ADR-0006). A fact in the
bank but not the exemplar is a decision, not drift: it is material for an interview, not a
line on a CV. There is no sync obligation between the two and no rebuild trigger — if you
find yourself asking "the bank grew, should the exemplar?", the answer is only ever "if the
candidate wants that claim on a CV", which is the promotion decision below.

## Build — one terminal pass, at intake's close

Build **once**, when the candidate declares the interview done (`core/interview_protocol.md`
Phase 5) — never incrementally, and never mid-interview. A document accreted role by role
is a pile; the exemplar has to read as one coherent whole, and it can only be that if it is
written in one pass with the whole bank in view.

1. **Build.** Dispatch `application-writer` with `story_bank.md`, the CV standards
   (`standards/cv_rules.md`, `standards/ats_rules.md`, `templates/cv_template.md`,
   `standards/dach_conventions.md` when the market applies) and the instruction: *exemplar
   only — superset, not tailored.* Every role, every bullet worth ever using, canonical
   spellings, the template skeleton. There is no posting, so there is nothing to mirror or
   subtract, no slot map, and no letter in this run.
2. **Containment check.** Dispatch one `general-purpose` agent with **only** `story_bank.md`
   and `master_cv.md`, both whole, and one question: *does every claim in the exemplar
   appear in the bank, at the same strength?* It returns the exemplar lines that do not, or
   CLEAN.

   This must be a **fresh** dispatch, not the main session. The session that just ran the
   interview remembers what the candidate said, so it will read a claim as supported when
   only the conversation supports it — and the conversation is not an artifact anything
   later can check. Fix every finding by correcting the exemplar or by writing the missing
   support into the bank, then re-run the check.
3. **Sign-off — blocking.** The candidate reads the exemplar end to end and says they stand
   behind every line. Record it in `master_cv_signoff.md`:

   ```markdown
   # Exemplar sign-off

   - 2026-08-11 — full exemplar · sha256 3f9a2c… — read end to end, every line mine
   ```

   The hash is `sha256sum master_cv.md` at the moment of signing. It is what makes the
   sign-off checkable later: edit the exemplar and the recorded hash no longer matches, so
   the sign-off is stale until re-signed.

   **No application may proceed without a current sign-off.** Not for a deadline, not for a
   posting closing tonight, not "just this once" — the sign-off is the candidate's own
   guarantee that they can defend every line in a room, and a deadline is exactly when
   someone would waive it.

## Promotion — the one way content enters the exemplar

Moving a fact from the bank into the exemplar as a new slot. **One mechanism, three
situations**, all identical in procedure:

- a posting exposed a gap the bank can cover (`ats_coverage` bucketed it PROMOTABLE);
- a one-off slot the candidate directed into an application and wants to keep;
- a fact carried over by the superset sweep when migrating a v3 job folder
  (`lifecycle/migration.md`).

The procedure:

1. Write the slot into `master_cv.md` in the right section, in canonical spellings.
2. Run the containment check again — its inputs are cheap to re-read and its judgment is
   scoped to what changed, so only the new slot needs judging.
3. The candidate reads **the new slot** and signs off on it. Append one line to
   `master_cv_signoff.md` naming the slot and the exemplar's new hash.

Only the new slot is judged and only the new slot is read. That is what makes promotion
cheap enough to do on the spot, mid-application, rather than a thing the candidate avoids.

A promotion changes the exemplar's text, so slot ids of the promoted section change and any
edit plan written against the old slot map stops resolving — which is the correct failure,
not a problem to work around. Re-extract the slot map and re-run assembly.

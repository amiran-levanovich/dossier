# Migration — a v3 job folder to the two-artifact model

Run once, in a folder that has a `knowledge/` directory and no `story_bank.md`. It converts
what the v3 interview already established into the v4 pair — a story bank and a signed-off
exemplar — so nothing verified gets re-interviewed. It is **offered, never automatic**: the
user decides when to spend the session, and until they do, the folder keeps working the way
it did.

Nothing is deleted while the migration runs. `knowledge/` stays in place until the sign-off
lands, so an interrupted migration leaves a folder that is still a valid v3 folder.

## Step 1 — Read the folder and say what will happen

One `ls` plus `knowledge/INDEX.md`. Report in a few lines: how many role and project files,
whether `master_cv.md` exists, how many applications are in `applications/`, and the plan
below. Then get a yes before writing anything.

## Step 2 — Knowledge base → story bank

Read every knowledge file **whole** and write `story_bank.md` as prose. This is a
conversion, not a summary: the numbers, the scope, the failures and the motivations all
carry over, and the schema — per-role files, `INDEX.md`, heading anchors — is simply
dropped (ADR-0006). Headings in the bank are for the candidate's navigation and nothing
depends on them.

- **Verified entries carry over as facts.** They went through the v3 gauntlet; re-asking
  would waste the session that built them.
- **`[unverified]` entries do not.** They were CV claims nobody interrogated. They go onto
  `interview_progress.md` as open agenda items, exactly where a seeded claim belongs, or
  the candidate strikes them on the spot. Writing one into the bank would make a hypothesis
  indistinguishable from an interviewed fact — the one thing the intake protocol exists to
  prevent.
- **`portfolio.md`** becomes the bank's portfolio verdicts: each asset, its assessment, and
  the show / fix / don't-link call.
- **`profile.md`** splits: admin facts (location, permit, notice period, languages) into the
  bank, and the header details (name, contact line, the DACH photo/personal-data choices)
  into the exemplar's header in Step 4.

## Step 3 — Search meta to the job-folder root

`goals.md`, `constraints.md` and `lessons.md` move out of `knowledge/` to the job-folder
root, unchanged. They are not candidate facts — they are what the search wants and what it
has learned — and the fit gate reads them there (`core/fit_check.md`). A v3 folder whose
constraints lived inside `profile.md` gets a `constraints.md` written from them.

## Step 4 — The superset sweep

**This is the step that makes the migration necessary rather than cosmetic.** A v3 exemplar
was never required to be complete: the knowledge base was still live at apply time, so the
writer could reach past the exemplar for a claim. Under v4 it cannot — trimming only
removes, so a claim absent from the exemplar cannot appear on any CV. Carried over
untouched, a v3 exemplar violates the superset invariant on day one, and the coverage report
would start calling things `PROMOTABLE` that the candidate demonstrably has.

Dispatch **one `general-purpose` agent** with only `story_bank.md` and `master_cv.md`, both
whole, and one question: *which claims in the bank have no slot in the exemplar?* It returns
a list, not edits.

Fresh dispatch, for the same reason the containment check is fresh: the session that just
converted the bank remembers what it read and will see coverage that isn't there.

Then walk the list with the candidate. Each item is a **promotion decision**, not a defect —
a fact can be legitimately bank-only. For each yes, promote it per `lifecycle/exemplar.md`:
write the slot in canonical spellings, in the right section.

Also fold in the header details from Step 2, and any admin fact the exemplar's logistics
lines need.

## Step 5 — Containment check and sign-off

The migrated exemplar has changed, so it finishes the way a fresh one does
(`lifecycle/exemplar.md`): a fresh containment check over the whole pair, then the
candidate reads the exemplar end to end and signs off in `master_cv_signoff.md` with its
hash.

**Blocking, and not waived for a migration.** A v3 sign-off — if one exists — does not carry
over: it covered a different document. No v4 application runs until this one is recorded.

## Step 6 — Freeze what was already sent

Every existing `applications/<company>/` folder is **frozen as-is**. Do not rebuild, re-verify,
or re-assemble any of it.

- The `cv.md` and `cover.md` in those folders are the historical record of what the employer
  actually received. Regenerating them would destroy that record and prove nothing.
- Their `cv_trace.md`, `cover_trace.md` and `overrides.md` **stop resolving** once `knowledge/`
  is retired. That is expected and harmless: nothing in v4 reads them, and they stay as an
  artifact of how that application was built.
- `.claim_ledger.json` and `master_cv_trace.md` are inert. Leave or delete them; nothing
  reads either.
- **The tracker is untouched.** `tracker.csv` is what analytics and post-mortems read, its
  columns are unchanged (`lifecycle/tracking.md`), and every row stays valid across the
  migration.

## Step 7 — Retire `knowledge/`

Only after the sign-off. Ask the candidate: archive it (rename to `knowledge_v3/`) or delete
it. Archiving is the default — it costs nothing and a converted bank is worth one round of
spot-checking. Either way it stops being read: from here the bank and the exemplar are the
only candidate artifacts, and `job-apply` runs the normal pipeline.

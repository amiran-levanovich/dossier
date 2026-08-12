# Dossier

A self-hosting Claude Code plugin that runs a job search: interview the candidate once into a story bank and a superset CV, then produce per-posting applications by trimming that CV rather than writing a new one. The glossary below is the vocabulary the docs, skills, and agents must all use; general software terms don't belong here.

## The knowledge layer

**Story bank**:
The candidate's career in free-form prose — situations, numbers, failures, motivations — authored once by the intake interview and living in the user's own job folder. The plugin ships none of it.
_Avoid_: knowledge base, profile, corpus, candidate data

**Exemplar**:
`master_cv.md` — the superset CV, built once from the story bank, verified at full rigor, and the sole content source for every application. The cover letter has no exemplar (ADR-0001).
_Avoid_: master document, template, boilerplate

**Containment check**:
The machine half of exemplar verification: a fresh dispatch reads the bank and the exemplar whole and reports any exemplar claim the bank does not support at the same strength. Fresh because the session that ran the interview cannot tell a recorded fact from a remembered one.
_Avoid_: audit, validation, cross-check

**Sign-off**:
The candidate reading the exemplar and stating they stand behind every line, recorded in `master_cv_signoff.md` with the exemplar's hash. Blocking: no application proceeds without a current one, and an edit since signing makes it stale (ADR-0004).
_Avoid_: approval, review, confirmation

**Superset invariant**:
The exemplar holds every claim any application may ever make. Trimming only removes, so a claim absent from the exemplar cannot appear on any CV.
_Avoid_: completeness, full coverage

**Promotion**:
Moving a fact from the story bank into the exemplar as a new slot, making it usable in documents. One mechanism serving three situations: a posting exposing a gap, a one-off slot kept after the fact, and the migration sweep.
_Avoid_: adding, syncing, merging

**Search meta**:
`goals.md`, `constraints.md`, `lessons.md` at the job-folder root — what the candidate *wants* and what the search has learned, as opposed to what they have *done*. The fit gate reads only these; no document ever draws a claim from them.
_Avoid_: preferences, settings, profile

## The production layer

**Application package**:
The two files one posting produces — `cv.md` and `cover.md`. The unit presented to the user.
_Avoid_: application, documents, deliverables

**Slot**:
An addressable unit of the exemplar — a block (one role, project, education, or skills entry, inseparable from its heading and dates) or a bullet inside one. Identified by a hash of its own text.
_Avoid_: anchor, field, placeholder, section

**Slot map**:
The exemplar's slots with their ids and text. The writer's view of the exemplar; it never reads the exemplar itself.
_Avoid_: extract, manifest, index

**Edit plan**:
What the writer emits in place of a CV — an ordering of kept slot ids, plus any one-off slots. It may not reword a slot (ADR-0005). An intermediate, never part of the application package.
_Avoid_: manifest, patch set, diff

**One-off slot**:
Content the user directed into a single application because the exemplar lacked it. Always a new slot, never a rewording of an existing one, and never proposed by the writer unprompted.
_Avoid_: override, exception, patch

**Alias group**:
A set of interchangeable surface spellings for one technology ("PostgreSQL | Postgres"). Assembly may swap between them to match the posting, after the verbatim check (ADR-0008).
_Avoid_: synonym, keyword variant, normalization

**Fact containment**:
The rule holding the letter honest: it may assert no fact the assembled `cv.md` doesn't. Framing, motivation, and company angle are free; numbers, technologies, outcomes, and credentials are not (ADR-0007).
_Avoid_: grounding, provenance, traceability

**Merged attribution**:
The way contained facts still break containment: each appears in `cv.md`, but joined into a claim it doesn't make — one bullet's metric on another's verb, *built* widened to *owns*, a past role written as present. The gate's third finding class; the fix is a split, not a removal.
_Avoid_: conflation, overstatement, embellishment

**Lead evidence**:
The single achievement answering the posting's hardest requirement. The CV surfaces it first and the letter argues from it — one choice, made once, binding both documents.
_Avoid_: main selling point, key achievement

**Anti-slop pass**:
The mandatory prose pass over the letter draft before `cover.md` is written. Uses the `humanizer` skill when the session has it, the checklist in `standards/cover_letter_rules.md` when it doesn't. The pass never skips; only its instrument is optional.
_Avoid_: humanizing, polish, style pass

**The gate**:
`application-verifier`. One round per application, judging the letter's fact containment and any one-off slot. It returns CLEAN or severity-ordered findings and never edits.
_Avoid_: review step, QA, checker

## The maintenance layer

**Advised skill**:
A third-party or Anthropic skill that raises quality for one role but is never required. The plugin assumes nothing is installed and never blocks on absence.
_Avoid_: dependency, required skill, integration

**Budget row**:
A line in `TOKEN_ECONOMY.md` §5 capping a per-run doc's token count, parsed and enforced by `scripts/release_audit.py`. A file may exceed its row only with an `audit-ok: C7` marker stating why.
_Avoid_: token limit, quota

## Retired terms

**Knowledge base**, **verified entry**, **`[unverified]` marker**, **trace file**, **override**, **round cap** — *retired in v4.0.0*:
The schema'd `knowledge/` directory, its per-claim `file#anchor` trace sidecars, the per-entry verification marker, the per-application override file, and the three-round verifier loop. Replaced by the story bank, the superset invariant, the containment check and sign-off, and the one-off slot (ADR-0004, ADR-0006). The marker's job is now structural: only interrogated material enters the bank, and the exemplar is built in one pass after the interview closes. Do not reintroduce the concepts or the terms.

**Cover frame** — *retired in v3.0.0*:
The removed cover-letter exemplar (`cover_frame.md`); see ADR-0001.

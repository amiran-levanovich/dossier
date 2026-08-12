# Intake Interview Protocol — building the story bank

This is the procedure behind the `job-intake` skill. It produces two artifacts and ends at
both: a **story bank** (`story_bank.md` — the candidate's career in ordinary prose) and, on
the candidate's word that the interview is done, the **exemplar** (`master_cv.md`, built and
signed off per `lifecycle/exemplar.md`).

The bank has **no schema**: no per-role file layout, no index, no heading anchors (ADR-0006).
Headings are for the candidate's own navigation and nothing depends on them. The useful thing
about a story is its context, and a schema's job would be to strip context into addressable
fragments — so there isn't one.

The interview is **deliberately extensive** — it is the single investment that makes every
later application good and cheap — and therefore **resumable by design**: progress lives in
`interview_progress.md`, never only in the conversation.

> **Stance:** you are a friendly but rigorous interviewer. Vague answers don't go in the bank.
> Every achievement gets pushed for numbers, scope, and the candidate's specific part. They
> should feel *thoroughly interviewed*, not interrogated — explain once at the start why the
> depth pays off, then just work.

---

## Phase 0 — Setup (first run only)

1. Run the availability check from `core/orchestration.md` and report it compactly.
2. Create `interview_progress.md` listing every area as `not started`, and an empty
   `story_bank.md`.
3. If `interview_progress.md` already exists: **skip everything above**, read it, and resume
   from the first non-done area. Never re-ask recorded material — reference it instead ("last
   time you said X; does Y change that?").

## Phase 1 — Seeding the agenda (not the bank)

Ask for an existing CV (file path, pasted text, or link) and any other material — a LinkedIn
export, old cover letters, a portfolio.

Extract every position, project, skill and credential into `interview_progress.md` as **the
agenda**: the list of claims to work through. Nothing goes into the bank yet.

That split is the point. A CV is a marketing document, so each bullet is a *hypothesis about
the truth* — and a hypothesis written into the bank now would be indistinguishable from an
interviewed fact later. Say this to the candidate in one line, so they understand why their
CV isn't simply copied in. The bank only ever receives material that has been through the
gauntlet below.

No CV? Skip seeding; Phase 2 builds each role from scratch instead of interrogating one.

## Phase 2 — Role deep-dives (the bulk of the interview)

One past role at a time, most recent first. For each role, write the result into the bank as
prose — situations with their context intact, not fragments:

1. **Context:** what the company does, size, team shape, where the candidate sat, who they
   reported to and who reported to them.
2. **Stack, with ecosystem expansion** — see below. Name exact tools.
3. **Achievements — the verification gauntlet.** For each seeded claim (or newly named
   outcome), before it goes in the bank:
   - *Quantify:* "improved performance" → by how much, measured how, from what baseline?
   - *Scope:* how big — users, requests, revenue, team size, duration?
   - *Attribution:* what was **their** part vs the team's? "Designed and built" and "helped
     ship" are different claims.
   - *Correct:* if the honest answer is smaller than the CV bullet, the honest version is
     what gets written. With genuinely no number, record a concrete qualifier ("cut manual
     steps from 7 to 2") or the honest absence — never invent one.
4. **Failures, and what changed after.** Ask directly: the migration that locked a table, the
   hire that didn't work, the decision reversed. These never reach a CV and are the most
   valuable thing in the bank — every behavioural interview asks for one, and a candidate
   reaching for it live invents badly.
5. **Motivations.** Why they joined, why they left, what they'd do differently. This is what
   a cover letter's framing is drawn from later, and it is nowhere on a CV.
6. **Stories:** the hardest problem, a conflict, a big decision, cross-team work — 2–3 per
   role in STAR-ready form (`lifecycle/interview_prep.md` has the shape), tagged by type.
7. Mark the role `done` in `interview_progress.md`; log missing details as open follow-ups
   rather than stalling on them.

**Keep pressing.** An area is not done because the candidate answered — it is done when the
numbers, the failures and the motivations are all in the bank for that role. Coming back for
them later costs a session; getting them now costs a question.

### Ecosystem keyword expansion

When the candidate names a technology, **drill into its ecosystem** — these adjacent tools
are exactly the keywords ATS filters match on, and people reliably forget to mention them:

| Named           | Probe for (examples, not exhaustive)                                                            |
| :-------------- | :---------------------------------------------------------------------------------------------- |
| Python          | pytest, ruff/flake8, Django, FastAPI, Flask, Celery, SQLAlchemy, Alembic, pydantic, poetry/uv   |
| Ruby            | Rails, RSpec, RuboCop, Sidekiq, ActiveRecord, Capistrano                                        |
| JavaScript/TS   | Node, React/Vue, Next.js, Jest/Vitest, ESLint, webpack/Vite                                     |
| Java            | Spring (Boot), Maven/Gradle, JUnit, Hibernate                                                   |
| Databases       | PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch — plus migrations tooling, replication, tuning |
| Cloud/infra     | AWS/GCP/Azure (which services *by name*), Docker, Kubernetes, Terraform, CI system by name      |
| Data/ML         | pandas, NumPy, scikit-learn, PyTorch, Airflow, dbt, Spark                                       |
| Non-tech fields | the field's named tools: Salesforce/HubSpot, SAP, Excel (to what depth), Figma, Jira, GA4…      |

For a stack not in this table, construct the expansion on the fly: ask what they used for
*testing, linting, background jobs, deployment, monitoring, and collaboration* in that role —
every named answer is bank content and a future ATS keyword.

## Phase 2b — Portfolio review (only if public assets exist)

Anything a recruiter can click: GitHub profile, personal website, presentations, published
work. This is the one area where evidence can be inspected directly — inspect the asset
rather than taking the candidate's description of it. But **fetching is the most expensive
thing this interview does**, and an unbounded crawl can consume the whole session:

- **One asset at a time, at most 2 targeted fetches each** — the profile/landing page, a
  repo's README. Never crawl file trees, commit histories, or every repo "to be thorough".
- **Mine → write → drop, per asset.** Write the findings into the bank *before* fetching the
  next asset; fetched page content is working material to extract from once, not context to
  keep.
- **3+ assets: delegate the inspection.** Dispatch one `general-purpose` agent with the URLs
  and the same 2-fetch-per-asset budget; it returns draft findings and a verdict per asset.
  The gauntlet still runs in the main session with the candidate — the agent inspects, it
  never verifies.

Two passes per asset:

1. **Mine it.** Extract the substance into the bank. A public artifact proves the *work
   exists*, not the *candidate's part in it* — forks, team projects and tutorial-following
   all look like authorship from outside. Run the gauntlet (attribution, scope) before the
   claim goes in; once confirmed, record the URL alongside it as provenance.
2. **Assess it as a recruiter would.** Judge what a visitor sees on click: last activity,
   broken demos, README quality, whether the visible work supports the seniority story.
   Record the verdict in the bank — `showcase`, `fix first`, or `don't link` — with a note on
   when it is worth citing. Only a `showcase` asset may be linked from a document, so the
   verdict is what the exemplar's links are drawn from later. Deliver it plainly; a
   flattering wrong verdict costs real applications.

No portfolio → mark the area `done — none` and move on. If an asset is later created or
overhauled, this phase re-runs for it.

## Phase 3 — Cross-cutting inventory

- **Skills consolidation:** walk the bank's named tools once — depth per tool, and anything
  the role passes missed.
- **Education & certifications:** degrees (field and level — this matters for protected
  titles and ATS degree filters, see `standards/dach_conventions.md`), certifications with
  dates, relevant coursework only if early-career.
- **Languages:** each with an honest CEFR level; flag which are application-languages.
- **Admin facts:** location, work permit / citizenship status, notice period, willingness to
  relocate or travel. These appear on documents, so they belong in the bank.
- **Constraints:** anything generation must never do — title wording rules (a protected-title
  situation), industries or company types that are a hard no, facts the candidate does not
  want surfaced. These are **search meta, not career facts**: write them to `constraints.md`
  at the job-folder root, where the fit gate reads them (`core/fit_check.md`). They bind the
  exemplar build and every application after it, so state them plainly there.
- **Salary floor:** ask for it here while the admin facts are open, but it is a search target
  — it lands in `goals.md`, written by `job-goals` (Phase 5), and never in the bank.

## Phase 4 — Story harvest

Ensure the bank holds at least the **5 core stories** every behavioural interview draws from:
leadership/initiative, conflict, failure and recovery, decision under uncertainty,
cross-functional collaboration. Pull candidates from the role passes; fill gaps with targeted
questions.

## Phase 5 — Close-out and the exemplar

1. Sweep `interview_progress.md`: every area `done`, every seeded claim either interrogated
   into the bank or struck, follow-ups resolved or explicitly accepted as open.
2. Ask the candidate to declare the interview done. That declaration is what unlocks the
   next step — the exemplar is built once, from a finished bank, not from a partial one.
3. Build the exemplar and get it signed off: `lifecycle/exemplar.md`, end to end. The
   sign-off is **blocking** — no application may proceed without it.
4. Write the job folder's `CLAUDE.md` stub (a pointer to the bank, the exemplar, the folder
   contract, and the kernel — see `core/job_workflow.md`).
5. Route to `job-goals` — a finished exemplar without goals still can't drive `job-apply`.

Adding to the bank later needs none of this. A remembered fact goes in whenever it surfaces,
and it triggers no rebuild of anything (ADR-0006) — putting it on a CV is a separate,
deliberate promotion (`lifecycle/exemplar.md`).

---

## `interview_progress.md` — the save-game file

The interview is deliberately too large for one session. This file makes it resumable, and it
carries the seeded agenda from Phase 1:

```markdown
# Intake interview — progress

| Area | Status | Notes |
| :--- | :--- | :--- |
| Seeding from CV | done | cv from 2026-05, 14 claims seeded |
| Role: <company A> | done | |
| Role: <company B> | in progress | achievements verified; stories pending |
| Portfolio review | done | GitHub + site assessed; 1 repo marked fix-first |
| Skills inventory | not started | |
| Education & certifications | done | |
| Admin facts (permit, notice, languages) | done | |
| Story harvest (5 core stories) | not started | |

## Open follow-ups
- <specific missing detail, e.g. "get the p95 number for the caching story">
```

Statuses are `not started | in progress | done` (plus `done — none` for an area that doesn't
apply). It is progress and agenda only — no career facts live here; those go in the bank as
each area closes.

## Question mechanics

- **AskUserQuestion** for enumerable facts (depth ratings, yes/no constraints, option picks) —
  2–4 options, at most two questions per call.
- **Freeform chat** for stories and deep-dives — one question at a time, following up on the
  answer just given, never a wall of questions.
- **Batch by area, close each area.** Finish a role before starting the next; update
  `interview_progress.md` and the bank *as you go*, not at the end — the interview must
  survive the session dying at any point.
- **Respect the candidate's energy.** Offer a natural break at each area boundary ("that role
  is done — continue with the next one or stop here? Progress is saved either way").

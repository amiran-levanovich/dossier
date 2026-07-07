# Intake Interview Protocol — building the knowledge base

This is the procedure behind the `job-intake` skill. Its output is the knowledge base defined in `core/kb_schema.md`. The interview is **deliberately extensive** — it is the single investment that makes every later tailoring run good — and therefore **resumable by design**: progress state lives in `knowledge/interview_progress.md`, never only in the conversation.

> **Stance:** you are a friendly but rigorous interviewer. Vague answers don't go in the book. Every achievement gets pushed for numbers, scope, and the user's specific part. The user should feel *thoroughly interviewed*, not interrogated — explain once at the start why the depth pays off, then just work.

---

## Phase 0 — Setup (first run only)

1. Run the availability check from `core/orchestration.md` and report it compactly.
2. Create `knowledge/` with empty `INDEX.md` and `interview_progress.md` listing all areas as `not started`.
3. If `knowledge/interview_progress.md` already exists: **skip everything above**, read it, and resume from the first non-done area. Never re-ask recorded material — reference it instead ("last time you said X; does Y change that?").

## Phase 1 — Seeding

Ask for an existing CV (file path, pasted text, or link) and any other material — LinkedIn profile export, old cover letters, a portfolio.

- Extract every position, project, skill, and credential into the KB layout.
- **Mark every seeded entry `[unverified]`.** A CV is a marketing document — treat each bullet as a *hypothesis about the truth*, to be confirmed, quantified, corrected, or struck in Phase 2. Say this to the user in one line so the markers don't surprise them.
- No CV? Skip seeding; Phase 2 builds each role file from scratch instead of verifying one.

## Phase 2 — Role deep-dives (the bulk of the interview)

One past role at a time, most recent first. For each role, work through:

1. **Context:** what the company does, size, team shape, where the user sat, who they reported to and who reported to them.
2. **Stack, with ecosystem expansion** — see below. Record exact tool names in the role file's Stack line.
3. **Achievements — the verification gauntlet.** For each seeded bullet (or newly claimed outcome):
   - *Quantify:* "improved performance" → by how much, measured how, from what baseline?
   - *Scope:* how big — users, requests, revenue, team size, duration?
   - *Attribution:* what was **your** part vs the team's? "Designed and built" and "helped ship" are different bullets.
   - *Correct:* if the honest answer is smaller than the CV bullet, write the honest version. If the user genuinely has no number, record a concrete qualifier ("cut manual steps from 7 to 2") or the honest absence — never invent one.
   - Then remove the `[unverified]` marker, or strike the entry if it doesn't survive.
4. **Stories:** the hardest problem, a conflict, a failure, a big decision, cross-team work — capture 2–3 per role in STAR-ready form (see `lifecycle/interview_prep.md` for the format), tagged by type.
5. Mark the role `done` in `interview_progress.md`; log any missing details as open follow-ups rather than stalling on them.

### Ecosystem keyword expansion

When the user names a technology, **drill into its ecosystem** — these adjacent tools are exactly the keywords ATS filters match on, and users reliably forget to mention them:

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

For a stack not in this table, construct the expansion on the fly: ask what the user used for *testing, linting, background jobs, deployment, monitoring, and collaboration* in that role — every named answer is a KB skill entry and a future ATS keyword. Each confirmed tool goes into `skills.md` with depth and provenance.

## Phase 3 — Cross-cutting inventory

- **Skills consolidation:** walk `skills.md` once — depth rating per tool, catch anything the role passes missed.
- **Education & certifications:** degrees (field and level — this matters for protected titles and ATS degree filters, see `standards/dach_conventions.md`), certifications with dates, relevant coursework only if early-career.
- **Languages:** each with an honest CEFR level; flag which are application-languages.
- **Admin facts** (into `profile.md`): location, work permit / citizenship status, notice period, salary floor, willingness to relocate/travel.
- **Constraints** (into `constraints.md`): anything generation must never do — title wording rules (e.g. a protected-title situation), industries or company types that are a hard no, facts the user does not want surfaced.

## Phase 4 — Story harvest

Ensure the KB holds at least the **5 core stories** every behavioural interview draws from: leadership/initiative, conflict, failure and recovery, decision under uncertainty, cross-functional collaboration. Pull candidates from the role files' Stories sections; fill gaps with targeted questions. Each lives in the most relevant role file.

## Phase 5 — Close-out

1. Sweep `interview_progress.md`: every area `done`, follow-ups either resolved or explicitly accepted as open by the user.
2. Sweep the KB for surviving `[unverified]` markers — resolve or strike them.
3. Regenerate `INDEX.md` hooks so each line genuinely describes its file.
4. Write the job folder's `CLAUDE.md` stub (pointer to `knowledge/`, the folder contract, and the kernel — see `core/job_workflow.md`).
5. Route to `job-goals` — a finished KB without goals still can't drive `job-apply`.

---

## Question mechanics

- **AskUserQuestion** for enumerable facts (depth ratings, yes/no constraints, option picks) — 2–4 options, at most two questions per call.
- **Freeform chat** for stories and deep-dives — one question at a time, follow up on the answer just given, never a wall of questions.
- **Batch by area, close each area.** Finish a role before starting the next; update `interview_progress.md` and the KB files *as you go*, not at the end — the interview must survive the session dying at any point.
- **Respect the user's energy.** Offer a natural break at each area boundary ("that role is done — continue with the next one or stop here? Progress is saved either way").

# Knowledge Base Schema — the distributed candidate dossier

The knowledge base (KB) is the system's memory about the candidate. It lives in the user's job folder under `knowledge/` — **never** inside the plugin — and follows one design rule:

> **One file, one topic, plus an index.** Agents read `INDEX.md` first and pull only the files relevant to the task at hand. No monolithic dossier: a tailoring run for a backend role should load two role files and a skills file, not the candidate's whole life.

## Layout

```
knowledge/
├── INDEX.md                 # one line per file — the entry point for every agent
├── profile.md               # hard facts: contact, location, languages + levels, work permit,
│                            #   notice period, salary floor, education, certifications
├── constraints.md           # hard rules and red lines — things generation must never violate,
│                            #   plus hard-yes / hard-no lists (industries, company types, setups)
├── goals.md                 # search targets: titles, seniority, locations, remote policy,
│                            #   salary target — written and updated by the job-goals skill
├── interview_progress.md    # the intake interview's save-game file (see below)
├── portfolio.md             # asset register: every public artifact a recruiter can click,
│                            #   with an assessment and a show/fix/don't-link verdict (see below)
├── lessons.md               # cross-application learning log — written by post-mortems and
│                            #   interview debriefs, read before diagnosing or applying (see below)
├── roles/<company>.md       # one file per past position
├── projects/<name>.md       # one file per side project / notable non-employment work
└── skills.md                # skill inventory with depth and provenance
```

## `INDEX.md` — the contract

One line per KB file: relative path, an em-dash, a hook that lets an agent decide relevance without opening the file.

```markdown
- roles/acme.md — Senior backend dev 2021–2025: Rails APIs, B2B SaaS, perf work, team of 5
- skills.md — full inventory: Ruby/Rails deep, Python working, PostgreSQL, Redis, CI
- constraints.md — hard rules: title wording, industries to avoid  (ALWAYS read)
- lessons.md — search learning log: 6 lessons, 1 open (degree-filter targeting)
```

Rules:
- **Same-edit updates.** Any change to a KB file updates its `INDEX.md` line in the same working step. A stale index silently hides knowledge from every future run.
- `profile.md`, `constraints.md`, and `goals.md` are marked `(ALWAYS read)` — they are small and every consumer needs them.

## Verification status — claims vs knowledge

A CV — including the user's own — is marketing material, not testimony. Anything seeded from an existing CV or other unexamined source enters the KB as a **claim**, not a fact:

- Seeded entries carry the marker `[unverified]` on the entry line.
- The intake interview interrogates each one — metrics? scope? the user's part vs the team's? — and either rewrites it as verified (corrected where the original was hyperbole) or strikes it.
- Verified entries carry no marker; verification is the default state of the KB at rest.
- **`job-apply` and its agents must not use `[unverified]` entries for tailoring.** If a relevant entry is unverified, the tailoring run flags it so the user can verify it on the spot (a 2-minute mini-interview) or drop it.

## Role files — `roles/<company>.md`

The unit of tailoring. Template:

```markdown
# <Company> — <Title> (<start> – <end>)

**Context:** what the company does, size, the team's shape and the user's place in it
**Stack:** exact tool names — language, frameworks, datastores, infra, CI (see ecosystem
  expansion in core/interview_protocol.md; these are the ATS keywords)

## Achievements
- <outcome with metric, scope, and the user's specific contribution>
- ...

## Stories
- <STAR-ready story: situation → task → action → result, 3–5 lines, tagged
  (leadership | conflict | failure | decision | collaboration)>

## Notes
- <anything else: reason for leaving, references, open follow-ups>
```

Every achievement records **the user's part explicitly** ("designed and built X" vs "was on the team that shipped X") — the difference between an honest bullet and an inflated one lives exactly there.

## `skills.md`

One section per skill area; each named tool gets: depth (`deep` / `working` / `used` / `ramping`), where it was used (link the role file), and last used when. Exact tool names only — "testing frameworks" is not a skill entry, `pytest` is.

## `portfolio.md` — the asset register

Everything public a recruiter can click: GitHub profile, personal website, presentations, published work. One entry per asset:

```markdown
## <Asset name> — <URL>
**Demonstrates:** <what it actually shows — honestly, not aspirationally>
**Condition:** <what a visitor sees today: last activity, broken demos, README quality> (assessed <date>)
**Verdict:** showcase | fix first | don't link
**Cite when:** <which posting types this helps — and which it would hurt>
```

Rules:
- **The register stores the assessment, not the content.** Substantial pieces mined from a portfolio get their own `projects/<name>.md`; repo contents go stale on the next push, so only the verdict and its date live here.
- An artifact proves the *work exists*, not the *user's part in it* — authorship still goes through the interview's verification gauntlet (`core/interview_protocol.md`). Once confirmed, the URL is recorded as provenance: inspectable evidence beats interview-only testimony.
- **Verdicts drive links.** Generated documents may only link assets marked `showcase` (see `standards/cv_rules.md`); the `application-verifier` enforces this.
- Re-assess after any meaningful change to an asset — a stale verdict misleads exactly like a stale index.

## `lessons.md` — the learning log

What the *search* has taught, one line per lesson, newest first — so a diagnosis made once is never made from scratch again:

```markdown
# Lessons — cross-application learning log

- 2026-07-08 [hard-filter] betacorp: strict CS-degree ATS filter → goals.md targeting now avoids degree-gated postings (applied)
- 2026-07-05 [interview] acme: wobbled on DB indexing depth in the tech round → refresh before every Rails tech screen; story sharpened in roles/oldco.md (applied)
- 2026-07-02 [keyword-gap] gammasoft: posting named "Sidekiq", KB only had "background jobs" → added to skills.md (applied)
```

Format: `- <date> [<category>] <company>: <what was learned> → <action taken> (applied | open)`. Categories: `keyword-gap | hard-filter | seniority | volume | format | screen-fit | interview | process`.

Rules:
- **Writers**: the post-mortem (`lifecycle/postmortem.md` Step 3) and the interview debrief (`lifecycle/interview_prep.md`) — every rejection and every debrief lands exactly one line.
- **Readers**: the next post-mortem before diagnosing (a repeated diagnosis escalates instead of re-fixing), the `job-apply` fit gate (`core/fit_check.md` — known-fatal patterns kill the application before anything is built), and `lifecycle/analytics.md` (lessons corroborate the numbers).
- `(open)` = the action wasn't applied on the spot — that is a debt; analytics and the next post-mortem surface open lessons until they're applied or consciously dropped.
- Lessons record judgments about the **search**, not facts about the candidate — candidate facts go into the role/skills files as always; a lesson may point at the KB edit it caused.
- **Orchestrator context only**: `lessons.md` is never passed to the writer agents — every CV/letter claim still traces to verified KB entries.

## `interview_progress.md` — the save-game file

The intake interview is deliberately too large for one session. This file makes it resumable:

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

`job-intake` reads this file first on every run and continues from the first non-done area — it never re-asks what is already recorded. When every area is `done` and no follow-ups remain, the interview is complete and the file says so on its first line.

## Hygiene

- English throughout (generated documents translate at write time; the KB stays single-language).
- Dates absolute, never relative.
- Update the KB whenever new facts surface — mid-application, in a post-mortem, during prep. The session-close checklist in `core/job_workflow.md` enforces this.
- The KB stays true. User-directed embellishments for a specific application live in that application's `overrides.md`, never here (see `core/tailoring_method.md`).

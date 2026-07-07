# job-workflow

> Part of the [**claude_setup**](../README.md) marketplace. Sibling plugins: [**dev-workflow**](../dev-workflow/README.md) (code) · [**craft-workflow**](../craft-workflow/README.md) (design, content, research).

A Claude Code plugin that runs a **job search** with the same discipline its siblings bring to code and craft: build deep, *verified* knowledge before producing anything, define the bar before writing, and gate every output. Per job posting, sub-agents produce an ATS-safe tailored CV and a company-specific cover letter — and a verifier agent blocks anything that can't be traced back to what the candidate actually did.

Built for the European market, with first-class **DACH** (Germany/Austria/Switzerland) conventions.

---

## The one idea

A tailored application is only as good as what the system **actually knows** about the candidate. So the workflow front-loads an extensive interview into a distributed knowledge base, and every generated claim must **trace** to a verified entry in it. Tailoring without the knowledge base is guessing — the pipeline refuses to guess.

## How it works

1. **`job-intake`** — the big interview. Seeds a knowledge base from the existing CV, then interrogates every claim (a CV is marketing, not testimony): metrics, scope, the user's part vs the team's. Drills into tool ecosystems ("Python" → pytest, ruff, Django, Celery… — exactly the keywords ATS filters match). Inspects portfolio assets (GitHub, website, published work) directly and records a show/fix/don't-link verdict per asset — what a recruiter sees on click is evidence too, in both directions. Deliberately too extensive for one sitting, and therefore **resumable by design**: progress lives in `knowledge/interview_progress.md`, and every session continues where the last one stopped.
2. **`job-goals`** — targets: titles, seniority, locations, remote policy, salary, hard-yes/hard-no lists. Small and re-runnable.
3. **`job-apply`** — the production line. Posting in (URL or pasted text) → requirement breakdown → ATS keyword check *before writing anything* → company research → two sub-agents in parallel (**cv-tailor**, **cover-letter-writer**) → the **application-verifier** gate, looped fix→re-verify until CLEAN → tracker updated.

The knowledge base it builds (in *your* job folder — the plugin ships zero personal data):

```
knowledge/
├── INDEX.md               # agents read this first, pull only what's relevant
├── profile.md             # hard facts: permit, notice period, languages, education
├── constraints.md         # hard rules (e.g. protected-title wording) — always read
├── goals.md               # search targets
├── interview_progress.md  # the interview's save-game file
├── portfolio.md           # asset register: per clickable asset, a verdict — showcase / fix first / don't link
├── roles/<company>.md     # one per position: stack, verified achievements, STAR stories
├── projects/<name>.md
└── skills.md              # exact tool names with depth + provenance
```

## Honesty model

- **Verified knowledge only.** Entries seeded from a CV are `[unverified]` claims until the interview confirms, corrects, or strikes them; unverified entries never feed tailoring.
- **Traceability.** Every claim in a generated CV/letter maps to a KB entry in a sidecar trace file; the verifier flags untraceable or inflated claims as BLOCKERs.
- **The user outranks the rule.** If the user explicitly asks to include something the KB can't back, the workflow warns once (concretely, no moralizing), confirms, gets the details, and records it as a `user-directed` override in that application's folder — the KB itself stays true. Agents never volunteer fabrication.

## Skills

| Skill        | When it triggers                                              |
| :----------- | :------------------------------------------------------------ |
| `job-intake` | Building/extending the knowledge base; resuming the interview |
| `job-goals`  | Setting or revising search targets                            |
| `job-apply`  | A posting arrives — the full tailoring pipeline               |

## Agents

| Agent                  | Role                                                                    |
| :--------------------- | :---------------------------------------------------------------------- |
| `cv-tailor`            | Tailored ATS-safe `cv.md` + `cv_trace.md` from selected KB files        |
| `cover-letter-writer`  | 6-part, <300-word, company-specific `cover.md` + trace                  |
| `application-verifier` | The gate: traceability, ATS, standards — CLEAN or findings; never edits |

## The docs layer (`job_docs/`)

| Doc                                          | What it holds                                                                       |
| :------------------------------------------- | :---------------------------------------------------------------------------------- |
| `core/job_workflow.md`                       | The kernel: folder contract, session start/close, routing, quality model            |
| `core/kb_schema.md`                          | Knowledge base layout, INDEX contract, verification markers                         |
| `core/interview_protocol.md`                 | The extensive interview: phases, verification gauntlet, ecosystem expansion         |
| `core/tailoring_method.md`                   | The per-application pipeline, agent dispatch, verifier loop, override protocol      |
| `core/orchestration.md` · `core/quickref.md` | Advised skills + availability check · the 10-rule floor                             |
| `standards/`                                 | `cv_rules` · `ats_rules` · `cover_letter_rules` · `dach_conventions` · `rendering`  |
| `lifecycle/`                                 | `tracking` (tracker.csv) · `postmortem` (rejections) · `interview_prep` (per-stage) |
| `templates/cv_template.md`                   | The ATS-safe single-column skeleton                                                 |

## European / DACH specifics

Language follows the posting (German posting → Lebenslauf + Anschreiben); protected titles ("Ingenieur") are hard rules the verifier blocks on; the logistics close always carries permit status and notice period; photo/birth-date are the user's recorded choice, asked once at intake; Austrian KV-minimum and Swiss permit/salary conventions covered. Details: [`job_docs/standards/dach_conventions.md`](./job_docs/standards/dach_conventions.md).

## Output format

**Markdown is the deliverable.** Rendering (PDF via the `pdf` skill or pandoc, docx, or a transfer block for an external designed-CV builder) happens only on request — options and ATS caveats in [`job_docs/standards/rendering.md`](./job_docs/standards/rendering.md).

## Install

```
/plugin marketplace add amiran-levanovich/claude_setup
/plugin install job-workflow@claude-setup
```

Then, in your job folder: run `job-intake` and block out a coffee's worth of time — the interview is the investment everything else pays back.

## What it deliberately does **not** have

- **No pre-commit hook, no fixer agents** (same stance as `craft-workflow`) — application quality is a judgment; enforcement is the verifier gate and the traceability contract.
- **No personal data in the plugin.** The knowledge base, tracker, and applications live in your own job folder; the plugin ships only method, standards, and templates.

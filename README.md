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
3. **`job-apply`** — the production line. Posting in (URL or pasted text) → requirement breakdown → the **fit gate** (liveness check, a binary constraints screen, a 1–5 fit score where every dimension cites its evidence, and a signals-based legitimacy tier — a weak or fishy posting gets said out loud *before* a minute is spent producing for it; the user's override always wins and is recorded) → ATS keyword check *before writing anything* → company research → two sub-agents in parallel (**cv-tailor**, **cover-letter-writer**) → the **application-verifier** gate, looped fix→re-verify until CLEAN → tracker updated with the fit score.

When an interview gets booked, the workflow routes to `lifecycle/interview_prep.md`: the session refreshes the company/interviewer research, then the **interview-briefer** agent builds a stage-specific `prep.md` with fresh eyes — prepped against what was *actually claimed* to that company (overrides included), with rusty-risk topics and gaps flagged honestly. When an **offer** arrives, `lifecycle/offer.md` takes over: a contract-reading companion (describe-don't-judge — a clause-by-clause walk with neutral tags against the DACH clause taxonomy, promises-vs-paper reconciliation, and two strictly separated question lists: clarifications for the employer, everything legal for a lawyer — the companion never states law or judges enforceability), then negotiation prep that positions the offer against `goals.md` and the fit gate's own comp research, anchors arguments in KB-traced achievements, and drafts replies without ever sending them. Contract text is the most sensitive input the workflow touches: it never goes to a sub-agent or into a web query — this stage runs entirely in the main session against local files. (The contract-reading companion adapts ideas from *career-ops*' offer-prep skill, itself building on Anthropic's *claude-for-legal* — credit to both.) And across applications, `lifecycle/analytics.md` reads the whole tracker — funnel, where applications die, pace — and turns a rejection pattern into one concrete strategy adjustment instead of another per-application fix. The loop closes through `knowledge/lessons.md`: every rejection post-mortem and interview debrief lands one lesson line, and the fit gate reads them back before the next application gets built — a diagnosis made once is never made from scratch again. The gate's scores land in the tracker too, so analytics can tell whether the scoring itself is calibrated.

The knowledge base it builds (in *your* job folder — the plugin ships zero personal data):

```
knowledge/
├── INDEX.md               # agents read this first, pull only what's relevant
├── profile.md             # hard facts: permit, notice period, languages, education
├── constraints.md         # hard rules (e.g. protected-title wording) — always read
├── goals.md               # search targets
├── interview_progress.md  # the interview's save-game file
├── portfolio.md           # asset register: per clickable asset, a verdict — showcase / fix first / don't link
├── lessons.md             # learning log: every post-mortem and debrief lands one lesson, reread before applying
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

| Agent                  | Role                                                                     |
| :--------------------- | :----------------------------------------------------------------------- |
| `cv-tailor`            | Tailored ATS-safe `cv.md` + `cv_trace.md` from selected KB files         |
| `cover-letter-writer`  | 6-part, <300-word, company-specific `cover.md` + trace                   |
| `application-verifier` | The gate: traceability, ATS, standards — CLEAN or findings; never edits  |
| `interview-briefer`    | Stage-specific interview `prep.md` — claims-aware, gaps flagged honestly |

## The docs layer (`job_docs/`)

| Doc                                          | What it holds                                                                                                         |
| :------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------- |
| `core/job_workflow.md`                       | The kernel: folder contract, session start/close, routing, quality model                                              |
| `core/kb_schema.md`                          | Knowledge base layout, INDEX contract, verification markers                                                           |
| `core/interview_protocol.md`                 | The extensive interview: phases, verification gauntlet, ecosystem expansion                                           |
| `core/tailoring_method.md`                   | The per-application pipeline, agent dispatch, verifier loop, override protocol                                        |
| `core/fit_check.md`                          | The pre-application gate: liveness, constraints kill-switch, evidence-cited fit score, comp-reliability weighting, legitimacy tier |
| `core/orchestration.md` · `core/quickref.md` | Advised skills + availability check · the 10-rule floor                                                               |
| `standards/`                                 | `cv_rules` · `ats_rules` · `cover_letter_rules` · `dach_conventions` · `rendering`                                    |
| `lifecycle/`                                 | `tracking` (tracker.csv) · `postmortem` (rejections) · `interview_prep` (per-stage) · `analytics` (funnel + patterns) · `offer` (contract read + negotiation prep) |
| `templates/cv_template.md`                   | The ATS-safe single-column skeleton                                                                                   |

## European / DACH specifics

Language follows the posting (German posting → Lebenslauf + Anschreiben); protected titles ("Ingenieur") are hard rules the verifier blocks on; the logistics close always carries permit status and notice period; photo/birth-date are the user's recorded choice, asked once at intake; Austrian KV-minimum and Swiss permit/salary conventions covered; a contract clause taxonomy (Probezeit, Kündigungsfrist, 13th salary, non-compete with compensation, …) equips the offer stage's clause walk — as market patterns, never legal statements. Details: [`job_docs/standards/dach_conventions.md`](./job_docs/standards/dach_conventions.md).

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

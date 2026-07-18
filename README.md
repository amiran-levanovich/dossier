# dossier

> Sibling plugins, same method, separate repos: [**redgreen**](https://github.com/amiran-levanovich/redgreen) (code) · [**atelier**](https://github.com/amiran-levanovich/atelier) (design, content, research). Formerly `job-workflow` in the `claude_setup` marketplace.

A Claude Code plugin that runs a **job search** with the same discipline its siblings bring to code and craft: build deep, *verified* knowledge before producing anything, define the bar before writing, and gate every output. Per job posting, sub-agents produce an ATS-safe tailored CV and a company-specific cover letter — and a verifier agent blocks anything that can't be traced back to what the candidate actually did.

Built for the European market, with first-class **DACH** (Germany/Austria/Switzerland) conventions.

---

## The one idea

A tailored application is only as good as what the system **actually knows** about the candidate. So the workflow front-loads an extensive interview into a distributed knowledge base, and every generated claim must **trace** to a verified entry in it. Tailoring without the knowledge base is guessing — the pipeline refuses to guess.

## How it works

Three skills, in order — each builds what the next one needs:

```
        (once; resumable)      (small; re-runnable)     (per posting)
        ┌────────────┐         ┌───────────┐         ┌───────────┐
CV ───▶ │ job-intake │ ──────▶ │ job-goals │ ──────▶ │ job-apply │ ◀─── posting
        └─────┬──────┘         └─────┬─────┘         └─────┬─────┘
              ▼                      ▼                     ▼
         knowledge/              goals.md         applications/<company>/
        (verified KB)        (search targets)     (CV + letter + traces)
```

1. **`job-intake`** — the big interview. Seeds a knowledge base from the existing CV, then interrogates every claim (a CV is marketing, not testimony): metrics, scope, the user's part vs the team's. Drills into tool ecosystems ("Python" → pytest, ruff, Django, Celery… — exactly the keywords ATS filters match). Inspects portfolio assets (GitHub, website, published work) directly — budgeted, one asset at a time — and records a show/fix/don't-link verdict per asset: what a recruiter sees on click is evidence too, in both directions. Deliberately too extensive for one sitting, and therefore **resumable by design**: progress lives in `knowledge/interview_progress.md`, and every session continues where the last one stopped.
2. **`job-goals`** — targets: titles, seniority, locations, remote policy, salary, hard-yes/hard-no lists. Small and re-runnable.
3. **`job-apply`** — the production line:

```
posting (URL or pasted text)
   │
   ▼
 jd.md ── requirement breakdown + ATS keyword list
   │
   ▼
 FIT GATE ── liveness · constraints screen · evidence-cited score 1–5
   │         · legitimacy tier — verdict said out loud BEFORE anything
   │         is built; weak/fishy → user decides (override recorded)
   ▼
 ATS keyword check ── covered / verifiable gap (mini-interview → KB)
   │                  / real gap — before writing a single line
   ▼
 company research ──▶ notes.md
   │
   ├──────────────────┬─────────────────────┐   parallel sub-agents,
   ▼                  ▼                     │   targeted KB files only
 cv-tailor        cover-letter-writer       │
 cv.md + trace    cover.md + trace          │
   └──────────────────┴─────────────────────┘
   ▼
 application-verifier ──▶ findings ──▶ fix ──▶ re-verify ─┐
   ▲                     (same agents continued, not      │
   └──────────────────────respawned)◀─────────────────────┘
   │ CLEAN
   ▼
 present + tracker.csv row (fit score recorded)
```

## After you apply — the lifecycle

```
                ┌─ rejection ──▶ postmortem ──────────────┐
 tracker.csv ───┼─ interview ──▶ interview-briefer ▶ prep.md ─┼──▶ one lesson line
                └─ offer ─────▶ clause walk + negotiation ┘         │
                                                                    ▼
     next application's fit gate ◀── reads ◀── knowledge/lessons.md
                (analytics reads the whole tracker for patterns)
```

- **Interview booked** → `lifecycle/interview_prep.md`: a capped research refresh, then the **interview-briefer** agent builds a stage-specific `prep.md` with fresh eyes — prepped against what was *actually claimed* to that company (overrides included), with rusty-risk topics and gaps flagged honestly.
- **Offer arrives** → `lifecycle/offer.md`, two parts in strict order. First the **contract-reading companion**: describe-don't-judge — a clause-by-clause walk with neutral tags against the DACH clause taxonomy, promises-vs-paper reconciliation, and two strictly separated question lists (clarifications for the employer; everything legal for a lawyer — the companion never states law or judges enforceability). Then **negotiation prep**: the offer positioned against `goals.md` and the fit gate's own comp research, arguments anchored in KB-traced achievements, replies drafted but never sent. **Contract text never leaves the main session** — no sub-agent, no web query, no artifact. *(The companion adapts ideas from career-ops' offer-prep skill, itself building on Anthropic's claude-for-legal — credit to both.)*
- **Rejection** → `lifecycle/postmortem.md`: classify where it died (machine / human screen / post-interview), work the cause checklist against the actual submitted documents, state one plain diagnosis with one concrete fix.
- **Across applications** → `lifecycle/analytics.md` reads the whole tracker by recipe — funnel, where applications die, pace — and turns a rejection *pattern* into one strategy adjustment instead of another per-application fix. Fit scores land in the tracker, so analytics can also tell whether the gate's own scoring is calibrated.
- **The loop closes** through `knowledge/lessons.md`: every post-mortem and interview debrief lands exactly one lesson line, and the fit gate reads them back before the next application is built — a diagnosis made once is never made from scratch again.

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

## The scripts layer (`scripts/`)

The pipeline's mechanical, no-judgment steps run through small, dependency-free Python helpers (standard library only) instead of burning tokens on an LLM call. Each returns a short report; the orchestrator applies the judgment, and every step falls back to being done by hand if a script is absent.

| Script                | Replaces                                                                                     |
| :-------------------- | :------------------------------------------------------------------------------------------- |
| `ats_coverage.py`     | The inline ATS keyword sweep — literal whole-token matching of `jd.md` keywords vs the KB, bucketed COVERED / UNVERIFIED / GAP |
| `trace_check.py`      | The verifier's trace bookkeeping — confirms every trace target resolves to a real file + `#anchor` before `application-verifier` runs |
| `claim_ledger.py`     | Re-judging unchanged claims — memoizes (claim, source, content hash) on CLEAN verdicts; exact repeats come back PRE-VERIFIED, so the verifier judges only new/changed claims |
| `tracker.py`          | Hand-editing `tracker.csv` — column order, quoting, and header migration, with defect warnings |
| `session_metrics.py`  | Manual transcript reading — the `TOKEN_ECONOMY.md` §2 measurement proxies + real token totals |

Tests: `python3 -m unittest discover -s scripts/tests`.

## European / DACH specifics

Language follows the posting (German posting → Lebenslauf + Anschreiben); protected titles ("Ingenieur") are hard rules the verifier blocks on; the logistics close always carries permit status and notice period; photo/birth-date are the user's recorded choice, asked once at intake; Austrian KV-minimum and Swiss permit/salary conventions covered; a contract clause taxonomy (Probezeit, Kündigungsfrist, 13th salary, non-compete with compensation, …) equips the offer stage's clause walk — as market patterns, never legal statements. Details: [`job_docs/standards/dach_conventions.md`](./job_docs/standards/dach_conventions.md).

## Output format

**Markdown is the deliverable.** Rendering (PDF via the `pdf` skill or pandoc, docx, or a transfer block for an external designed-CV builder) happens only on request — options and ATS caveats in [`job_docs/standards/rendering.md`](./job_docs/standards/rendering.md).

## Install

```
/plugin marketplace add amiran-levanovich/dossier
/plugin install dossier@dossier
```

Then, in your job folder: run `job-intake` and block out a coffee's worth of time — the interview is the investment everything else pays back.

## What it deliberately does **not** have

- **No pre-commit hook, no fixer agents** (same stance as `atelier`) — application quality is a judgment; enforcement is the verifier gate and the traceability contract.
- **No personal data in the plugin.** The knowledge base, tracker, and applications live in your own job folder; the plugin ships only method, standards, and templates.

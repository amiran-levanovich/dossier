# dossier

> Sibling plugins, same method, separate repos: [**redgreen**](https://github.com/amiran-levanovich/redgreen) (code) · [**atelier**](https://github.com/amiran-levanovich/atelier) (design, content, research). Formerly `job-workflow` in the `claude_setup` marketplace.

A Claude Code plugin that runs a **job search** with the same discipline its siblings bring to code and craft: interview the candidate once into a story bank and one superset CV, verify that CV at full rigor, then produce every application by **trimming** it rather than writing a new one. Two agent dispatches per posting produce an ATS-safe CV and a company-specific cover letter; a verifier gates what is left to judge.

Built for the European market, with first-class **DACH** (Germany/Austria/Switzerland) conventions.

---

## The one idea

A tailored application is only as good as what the system **actually knows** about the candidate — so rigor is paid **once**, on one document, and inherited forever after. An extensive interview produces a story bank; one superset CV is built from it, machine-checked for containment against it, and read and signed off by the candidate. Every application then trims that CV **byte-verbatim**, which is what makes the one-time verdict apply to the artifact actually being sent. Nothing is generated, so there is nothing to re-verify.

## How it works

Three skills, in order — each builds what the next one needs:

```
        (once; resumable)      (small; re-runnable)     (per posting)
        ┌────────────┐         ┌───────────┐         ┌───────────┐
CV ───▶ │ job-intake │ ──────▶ │ job-goals │ ──────▶ │ job-apply │ ◀─── posting
        └─────┬──────┘         └─────┬─────┘         └─────┬─────┘
              ▼                      ▼                     ▼
    story_bank.md +             goals.md         applications/<company>/
      master_cv.md          (search targets)        (CV + letter)
```

1. **`job-intake`** — the big interview. Seeds the *agenda* from the existing CV rather than the bank, because a CV bullet is a hypothesis and one written straight into the bank would be indistinguishable from an interviewed fact later. Then interrogates every claim (a CV is marketing, not testimony): metrics, scope, the candidate's part vs the team's — and keeps pressing until the numbers, the **failures**, and the **motivations** are all recorded, since those two never reach a CV and are what interview prep and a letter's framing are drawn from. Drills into tool ecosystems ("Python" → pytest, ruff, Django, Celery… — exactly the keywords ATS filters match). Inspects portfolio assets (GitHub, website, published work) directly — budgeted, one asset at a time — and records a show/fix/don't-link verdict per asset. Deliberately too extensive for one sitting, and therefore **resumable by design**: progress lives in `interview_progress.md`. Ends, on the candidate's word that it's finished, in the **exemplar build** (below).
2. **`job-goals`** — targets: titles, seniority, locations, remote policy, salary, hard-yes/hard-no lists. Small and re-runnable.
3. **`job-apply`** — the production line:

**Two LLM dispatches per posting.** Everything else is deterministic script:

```
posting (URL or pasted text)
   │
   ▼
 jd.md ── requirement breakdown + ATS keyword list
   │
   ▼
 ATS keyword check ── covered (usable now) / promotable (in the bank,
   │                  your call) / gap (feeds the fit score) — alias-aware.
   │                  Runs first: it costs no LLM call, and it is what the
   ▼                  gate's coverage dimension cites
 FIT GATE ── liveness · constraints screen · evidence-cited score 1–5
   │         · legitimacy tier — verdict said out loud BEFORE anything
   │         is built; weak/fishy → user decides
   ▼
 company research ──▶ notes.md
   │
   ▼
 slot map ── cv.py map: the writer's only view of the exemplar
   │
   ▼
 DISPATCH 1 · application-writer ── plan.json (slot ids, no wording)
   │                              + cover.md — one head picks the lead
   │  evidence, so both documents argue from it; anti-slop pass first
   ▼
 assemble ── cv.py build: kept slots rendered byte-verbatim, proved,
   │  then the posting's spellings swapped in and logged. A faulty plan
   │  writes NOTHING → one repair back to the same writer
   ▼
 DISPATCH 2 · application-verifier ── one round, no cap: the letter's
   │  facts must be in the CV *and* keep its attribution; any one-off
   │  slot judged against the bank.
   │  Everything else inherits the exemplar's verdict
   ▼
 present + tracker.csv row (fit score recorded)
```

## The exemplar — master CV

The writer never generates a CV. At intake's close, once the candidate declares the interview done, the pipeline builds one exemplar in the job folder and verifies it **once, at full rigor** — a containment check against the story bank by a fresh agent, then the candidate's blocking sign-off (`lifecycle/exemplar.md`):

- **`master_cv.md`** — the superset CV: every role, every bullet worth ever using, in canonical spellings. It holds every claim any application may ever make, so trimming never has to reach outside it.

  Per application the writer **only trims** (ADR-0005). `scripts/cv.py map` decomposes the exemplar into addressable **slots**; the writer emits an **edit plan** naming slot ids in output order, and `cv.py build` renders those slots byte-verbatim and proves it with a self-test. There is no mechanism to reword one, which is what makes the once-earned verdict apply to the artifact actually being sent. The only exception is a **one-off slot** the user explicitly directs — the single thing the gate still judges on the CV side.

**The cover letter has no exemplar, on purpose** (removed in v3.0.0). A CV is a superset you subtract from, so verbatim lines stay true across companies. A letter's stable parts are exactly what makes it swappable between companies — the defect `standards/cover_letter_rules.md` exists to prevent — and the anti-slop pass would rewrite reused phrasing anyway.

Slot ids are a hash of the slot's own text, so editing the exemplar renames exactly the slots you touched and nothing else — an edit plan naming a slot that no longer exists fails assembly rather than quietly assembling stale wording. One exemplar only, in the search's primary language, and applying to anything requires its sign-off.

## The anti-slop pass

A letter that reads as machine-written is a defect, so `application-writer` runs a mandatory prose pass over the letter draft **before** writing `cover.md`. It uses the `humanizer` skill when the session has one, and the checklist in `standards/cover_letter_rules.md` when it doesn't: **the pass never skips, only its instrument is optional.** The pass edits prose, never facts — a "humanized" letter that gained a fact the CV doesn't carry is a containment BLOCKER, not a style win. `application-verifier` checks the same anti-slop rules either way: a banned pattern is a MAJOR, a voice note is a MINOR. The CV is out of scope — it is trimmed verbatim, so there is no prose there to polish.

## After you apply — the lifecycle

```
                ┌─ rejection ──▶ postmortem ──────────────┐
 tracker.csv ───┼─ interview ──▶ interview-briefer ▶ prep.md ─┼──▶ one lesson line
                └─ offer ─────▶ clause walk + negotiation ┘         │
                                                                    ▼
     next application's fit gate ◀── reads ◀────── lessons.md
                (analytics reads the whole tracker for patterns)
```

- **Interview booked** → `lifecycle/interview_prep.md`: a capped research refresh, then the **interview-briefer** agent builds a stage-specific `prep.md` with fresh eyes — prepped against what was *actually claimed* to that company (overrides included), with rusty-risk topics and gaps flagged honestly.
- **Offer arrives** → `lifecycle/offer.md`, two parts in strict order. First the **contract-reading companion**: describe-don't-judge — a clause-by-clause walk with neutral tags against the DACH clause taxonomy, promises-vs-paper reconciliation, and two strictly separated question lists (clarifications for the employer; everything legal for a lawyer — the companion never states law or judges enforceability). Then **negotiation prep**: the offer positioned against `goals.md` and the fit gate's own comp research, arguments anchored in achievements the bank records, replies drafted but never sent. **Contract text never leaves the main session** — no sub-agent, no web query, no artifact. *(The companion adapts ideas from career-ops' offer-prep skill, itself building on Anthropic's claude-for-legal — credit to both.)*
- **Rejection** → `lifecycle/postmortem.md`: classify where it died (machine / human screen / post-interview), work the cause checklist against the actual submitted documents, state one plain diagnosis with one concrete fix.
- **Across applications** → `lifecycle/analytics.md` reads the whole tracker by recipe — funnel, where applications die, pace — and turns a rejection *pattern* into one strategy adjustment instead of another per-application fix. Fit scores land in the tracker, so analytics can also tell whether the gate's own scoring is calibrated.
- **The loop closes** through `lessons.md`: every post-mortem and interview debrief lands exactly one lesson line, and the fit gate reads them back before the next application is built — a diagnosis made once is never made from scratch again.

What it builds in *your* job folder (the plugin ships zero personal data):

```
story_bank.md              # your career in prose: context, numbers, failures, motivations,
                           #   portfolio verdicts — wider than any CV, on purpose
master_cv.md               # the exemplar: the subset cleared for documents, built once
master_cv_signoff.md       # what you have read and stood behind, with the exemplar's hash
goals.md                   # search targets
constraints.md             # hard rules and red lines the fit gate screens against
interview_progress.md      # the interview's save-game, and its seeded agenda
lessons.md                 # learning log: every post-mortem lands one lesson, reread before applying
tracker.csv                # one row per application
applications/<company>/    # jd.md · notes.md · plan.json · cv.md · cover.md · alias_log.md · prep.md
```

The bank has **no schema** — no per-role files, no index, no anchors. That machinery existed to serve per-claim trace targets, and with the exemplar verified as a whole there is nothing left for it to serve; what a story is worth is its context, which a schema's job would be to strip.

## Honesty model

- **A CV bullet is a hypothesis.** Claims seeded from your old CV sit on the interview's agenda, not in the bank, until the gauntlet quantifies, scopes and attributes them. Only interrogated material enters the bank.
- **One verification, inherited.** The exemplar is machine-checked for containment against the bank and then **read and signed off by you** — blocking, and never waived for a deadline. Every application trims it byte-verbatim and a self-test proves it, so the signed verdict covers the artifact that actually goes out.
- **The candidate outranks the rule.** If you ask for a claim the exemplar lacks, the workflow warns once (concretely, no moralizing), confirms, gets the details, and it becomes a **one-off slot** — declared, judged at full rigor by the gate, and never disguised as a reworded exemplar line. Agents never volunteer fabrication and never propose a one-off unprompted.

## Skills

| Skill        | When it triggers                                              |
| :----------- | :------------------------------------------------------------ |
| `job-intake` | Building/extending the story bank; resuming the interview; the exemplar build |
| `job-goals`  | Setting or revising search targets                            |
| `job-apply`  | A posting arrives — the full tailoring pipeline               |

## Agents

| Agent                  | Role                                                                     |
| :--------------------- | :----------------------------------------------------------------------- |
| `application-writer`   | The whole package from the slot map and the bank: an edit plan trimming the exemplar + a 6-part, <300-word `cover.md`, both leading with the same evidence |
| `application-verifier` | The gate: traceability, ATS, standards — CLEAN or findings; never edits  |
| `interview-briefer`    | Stage-specific interview `prep.md` — claims-aware, gaps flagged honestly |

## The docs layer (`job_docs/`)

| Doc                                          | What it holds                                                                                                         |
| :------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------- |
| `core/job_workflow.md`                       | The kernel: folder contract, session start/close, routing, quality model                                              |
| `core/interview_protocol.md`                 | The extensive interview: phases, verification gauntlet, ecosystem expansion                                           |
| `core/tailoring_method.md`                   | The per-application pipeline: two dispatches, the deterministic steps between them, the single gate                   |
| `core/fit_check.md`                          | The pre-application gate: liveness, constraints kill-switch, evidence-cited fit score, comp-reliability weighting, legitimacy tier |
| `core/orchestration.md` · `core/quickref.md` | Advised skills + availability check · the 10-rule floor                                                               |
| `standards/`                                 | `cv_rules` · `ats_rules` · `cover_letter_rules` · `dach_conventions` · `rendering`                                    |
| `lifecycle/`                                 | `tracking` (tracker.csv) · `postmortem` (rejections) · `interview_prep` (per-stage) · `analytics` (funnel + patterns) · `offer` (contract read + negotiation prep) · `exemplar` (build it once, sign it off, promote into it) · `migration` (a v3 folder to the two-artifact model) |
| `templates/cv_template.md`                   | The ATS-safe single-column skeleton                                                                                   |

## The scripts layer (`scripts/`)

The pipeline's mechanical, no-judgment steps run through small, dependency-free Python helpers (standard library only) instead of burning tokens on an LLM call. Each returns a short report; the orchestrator applies the judgment, and every step falls back to being done by hand if a script is absent.

| Script                | Replaces                                                                                     |
| :-------------------- | :------------------------------------------------------------------------------------------- |
| `ats_coverage.py`     | The inline ATS keyword sweep — literal whole-token matching of `jd.md` keywords against the exemplar and the story bank, bucketed COVERED (usable now) / PROMOTABLE (in the bank only — a promotion decision) / GAP (in neither — feeds the fit score). Alias-aware, so a posting's "Postgres" matches an exemplar's "PostgreSQL"; and singular/plural-aware on the last word, so its "migrations" matches a bank's "migration" — both directions of a gap the delivered CV doesn't have |
| `cv.py`               | Writing and re-judging a CV — `map` decomposes the exemplar into slots, `build` renders the slots an edit plan kept and refuses anything non-verbatim, writing no file on any fault (ADR-0004, ADR-0005), then runs the alias pass when given `--posting` |
| `aliases.py`          | The manual hunt for the posting's spelling of a technology: merges the shipped `alias_groups.md` with a user extension and swaps in the posting's variant, *after* `cv.py`'s verbatim self-test passes (ADR-0008), logging every swap to `alias_log.md` |
| `tracker.py`          | Hand-editing `tracker.csv` — column order, quoting, and header migration, with defect warnings |
| `session_metrics.py`  | Manual transcript reading — the `TOKEN_ECONOMY.md` §2 measurement proxies, real token totals, and per-dispatch subagent cost (tokens, tool uses, duration) read off the Agent tool result — plus **repairs**, which report through a task notification instead and so leave no dispatch record. Together they made ADR-0003's projected saving measurable |

Tests: `python3 -m unittest discover -s scripts/tests`.

**The regression net.** `eval/fixtures/` holds tiny synthetic job folders; `scripts/eval_run.py` runs the deterministic scripts over each and asserts the output is byte-identical to a blessed snapshot — the slot map, the assembly and its verbatim self-test, the alias swap, the coverage buckets, and the refusal path where a bad plan must write no file at all. `--bless` re-records so an intentional change is one reviewable diff. It also runs under `unittest`, so drift fails without anyone remembering to look. Details: [`eval/fixtures/README.md`](./eval/fixtures/README.md).

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
- **No personal data in the plugin.** The story bank, exemplar, tracker, and applications live in your own job folder; the plugin ships only method, standards, and templates.

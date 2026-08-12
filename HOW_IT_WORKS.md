# How dossier works — the full flow

The companion to [`README.md`](./README.md). The README says *what* the plugin does; this
says *how it actually runs*, end to end, in plain language: what happens in what order, what
each step produces, what gets checked and by whom.

Written for someone who wants to understand the system, not maintain it. For the maintainer's
view see [`CLAUDE.md`](./CLAUDE.md); for exact vocabulary see [`CONTEXT.md`](./CONTEXT.md).

---

## Contents

1. [What this is](#1-what-this-is)
2. [The bet everything rests on](#2-the-bet-everything-rests-on)
3. [The candidate's artifacts](#3-the-candidates-artifacts)
4. [Phase A — the intake interview (once)](#4-phase-a--the-intake-interview-once)
5. [Phase B — goals](#5-phase-b--goals)
6. [Phase C — one application, step by step](#6-phase-c--one-application-step-by-step)
   - [Step 1 — Capture](#step-1--capture)
   - [Step 2 — Keyword coverage](#step-2--keyword-coverage--script-no-ai)
   - [Step 3 — The fit gate](#step-3--the-fit-gate)
   - [Step 4 — Company research](#step-4--company-research)
   - [Step 5 — Dispatch 1: the writer](#step-5--dispatch-1-the-writer--ai-call-1-of-2)
   - [Step 6 — Assembly](#step-6--assembly--script-no-ai)
   - [Step 7 — Dispatch 2: the gate](#step-7--dispatch-2-the-gate--ai-call-2-of-2)
   - [Step 8 — Present and close](#step-8--present-and-close)
7. [Phase D — after you apply](#7-phase-d--after-you-apply)
8. [Who checks what](#8-who-checks-what)
9. [When the gate finds something](#9-when-the-gate-finds-something)
10. [Promotions and one-off slots](#10-promotions-and-one-off-slots)
11. [Checking the plugin itself](#11-checking-the-plugin-itself)
12. [What the live runs have shown](#12-what-the-live-runs-have-shown)
13. [The parts list](#13-the-parts-list)
14. [Where to read next](#14-where-to-read-next)

---

## 1. What this is

A Claude Code plugin that runs a job search. Not an app — a set of instructions in Markdown,
plus small dependency-free Python helpers, that a Claude session reads and follows.

The plugin ships **zero personal data**. Everything about a candidate lives in that person's
own job folder, never in this repo.

It exists to answer one question well: *given this posting, what should this person send, and
can they defend every line of it?*

---

## 2. The bet everything rests on

v3 worked like this: for each application an agent read a schema'd pile of knowledge files,
wrote a CV and a letter from scratch, wrote a sidecar file mapping every claim to a source,
and a verifier adjudicated every claim across up to three rounds. Five AI calls per posting —
and the machinery had to be described in every document in the repo.

v4 bets the other way: **pay full rigor once, then inherit it.**

Interview the candidate thoroughly, once. Build **one superset CV** from that — every bullet
they would ever want on any CV. Verify it, and have the candidate **personally sign off**.
After that, every application is produced by **deleting from it**. Nothing is rewritten.

That is why it is both cheap and trustworthy: an application is trustworthy exactly to the
degree that it is *unchanged* from the document the candidate already read and approved.

**The stated failure condition** (recorded in `CLAUDE.md`): if three or more of the first five
applications are hand-edited before sending, the bet was wrong — and the answer is to revert
to v3, preserved at the `v3.2.1` tag, rather than patch this one.

---

## 3. The candidate's artifacts

```
<job folder>/
├── story_bank.md          the career in ordinary prose
├── master_cv.md           the exemplar: the superset CV
├── master_cv_signoff.md   what was read and stood behind, with the exemplar's hash
├── goals.md               search targets
├── constraints.md         hard rules and red lines
├── lessons.md             one line per rejection or debrief
├── interview_progress.md  the interview's save-game
├── tracker.csv            one row per application
└── applications/<company>/
    ├── jd.md · notes.md · plan.json · cv.md · cover.md · alias_log.md · prep.md
```

**The story bank** holds everything: numbers, failures, motivations, the language trialled for
a quarter and dropped, the migration that locked a table for nine minutes. Wide on purpose.
Much of it will never appear on a CV.

**The exemplar** is the narrower subset cleared for documents.

The relationship is the part people get wrong: **the bank is wider than the exemplar, and that
is correct.** A fact in the bank but not the exemplar is a decision — "not on my CV" — not
drift. No sync obligation, no rebuild trigger (ADR-0006).

**The sign-off** records the exemplar's SHA-256 hash at the moment of approval. Edit the
exemplar afterwards and the hash stops matching, so the sign-off goes stale automatically. No
application can be built on a document the candidate never re-read.

**Search meta** — `goals.md`, `constraints.md`, `lessons.md` — is a third category: what the
candidate *wants* and what the search has *learned*, as opposed to what they have *done*. Only
the fit gate reads it. No document ever draws a claim from it.

---

## 4. Phase A — the intake interview (once)

Skill: `job-intake` · Procedure: `job_docs/core/interview_protocol.md`

**Seed the agenda, not the bank.** The existing CV is read and every bullet lands in
`interview_progress.md` as a *question to work through* — deliberately not in the bank. A CV is
marketing: "Led the platform migration" is a hypothesis until someone asks what the person
actually did. Written into the bank now, it would be indistinguishable from an interviewed fact
later.

**Interview, role by role.** Push for metrics, scope, and the candidate's part versus the
team's. Expand tool ecosystems ("Python" → pytest, Django, Celery — the words an ATS matches).
Inspect portfolio assets directly and record a show / fix / don't-link verdict for each. The
interview is too long for one sitting by design, so progress is written as it goes and it
resumes from wherever it stopped.

**Close-out.** When the candidate declares it finished, the exemplar is built in **one pass**
with the whole bank in view. Not incrementally — a document accreted role by role reads like a
pile rather than a whole.

**The containment check.** A *fresh* agent receives exactly two files — bank and exemplar — and
one question: does every claim in the exemplar appear in the bank, at the same strength?
Freshness matters: the session that just ran the interview remembers what was said out loud,
and a conversation is not an artifact anything later can check.

**The sign-off — blocking.** The candidate reads the exemplar end to end and states they stand
behind every line. No application proceeds without it, deadline or not. This is the
highest-stakes judgment in the system, and it is made calmly, once, outside any deadline — the
opposite of v3, where that judgment happened per posting, under time pressure, inside a
sub-agent the candidate never read.

---

## 5. Phase B — goals

Skill: `job-goals`

A short interview producing `goals.md` (titles, seniority band, locations and remote policy,
salary target **and floor**) and `constraints.md` (protected titles, industries that are a hard
no, facts not to surface). Minutes to run, re-run whenever targets shift.

---

## 6. Phase C — one application, step by step

Skill: `job-apply` · Procedure: `job_docs/core/tailoring_method.md`

**Two AI calls per posting.** Everything between them is deterministic script.

```
posting → jd.md → coverage → FIT GATE → research
                                          ↓
                     slot map → [WRITER] → plan.json + cover.md
                                          ↓
                            assemble (verbatim proof, then aliases)
                                          ↓
                                     [GATE] → present + tracker row
```

### Step 1 — Capture

Fetch the posting, or take pasted text. Produces `applications/<company>/jd.md`: must-haves,
nice-to-haves, and an **ATS keyword list** — every named technology, tool and recurring phrase,
in the posting's own spelling.

### Step 2 — Keyword coverage · *script, no AI*

`scripts/ats_coverage.py` checks that list against **both** artifacts and sorts every keyword
into three buckets:

| Bucket | Meaning | What it means for you |
|---|---|---|
| `COVERED` | the exemplar names it | usable now; trimming can surface it |
| `PROMOTABLE` | the bank has it, the exemplar doesn't | a promotion decision — you *have* this |
| `GAP` | neither has it | feeds the fit score, never the writing |

The three-way split is the whole point. Without it, "I have this but it isn't on my CV" and "I
don't have this" look identical — and the second answer loses applications you would have won.

Matching is literal and whole-token, like a real ATS, with three refinements each learned from
a real posting:

- **alias groups** — a posting's "Postgres" matches an exemplar's "PostgreSQL"
- **singular/plural** — a posting's "migrations" finds a bank that says "migration"
- **one-letter names** — `R` must not match a candidate called "R. Vogel"

It runs **before** the gate: it costs no AI call, and the gate needs its report as evidence.

### Step 3 — The fit gate

Runs `job_docs/core/fit_check.md`. Five minutes of evaluation before forty minutes of
production. Four parts:

1. **Liveness.** Is the posting actually alive? Of the first three real postings this pipeline
   was given, two were dead — one expired outright, one 21 months past its own stated validity
   while an aggregator still listed it as open. A dead posting stops the pipeline.
2. **Constraints screen — binary.** A violated hard constraint is a *kill switch*, not a low
   score. Constraints are never averaged away by a good salary.
3. **A 1–5 score on four dimensions** — coverage, goals alignment, comp, red flags — where
   **every dimension cites its evidence**: a quote from the posting, a bucket from the coverage
   report, a line from `goals.md`. A score without a citation is inflation; missing evidence
   scores a flat 3 marked low-confidence. Comp is weighted by how reliable the number is:
   printed in the posting = full weight, thin third-party data = quarter weight.
4. **Legitimacy tier** — High / Caution / Suspicious, from observable signals only. Report what
   is visible ("posted 90+ days ago, reposted three times, applications go to a free-mail
   address"), never a conclusion ("this is a scam").

The verdict is said out loud **before anything is built**. The candidate's override always wins,
is recorded in `jd.md` and in the tracker row's notes, and is never argued with twice.

### Step 4 — Company research

Usually zero new searches — the gate's own research generally covers it. Produces `notes.md`,
and the letter must reference something real from it.

This step earns its place in surprising ways. On one real posting, research established that the
poster was a **recruitment agency, not the employer** — so there was no product to reference,
and the letter had to be built around the agency's own stated screening practice instead.

### Step 5 — Dispatch 1: the writer · *AI call 1 of 2*

First a script extracts the **slot map**: the exemplar decomposed into addressable pieces, each
id a hash of its own text.

The writer receives the slot map, `jd.md`, `notes.md`, the bank and the standards. **It never
receives `master_cv.md`.** That is the load-bearing choice — rewording is not forbidden, it is
*unavailable*. You cannot reword text you were never given (ADR-0005).

It produces:

- **`plan.json`** — kept slot ids in output order, plus drops. No prose.
- **`cover.md`** — the letter, written fresh for this company.

One agent produces both, so the **lead evidence** — the achievement answering the posting's
hardest requirement — is chosen once and both documents argue from it.

Before writing the letter it runs a mandatory **anti-slop pass** against a catalogue of
machine-writing tells ("stands as a testament to", "cutting-edge", "delve", "not just X but Y").
The pass edits prose, never facts.

### Step 6 — Assembly · *script, no AI*

`scripts/cv.py build` renders the kept slots **byte-verbatim** from the exemplar and **proves
it** with a self-test against the exemplar's own text. A single non-matching line exits
non-zero and writes **no file at all** — a half-assembled CV cannot be sent.

Only after that proof does the **alias pass** run, swapping in the posting's spellings and
logging every swap to `alias_log.md`. The order is enforced in code rather than merely
described: aliasing before the proof would void the guarantee the proof exists to give
(ADR-0008).

### Step 7 — Dispatch 2: the gate · *AI call 2 of 2*

`application-verifier` reads the finished package with fresh eyes, **once**. There is no loop,
because there is nothing to loop over: everything except two things inherits the exemplar's
verdict.

- **The letter's fact containment.** The letter may assert no fact the assembled `cv.md`
  doesn't (ADR-0007). Framing, motivation and company angle are free; numbers, technologies,
  outcomes and credentials are not.
- **Any one-off slot** — content the candidate explicitly directed in that the exemplar lacks.
  Judged at full rigor against the bank.

Four failure classes, each found in a real run and now named in the rules:

| Class | What it looks like |
|---|---|
| **Invented fact** | a number or tool in the letter that appears nowhere |
| **Merged attribution** | "I own a Rails API serving 2M requests/day, including its on-call rotation" — the CV said *built* that API and *owned* a different service's on-call. Every fact contained; the sentence not. |
| **Imported bank fact** | "regularly bled into the working day" — true, in the bank, absent from the CV |
| **Paraphrase drift** | "hold the settlement *domain*" where the CV says "own the settlement *service*". A domain is bigger than a service. |

That last one is caught by a mechanical test, because it got two different verdicts in two runs:
**put the CV's own words back into the letter's sentence — if the meaning narrows, the letter
widened something.** Verb, scope noun, employer and tense must survive that swap; everything
else is the writer's to phrase.

### Step 8 — Present and close

The package is presented with a three-line summary: the lead evidence surfaced, gaps and how
they were handled, the gate's result. A row goes into `tracker.csv` via `scripts/tracker.py`,
carrying the fit score — so analytics can later check whether the gate's own scoring predicts
outcomes, and flag it as inflated if it doesn't.

Markdown is the deliverable. Rendering to PDF happens only if you ask
(`standards/rendering.md`).

---

## 7. Phase D — after you apply

The lifecycle docs take over, each triggered by something that happens rather than by a
schedule:

| Event | Runs | Produces |
|---|---|---|
| Status changes, follow-ups due | `lifecycle/tracking.md` | tracker rows kept current, dated next actions |
| **Rejection** | `lifecycle/postmortem.md` | a diagnosis, one specific fix, **one line in `lessons.md`** |
| **Interview booked** | `lifecycle/interview_prep.md` | `prep.md` — stage-specific briefing, built by a third agent |
| **Offer arrives** | `lifecycle/offer.md` | a clause-by-clause contract read, then negotiation prep |
| "How's the search going?" | `lifecycle/analytics.md` | funnel, where applications die, one strategy adjustment |

Two things worth knowing about this phase:

**Interview prep may use bank facts the exemplar lacks.** The candidate speaks for themselves
in an interview and no parser reads them there, so a story that never earned a CV slot is still
theirs to tell. Documents get no such licence — the widening stops at `prep.md` (ADR-0006).

**The loop closes through `lessons.md`.** Every post-mortem and debrief lands exactly one line,
and the fit gate reads them back before the next application is built. A diagnosis made once is
never made from scratch again — and a lesson logged twice without action is the strongest
evidence there is that the search is re-learning instead of adjusting.

---

## 8. Who checks what

| Actor | Does | Never does |
|---|---|---|
| **Scripts** | string matching, byte comparison, CSV columns, file existence | make a quality judgment |
| **Agents** (2 per application) | is the letter honest, does a one-off hold up | rewrite a verified line |
| **The candidate** | the sign-off; any override of the gate | get bypassed for a deadline |

The maintainer's rule: a script may only replace a step that is deterministic. Anything
requiring judgment stays an AI step.

---

## 9. When the gate finds something

Three outcomes, resolving differently:

- **An invented fact** → the writer removes it. Removal cannot introduce a claim, so nothing
  needs re-verifying.
- **A merged attribution or paraphrase drift** → the writer splits it back apart, each half
  keeping its own slot's attribution. A split *is* new phrasing, so it is constrained rather
  than re-judged: only facts already carried by kept slots may be redistributed, and the main
  session re-reads the result against `cv.md` before presenting. No dispatch, so the
  single-round property survives.
- **A promotion candidate** → the candidate's decision, not a defect.

Nothing is ever presented with an open BLOCKER or MAJOR.

---

## 10. Promotions and one-off slots

Two ways content the exemplar lacks can legitimately reach a document. Both are deliberate,
neither is ever proposed by an agent unprompted.

**Promotion** — moving a fact from the bank into the exemplar as a new slot. One mechanism,
three situations: a posting exposed a gap the bank covers, a one-off worth keeping, or a
migration sweep. The procedure is cheap on purpose: write the slot, re-run the containment
check (only the new slot needs judging), and the candidate signs off on **that slot** — one
line appended to the sign-off file with the new hash. Cheap enough to do mid-application rather
than avoid.

**One-off slot** — content directed into a single application because the exemplar lacked it.
The path when the candidate says "just add Kafka to this one": warn once concretely, confirm,
get the details, then record it as a **new slot** in `plan.json` — never as a reworded existing
slot, because a slot id that no longer matches its text is a lie. It is the one thing on the CV
the inherited verdict does not cover, so the gate judges it at full rigor against the bank.

---

## 11. Checking the plugin itself

Everything above checks *an application*. These check *the repo*, and run before every commit:

```
python3 -m unittest discover -s scripts/tests   the helper scripts' own tests
python3 scripts/eval_run.py                     Tier 1: scripts over synthetic job folders,
                                                diffed against blessed snapshots
python3 scripts/eval_score.py --case <id>       Tier 2: score a recorded agent run
python3 scripts/release_audit.py                doc token budgets + anti-waste rules
python3 scripts/privacy_scan.py --staged        no personal data ever committed
```

**Tier 1** guards the deterministic half: run the scripts over tiny synthetic job folders and
require byte-identical output against blessed snapshots. A deliberate change is one reviewable
diff (`--bless`).

**Tier 2** guards what only an LLM produces, by scoring a recorded run's discrete signals —
never its prose. Two of those signals check a run against *itself* (is every CV line accounted
for; does the run's self-report match the independent count) and hold for any run; the rest are
judged against expectations recorded for one case.

**`release_audit`** enforces the budget table in `TOKEN_ECONOMY.md` §5. Every document loaded on
every run has a token ceiling, because a doc that grows quietly is a tax on every application
forever. It is why adding one rule to the verifier costs four rounds of compression elsewhere in
the same file.

---

## 12. What the live runs have shown

The pipeline had never been run end to end until its first three runs:

| Run | Posting | Gate result | Repair |
|---|---|---|---|
| 1 | synthetic | merged attribution | yes |
| 2 | real, 21 months stale | imported bank fact | yes |
| 3 | real, live | **CLEAN** | none |

Cost per application, read out of the session transcript by `scripts/session_metrics.py`:

- **v3, trace-based:** 192,878 tokens
- **v4:** 80,841 → 98,292 → 114,296, growing with exemplar size — roughly **−58%** on a clean
  run
- **Repairs cost more than the writes they follow** (51,031 and 66,470). That was not in the
  original projection, and it makes the writer's *first-pass* quality the dominant cost term
  rather than the size of its output.

Every rule named in §7 above came from one of those runs finding something real. Full
accounting in `TOKEN_ECONOMY.md` §7c and §7d.

---

## 13. The parts list

**Skills** — thin routers that detect context and point at the authoritative doc:

| Skill | Runs when |
|---|---|
| `job-intake` | building or extending the story bank; the exemplar build |
| `job-goals` | setting or revising targets |
| `job-apply` | a posting arrives |

**Agents** — the only places an LLM makes a judgment:

| Agent | Judges |
|---|---|
| `application-writer` | which slots answer this posting; the letter |
| `application-verifier` | the letter's containment; any one-off slot |
| `interview-briefer` | what to prepare for a booked interview |

**Scripts** — deterministic, dependency-free, tested:

| Script | Replaces |
|---|---|
| `cv.py` | retyping the CV — `map` decomposes, `build` assembles and proves |
| `aliases.py` | hunting for the posting's spelling of a tool |
| `ats_coverage.py` | the inline keyword sweep |
| `tracker.py` | hand-editing a CSV |
| `session_metrics.py` | reading a transcript by hand |
| `machine_summary.py` | re-parsing a report's prose |
| `eval_run.py` / `eval_score.py` | the regression net, both tiers |
| `release_audit.py` / `privacy_scan.py` | release checks |

---

## 14. Where to read next

| Question | File |
|---|---|
| The method, top down | `job_docs/core/job_workflow.md` |
| One application, in detail | `job_docs/core/tailoring_method.md` |
| Whether to apply at all | `job_docs/core/fit_check.md` |
| The interview | `job_docs/core/interview_protocol.md` |
| Building and signing the exemplar | `job_docs/lifecycle/exemplar.md` |
| Coming from a v3 folder | `job_docs/lifecycle/migration.md` |
| Why the shape is the shape | `docs/adr/0004`–`0008` |
| The vocabulary, precisely | `CONTEXT.md` |
| Where the tokens go | `TOKEN_ECONOMY.md` |

---

**In one sentence:** interview once, build one superset CV, have the candidate sign it, then
produce every application by deleting from that CV and proving nothing changed — so the only
things left to judge per posting are the letter's honesty and anything deliberately added.

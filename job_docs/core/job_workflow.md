# The Job Workflow — one interview, many applications

This runbook is the **kernel** for running a job search with Claude Code. It is the sibling of `redgreen`'s `coding_workflow.md` and `atelier`'s `craft_workflow.md`: the same discipline — understand deeply before producing, define the bar before writing, gate the output — applied to applications instead of code.

> **The one idea everything hangs on:** the quality bar is earned **once**, not per application. An extensive intake interview builds a **story bank**, the bank builds one superset CV — the **exemplar** — and that exemplar is verified whole and signed off by the candidate. Every application after it is a *trim* of that signed artifact, byte-verbatim, so the signed verdict still covers what goes out. Tailoring by rewriting is guessing; the pipeline refuses to guess.

> **Context tight or lost?** `core/quickref.md` is the distilled 10-rule floor with a "when lost" protocol — re-read it instead of guessing.

<!-- audit-ok: C2 C3 C4 — kernel overview: it names the research step, the single gate and the daily tracker read conceptually; the search budgets live in core/fit_check.md + core/tailoring_method.md, the "continue, don't respawn" rule in core/tailoring_method.md + core/quickref.md, and the batch/read discipline in agents/application-verifier.md. Duplicating them here would bloat the kernel and split the source of truth. -->


---

## THE FOLDER CONTRACT

The plugin ships **zero personal data**. Everything about the candidate lives in the user's own job folder, created and maintained by the skills:

```
<job folder>/
├── story_bank.md              # the career record in prose — core/interview_protocol.md
├── master_cv.md               # the exemplar: built once from the bank — lifecycle/exemplar.md
├── master_cv_signoff.md       # the candidate's sign-off, with the exemplar's hash
├── interview_progress.md      # the intake interview's save-game and its seeded agenda
├── goals.md                   # search targets — job-goals
├── constraints.md             # hard rules and red lines the fit gate screens against
├── lessons.md                 # learning log, one line per post-mortem or debrief
├── applications/<company>/    # one folder per application:
│   ├── jd.md                  #   requirement breakdown + fit verdict (core/fit_check.md)
│   ├── notes.md               #   company research, and anything else worth keeping
│   ├── plan.json              #   the writer's edit plan: kept slot ids + any one-off slot
│   ├── cv.md + cover.md       #   the application package
│   ├── alias_log.md           #   every alias-group spelling swapped in at assembly
│   ├── prep.md                #   interview prep, once an interview is booked
│   ├── offer_notes.md         #   recorded promises, once an offer arrives (lifecycle/offer.md)
│   └── offer_prep.md          #   contract clause walk + negotiation prep (lifecycle/offer.md)
├── tracker.csv                # application status log — see lifecycle/tracking.md
└── CLAUDE.md                  # written after intake: a short pointer to the two artifacts and this workflow
```

`goals.md`, `constraints.md` and `lessons.md` are the **search meta**: what the candidate wants and what the search has learned. They sit outside both candidate artifacts because they are a different category from what the candidate has *done*, and no document ever draws a claim from them.

---

## SESSION START — run at the beginning of every session in the job folder

Gather context silently before responding; never ask for what a file can answer. Everything below lives **in the current working directory** — that folder *is* the job folder, whatever its state.

1. **One `ls` of the folder decides the state.** If `story_bank.md` is absent but `knowledge/` is present, this is a v3 folder — offer `lifecycle/migration.md` and stop the checklist here. If both are absent, the folder is fresh: there is nothing to gather — do **not** search parent directories, the home directory, or anywhere else for a bank, an exemplar, a tracker, or personal files. Skip the rest of this checklist and route per the table below (a fresh folder means `job-intake`).
2. Read `goals.md` and `constraints.md` in full — they are small and always relevant — and `master_cv_signoff.md` to know whether the exemplar is signed and current. The bank and the exemplar are **not** read at session start; they are large, and each pipeline reads what it needs.
3. Read `tracker.csv` — know every application's status and which `next_action` dates are due or overdue. In full while it's small; once it passes ~50 rows, read the header plus the non-terminal rows and this month's closures (Grep/filter), not the whole history — `lifecycle/analytics.md` has the recipe for whole-tracker questions. (Any of these files missing in a non-fresh folder: note it as a gap to fix, don't go looking for it elsewhere.)
4. Cross-check `applications/` subfolders against the tracker. A folder with application documents but a stale tracker row (or vice versa) is drift — fix it or flag it immediately.
5. **Brief conditionally.** If the user's opening is generic ("hi", "let's do some job stuff"): give a 5–8 line status summary — active applications, next actions due, anything needing attention — then ask what to work on. If they opened with a specific task, just do the task.

---

## ROUTING — which skill runs

| State / request                                                                                     | Route                                              |
| :-------------------------------------------------------------------------------------------------- | :------------------------------------------------- |
| A `knowledge/` directory and no `story_bank.md` — a v3 folder                                       | `lifecycle/migration.md`                           |
| No `story_bank.md` yet, the interview is unfinished (`interview_progress.md` has open areas), or the exemplar is unbuilt or unsigned | `job-intake`                                       |
| Bank and exemplar exist but `goals.md` is missing or stale; or the user wants to change targets      | `job-goals`                                        |
| The user brings a job posting (URL or pasted text)                                                  | `job-apply`                                        |
| A rejection came in                                                                                 | update tracker, then `lifecycle/postmortem.md`     |
| An interview got booked                                                                             | update tracker, then `lifecycle/interview_prep.md` |
| An offer arrived                                                                                    | update tracker, then `lifecycle/offer.md`          |
| Status changes, follow-ups, "where do things stand?"                                                 | `lifecycle/tracking.md`                            |
| "How's the search going?", patterns, a strategy review                                              | `lifecycle/analytics.md`                           |

**Order is not optional:** `job-apply` requires a **signed-off** `master_cv.md` and current goals. A sign-off whose recorded hash no longer matches the exemplar counts as unsigned — the artifact was edited after it was read. If either is missing, say so and route to the missing step first; a deadline never justifies applying without the sign-off.

---

## THE QUALITY MODEL — how enforcement works here

There is no commit hook and no fixer agent. The bar is held by three mechanisms, all defined in `core/tailoring_method.md` and `lifecycle/exemplar.md`:

1. **One verification, inherited.** The exemplar is machine-checked for containment against the bank, then read and signed off by the candidate. Every application CV is trimmed from it byte-verbatim and a self-test proves it, so the signed verdict covers the artifact that actually goes out. The exemplar holds every claim any application may ever make — trimming only removes, so a claim the exemplar lacks cannot reach a CV.
2. **The gate, once.** `application-verifier` reads the finished package with fresh eyes and judges the two things the inherited verdict does not cover: the letter's **fact containment** against the assembled CV, and any **one-off slot**. One round, no loop — an invented fact is removed (which cannot introduce a claim), and a promotion candidate is the user's decision, not a defect. Nothing ships with an open BLOCKER or MAJOR.
3. **Only interrogated material.** A CV bullet is a hypothesis: claims seeded from an old CV sit on the interview's agenda, not in the bank, until the gauntlet quantifies, scopes and attributes them.

**Two LLM dispatches per application** — one writer, one verifier. Everything between them is deterministic script (`scripts/`), because coverage counting, verbatim proving and CSV bookkeeping are mechanical and an LLM call for them is pure waste.

---

## STANDING RULES

- **Markdown is the deliverable.** CVs and letters are produced as `.md`. Render to PDF or other formats only when the user asks — options and market caveats are in `standards/rendering.md`.
- **Language follows the posting.** The story bank and the exemplar are written in English; generated documents match the posting's language unless the user says otherwise. DACH-market specifics live in `standards/dach_conventions.md`.
- **Research before writing.** Every new company gets a quick WebSearch (what they do, size, recent news, tone) before any material is written — letters that reference something real outperform generic ones.
- **Never volunteer fabrication.** Agents write only what their inputs support, and the writer never proposes a one-off of its own. The user may explicitly direct a claim the exemplar lacks — warn once, confirm, get the details, and it becomes a **one-off slot**: declared as such, judged at full rigor by the gate, never disguised as a reworded exemplar line. It is the *user's* call, not yours.
- **Don't chase mismatches.** Every posting passes the fit gate (`core/fit_check.md`) before anything is built: liveness, a binary constraints screen, an evidence-cited 1–5 score, a legitimacy tier. A weak verdict gets said out loud — applying anyway is the user's call, recorded and never argued with twice.
- **Verify the checkable, don't assume it.** Before acting on a claimed state that a file or a fetch can confirm — a posting still live, a tracker row's status, a sign-off still current — check it, even when the claim comes from the user's memory or your own earlier in the session. The user's word is final on their own life (a call happened, a reply arrived); files and URLs speak for themselves.

---

## SESSION CLOSE — run before ending any session in the job folder

1. **Tracker current?** Every company touched this session has the right status, dates, link, and a concrete dated `next_action`.
2. **Application folders complete?** Every application worked on has its `jd.md`, `notes.md`, `plan.json`, `cv.md` and `cover.md` in place.
3. **Bank current?** New facts learned this session (a metric recalled mid-conversation, a new story) are written into `story_bank.md` — including a `lessons.md` line if a post-mortem or interview debrief ran; if the intake interview is still open, `interview_progress.md` reflects exactly where it stopped. A bank fact worth putting on a CV is a separate, deliberate **promotion** (`lifecycle/exemplar.md`), never automatic.
4. End with one line: what was updated, what's next. Keep it brief.

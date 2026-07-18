# The Job Workflow — knowledge-first job applications

This runbook is the **kernel** for running a job search with Claude Code. It is the sibling of `redgreen`'s `coding_workflow.md` and `atelier`'s `craft_workflow.md`: the same discipline — understand deeply before producing, define the bar before writing, gate the output — applied to applications instead of code.

> **The one idea everything hangs on:** a tailored application is only as good as what the system *actually knows* about the candidate. So the workflow front-loads an extensive, verified knowledge base, and every generated document must **trace each claim back to it**. Tailoring without the knowledge base is guessing; the pipeline refuses to guess.

> **Context tight or lost?** `core/quickref.md` is the distilled 10-rule floor with a "when lost" protocol — re-read it instead of guessing.

---

## THE FOLDER CONTRACT

The plugin ships **zero personal data**. Everything about the candidate lives in the user's own job folder, created and maintained by the skills:

```
<job folder>/
├── knowledge/                 # the knowledge base — see core/kb_schema.md
├── applications/<company>/    # one folder per application:
│   ├── jd.md                  #   requirement breakdown + fit verdict (core/fit_check.md)
│   ├── cv.md + cv_trace.md    #   tailored CV + claim→source map
│   ├── cover.md + cover_trace.md
│   ├── overrides.md           #   user-directed claims, if any (core/override_protocol.md)
│   ├── prep.md                #   interview prep, once an interview is booked
│   ├── offer_notes.md         #   recorded promises, once an offer arrives (lifecycle/offer.md)
│   ├── offer_prep.md          #   contract clause walk + negotiation prep (lifecycle/offer.md)
│   └── notes.md               #   anything else worth keeping per company
├── master_cv.md (+ trace)     # optional exemplars, built once — lifecycle/master_documents.md
├── cover_frame.md (+ trace)   #   (with .claim_ledger.json, the verifier's memo of past CLEANs)
├── tracker.csv                # application status log — see lifecycle/tracking.md
└── CLAUDE.md                  # written after intake: a short pointer to knowledge/ and this workflow
```

---

## SESSION START — run at the beginning of every session in the job folder

Gather context silently before responding; never ask for what a file can answer. Everything below lives **in the current working directory** — that folder *is* the job folder, whatever its state.

1. **One `ls` of the folder decides the state.** If `knowledge/` is absent, the folder is fresh: there is nothing to gather — do **not** search parent directories, the home directory, or anywhere else for a knowledge base, tracker, or personal files. Skip the rest of this checklist and route per the table below (a fresh folder means `job-intake`).
2. Read `knowledge/INDEX.md` — know what the knowledge base covers. Read `knowledge/goals.md` and `knowledge/constraints.md` in full; they are small and always relevant.
3. Read `tracker.csv` — know every application's status and which `next_action` dates are due or overdue. In full while it's small; once it passes ~50 rows, read the header plus the non-terminal rows and this month's closures (Grep/filter), not the whole history — `lifecycle/analytics.md` has the recipe for whole-tracker questions. (Any of these files missing in a non-fresh folder: note it as a gap to fix, don't go looking for it elsewhere.)
4. Cross-check `applications/` subfolders against the tracker. A folder with application documents but a stale tracker row (or vice versa) is drift — fix it or flag it immediately.
5. **Brief conditionally.** If the user's opening is generic ("hi", "let's do some job stuff"): give a 5–8 line status summary — active applications, next actions due, anything needing attention — then ask what to work on. If they opened with a specific task, just do the task.

---

## ROUTING — which skill runs

| State / request                                                                                        | Route                                              |
| :----------------------------------------------------------------------------------------------------- | :------------------------------------------------- |
| No `knowledge/` yet, or the interview is unfinished (`knowledge/interview_progress.md` has open areas) | `job-intake`                                       |
| Knowledge base exists but `goals.md` is missing or stale; or the user wants to change targets          | `job-goals`                                        |
| The user brings a job posting (URL or pasted text)                                                     | `job-apply`                                        |
| A rejection came in                                                                                    | update tracker, then `lifecycle/postmortem.md`     |
| An interview got booked                                                                                | update tracker, then `lifecycle/interview_prep.md` |
| An offer arrived                                                                                       | update tracker, then `lifecycle/offer.md`          |
| Status changes, follow-ups, "where do things stand?"                                                   | `lifecycle/tracking.md`                            |
| "How's the search going?", patterns, a strategy review                                                 | `lifecycle/analytics.md`                           |

**Order is not optional:** `job-apply` requires a knowledge base with verified content and a signed-off `goals.md`. If either is missing, say so and route to the missing step first — a tailored CV built on an empty or unverified knowledge base is the exact failure this workflow exists to prevent.

---

## THE QUALITY MODEL — how enforcement works here

There is no commit hook and nothing deterministic to check. The bar is held by three mechanisms, all defined in `core/tailoring_method.md`:

1. **Traceability.** Every claim in a generated CV or cover letter maps to a knowledge-base entry (or an explicit user-directed override) via a trace file. Untraceable claims are defects.
2. **The verifier gate.** The `application-verifier` agent reviews every application package with fresh eyes — traceability, ATS compliance, standards — and the fix→re-verify loop runs until it returns CLEAN. Nothing ships on a round with open findings.
3. **Verified knowledge only.** Knowledge-base entries seeded from a CV start as `unverified` claims; only interview-confirmed entries feed tailoring (see `core/kb_schema.md`).

---

## STANDING RULES

- **Markdown is the deliverable.** CVs and letters are produced as `.md`. Render to PDF or other formats only when the user asks — options and market caveats are in `standards/rendering.md`.
- **Language follows the posting.** The knowledge base is written in English; generated documents match the posting's language unless the user says otherwise. DACH-market specifics live in `standards/dach_conventions.md`.
- **Research before writing.** Every new company gets a quick WebSearch (what they do, size, recent news, tone) before any material is written — letters that reference something real outperform generic ones.
- **Never volunteer fabrication.** Agents write only what the knowledge base supports. The user may explicitly direct an unsupported claim — that path has a protocol (warn once, confirm, detail, record in `overrides.md`) and it is the *user's* call, not yours. See `core/tailoring_method.md`.
- **Don't chase mismatches.** Every posting passes the fit gate (`core/fit_check.md`) before anything is built: liveness, a binary constraints screen, an evidence-cited 1–5 score, a legitimacy tier. A weak verdict gets said out loud — applying anyway is the user's call, and the override is recorded, never argued with twice.
- **Verify the checkable, don't assume it.** Before acting on a claimed state that a file or a fetch can confirm — a posting still live, a tracker row's status, an application package complete — check it, even when the claim comes from the user's memory or your own earlier in the session. The user's word is final on their own life (a call happened, a reply arrived); files and URLs speak for themselves.

---

## SESSION CLOSE — run before ending any session in the job folder

1. **Tracker current?** Every company touched this session has the right status, dates, link, and a concrete dated `next_action`.
2. **Application folders complete?** Every application worked on has its `jd.md`, `cv.md`, `cover.md` (+ trace files) in place.
3. **Knowledge base current?** New facts learned this session (a metric recalled mid-conversation, a new story) are written into `knowledge/` and `INDEX.md` — including a `lessons.md` line if a post-mortem or interview debrief ran; if the intake interview is still open, `interview_progress.md` reflects exactly where it stopped.
4. End with one line: what was updated, what's next. Keep it brief.

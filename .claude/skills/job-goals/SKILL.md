---
name: job-goals
description: Use to SET or REVISE job-search targets once the story bank and exemplar exist — target titles and seniority, locations and remote policy, salary target and floor, hard-yes and hard-no lists. Triggers on 'set my job goals', 'what should I target', 'change my targets', 'update my search criteria', 'new salary target'. NOT for building the story bank (job-intake) or applying to a posting (job-apply).
---

Read `job_docs/core/fit_check.md` — it is what consumes `goals.md` and `constraints.md`, so it defines what these files must answer. Locate it as follows: use `job_docs/core/fit_check.md` in the project root if present (drop-in install); otherwise read `../../../job_docs/core/fit_check.md` relative to this skill's directory (plugin install). Those two locations are the only ones: if neither resolves, report the broken install and stop — never search the filesystem for `job_docs`.

This skill is deliberately small and re-runnable — targets shift during a search; the story bank and the exemplar don't.

1. **Precondition**: `story_bank.md` **in the current working directory** — one existence check, not a search. If missing, route to `job-intake` first (never hunt for a bank elsewhere on the filesystem) — goals set against an empty bank are guesses.
2. **Interview** with AskUserQuestion (options-first, at most two questions per call), grounded in what the bank and `master_cv.md` show: target titles and seniority band (sanity-check against the recorded experience — flag a reach or an undersell), locations + remote policy + relocation, salary target **and floor**, industries/company types/setups that are hard-yes or hard-no.
3. **Write** the two search-meta files at the job-folder root, both plain and short — the fit gate reads them whole on every application:
   - `goals.md` — target titles, seniority band, locations and remote policy, salary target and floor. Date the top of the file.
   - `constraints.md` — the hard rules and red lines: title wording (a protected-title situation), industries or company types that are a hard no, facts the candidate does not want surfaced. A constraint is a kill-switch at the gate, so write each one so a violation is unambiguous.
4. **Read back** the result in ~6 lines and get an explicit nod — `job-apply` treats these files as authoritative filters, so they must actually be the user's answer, not your summary of it.

On a revision run, read the existing files first and change only what the user wants changed; date the revision at the top of `goals.md`.

If context is tight, read `job_docs/core/quickref.md` (same path resolution).

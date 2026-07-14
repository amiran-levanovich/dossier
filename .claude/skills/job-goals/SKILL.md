---
name: job-goals
description: Use to SET or REVISE job-search targets once the knowledge base exists — target titles and seniority, locations and remote policy, salary target, hard-yes and hard-no lists. Triggers on 'set my job goals', 'what should I target', 'change my targets', 'update my search criteria', 'new salary target'. NOT for building the knowledge base (job-intake) or applying to a posting (job-apply).
---

Read `job_docs/core/kb_schema.md` for the `goals.md` / `constraints.md` contracts. Locate it as follows: use `job_docs/core/kb_schema.md` in the project root if present (drop-in install); otherwise read `../../../job_docs/core/kb_schema.md` relative to this skill's directory (plugin install). Those two locations are the only ones: if neither resolves, report the broken install and stop — never search the filesystem for `job_docs`.

This skill is deliberately small and re-runnable — targets shift during a search; the knowledge base doesn't.

1. **Precondition**: a knowledge base **in the current working directory** with at least `profile.md` and one verified role — one existence check, not a search. If missing, route to `job-intake` first (never hunt for a knowledge base elsewhere on the filesystem) — goals set against an empty profile are guesses.
2. **Interview** with AskUserQuestion (options-first, at most two questions per call), grounded in what the KB shows: target titles and seniority band (sanity-check against the verified experience — flag a reach or an undersell), locations + remote policy + relocation, salary target and floor (the floor goes to `profile.md`, the target to `goals.md`), industries/company types/setups that are hard-yes or hard-no.
3. **Write** `knowledge/goals.md` and fold the hard rules into `knowledge/constraints.md`; update both `INDEX.md` lines in the same step.
4. **Read back** the result in ~6 lines and get an explicit nod — `job-apply` treats these files as authoritative filters, so they must actually be the user's answer, not your summary of it.

On a revision run, read the existing files first and change only what the user wants changed; date the revision at the top of `goals.md`.

If context is tight, read `job_docs/core/quickref.md` (same path resolution).

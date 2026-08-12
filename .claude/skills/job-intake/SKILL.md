---
name: job-intake
description: Use to BUILD or EXTEND the candidate's story bank at the start of a job search — an extensive, resumable interview that turns a CV and the candidate's memory into a career record in prose, ending in a signed-off superset CV (master_cv.md). Triggers on 'set up my job search', 'build my profile', 'intake interview', 'continue the interview', 'add to my story bank', or when job-apply finds no exemplar. NOT for tailoring an application (job-apply) or setting search targets (job-goals).
---

Read `job_docs/core/interview_protocol.md` and follow it. Locate it as follows: the project-root copy if present (drop-in install); otherwise `../../../job_docs/core/interview_protocol.md` relative to this skill's directory (plugin install). The docs it references resolve the same way. Those two locations are the only ones: if neither resolves, report the broken install and stop — never search the filesystem for `job_docs`.

This skill runs the front of the kernel (`job_docs/core/job_workflow.md`):

1. **Resume check first**: if `interview_progress.md` exists **in the current working directory** (one existence check — never search elsewhere for it), read it and continue from the first non-done area, never re-asking recorded material. Otherwise this is a first run; a fresh or empty folder is the normal starting state, not something to investigate.
2. **Availability check** (first run only): read `job_docs/core/orchestration.md` and report the compact advised-skills table. Informational, never blocks.
3. **Seed the agenda** (Phase 1): ingest the existing CV into `interview_progress.md` as the list of claims to work through — **not** into the story bank. A CV bullet is a hypothesis; written into the bank now it would be indistinguishable from an interviewed fact later.
4. **Interview** (Phases 2–4): role deep-dives with the gauntlet (quantify, scope, attribute, correct) and ecosystem keyword expansion, pressing until the numbers, the failures and the motivations are all recorded; then portfolio verdicts, skills, education, admin facts, constraints, story harvest. Write prose into `story_bank.md` and update `interview_progress.md` **as you go** — the interview must survive the session dying at any point.
5. **Close out** (Phase 5): every area done, every seeded claim interrogated or struck. Then ask the candidate to declare the interview finished — that declaration is what unlocks the **exemplar build** (`job_docs/lifecycle/exemplar.md`): one terminal pass over the whole bank, a containment check by a fresh agent, then the candidate's **blocking** sign-off. No application may proceed without it, deadline or not. Then hand off to `job-goals`.

The bank has no schema — prose with headings for the candidate's own navigation, nothing depending on them. It stays **wider** than the exemplar on purpose: interview material, failures and motivations belong in it and never on a CV. Adding to it later triggers no rebuild; putting a fact on the CV is a separate, deliberate promotion (`job_docs/lifecycle/exemplar.md`).

Offer a natural break at every area boundary — the interview is extensive by design and resumability is the feature, not an apology.

If context is tight (post-compaction, near the limit, or unsure of the rules), read `job_docs/core/quickref.md` (same path resolution) — the distilled floor and the "when lost" protocol.

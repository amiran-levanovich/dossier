---
name: job-intake
description: Use to BUILD or EXTEND the candidate knowledge base at the start of a job search — an extensive, resumable interview that turns a CV and the user's memory into verified, tailoring-ready knowledge. Triggers on 'set up my job search', 'build my profile', 'intake interview', 'continue the interview', 'update my knowledge base', or when job-apply finds no knowledge base. NOT for tailoring an application (job-apply) or setting search targets (job-goals).
---

Read `job_docs/core/interview_protocol.md` and follow it. Locate it as follows: use `job_docs/core/interview_protocol.md` in the project root if present (drop-in install); otherwise read `../../../job_docs/core/interview_protocol.md` relative to this skill's directory (plugin install). Read `job_docs/core/kb_schema.md` (same resolution) alongside it — it defines everything this skill writes.

This skill runs the front of the kernel (`job_docs/core/job_workflow.md`):

1. **Resume check first**: if `knowledge/interview_progress.md` exists, read it and continue from the first non-done area — never re-ask recorded material. Otherwise this is a first run:
2. **Availability check** (first run only): read `job_docs/core/orchestration.md` and report the compact advised-skills table. Informational, never blocks.
3. **Seed** (Phase 1): ingest the existing CV/materials into the KB layout, every entry marked `[unverified]` — a CV is claims, not facts.
4. **Interview** (Phases 2–4): role deep-dives with the verification gauntlet (quantify, scope, attribute, correct) and ecosystem keyword expansion; then skills, education, admin facts, constraints, story harvest. Update the KB files, `INDEX.md`, and `interview_progress.md` **as you go** — the interview must survive the session dying at any point.
5. **Close out** (Phase 5): no surviving `[unverified]` markers or open areas, regenerate INDEX hooks, write the job folder's `CLAUDE.md` stub, then hand off to `job-goals`.

Offer a natural break at every area boundary — the interview is extensive by design and resumability is the feature, not an apology.

If context is tight (post-compaction, near the limit, or unsure of the rules), read `job_docs/core/quickref.md` (same path resolution) — the distilled floor and the "when lost" protocol.

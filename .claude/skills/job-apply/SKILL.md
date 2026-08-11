---
name: job-apply
description: Use to APPLY to a specific job posting once the exemplar and goals exist — turns a posting URL or pasted text into an application package (a CV trimmed verbatim from the signed-off master_cv.md + a company-specific cover letter). Triggers on 'apply to this', 'here's a posting', 'tailor my CV for this job', 'write a cover letter for this role', or a pasted job description/link. NOT for building the story bank and exemplar (job-intake) or setting targets (job-goals).
---

Read `job_docs/core/tailoring_method.md` and follow it end to end. Locate it as follows: the project-root copy if present (drop-in install); otherwise `../../../job_docs/core/tailoring_method.md` relative to this skill's directory (plugin install). The standards it references (`job_docs/standards/…`) resolve the same way; pass **resolved absolute paths** to the agents — they don't inherit this skill's location. If neither resolves, report the broken install and stop — never search the filesystem for `job_docs`.

The pipeline this skill orchestrates — **two LLM dispatches, everything else deterministic**:

1. **Preconditions**: a signed-off `master_cv.md`, a `story_bank.md`, and a current `goals.md` **in the current working directory** — one existence check, not a search. Missing or unsigned: stop and route to `job-intake` / `job-goals`. A deadline never justifies skipping the sign-off.
2. **Capture** the posting (WebFetch or pasted text) → `applications/<company>/jd.md`.
3. **The fit gate** (per `job_docs/core/fit_check.md`, same path resolution): liveness, constraints screen, evidence-cited score with its band, legitimacy tier — the verdict gets said **before anything is built**. 2 WebSearch queries by default, 5 max when genuinely uncertain; a user override wins and is recorded.
4. **ATS keyword check** via `scripts/ats_coverage.py` **before writing anything**: COVERED is usable now, PROMOTABLE is the user's promotion decision, GAP feeds the fit score.
5. **Company research** → `notes.md` — reuse the fit gate's findings first; WebSearch only for what's still missing.
6. **Dispatch 1 — the writer.** Extract the slot map (`scripts/cv.py map`) and launch `application-writer` with it *instead of* the exemplar. It emits `plan.json` + `cover.md`, picking the lead evidence once so both argue from it. It may not reword a slot and never proposes a one-off unprompted.
7. **Assemble** (no dispatch): `scripts/cv.py build plan.json --exemplar master_cv.md --posting jd.md` renders kept slots byte-verbatim, proves it, then swaps in the posting's spellings. A faulty plan writes **nothing** — hand the diagnostic back to the *same* writer for one re-dispatch.
8. **Dispatch 2 — the gate.** `application-verifier`, **one round, no cap**: the letter's fact containment against the CV, plus any one-off slot. Everything else inherits the exemplar's verdict. An invented fact is removed by the writer — removal introduces nothing, so no re-verify; a claim the bank supports but the exemplar lacks is the user's promotion decision. Never present with open BLOCKER/MAJOR findings.
9. **Close**: present with the 3-line summary, update `tracker.csv` via `scripts/tracker.py` (per `job_docs/lifecycle/tracking.md`), offer rendering only on request (`job_docs/standards/rendering.md`).

A claim the user wants but the exemplar lacks becomes a one-off slot for this application (declared in `plan.json`, judged by the gate) or a promotion into the exemplar — never a reworded slot.

If context is tight (post-compaction or near the limit), read `job_docs/core/quickref.md` (same path resolution) — the distilled floor and the "when lost" protocol.

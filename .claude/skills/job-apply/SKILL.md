---
name: job-apply
description: Use to APPLY to a specific job posting once the knowledge base and goals exist — turns a posting URL or pasted text into a verified application package (tailored ATS-safe CV + company-specific cover letter, both trace-mapped to the knowledge base). Triggers on 'apply to this', 'here's a posting', 'tailor my CV for this job', 'write a cover letter for this role', or a pasted job description/link. NOT for building the knowledge base (job-intake) or setting targets (job-goals).
---

Read `job_docs/core/tailoring_method.md` and follow it end to end. Locate it as follows: use `job_docs/core/tailoring_method.md` in the project root if present (drop-in install); otherwise read `../../../job_docs/core/tailoring_method.md` relative to this skill's directory (plugin install). The standards it references (`job_docs/standards/…`) and the CV skeleton (`job_docs/templates/cv_template.md`) resolve the same way; pass **resolved absolute paths** to the agents — they don't inherit this skill's location. If neither resolves, report the broken install and stop — never search the filesystem for `job_docs`.

The pipeline this skill orchestrates:

1. **Preconditions**: verified knowledge base + current `goals.md` **in the current working directory** — one existence check, not a search. If `knowledge/` isn't there, stop immediately and route to `job-intake` / `job-goals`; never hunt for a knowledge base elsewhere on the filesystem.
2. **Capture** the posting (WebFetch or pasted text) → `applications/<company>/jd.md` with the requirement breakdown.
3. **The fit gate** (per `job_docs/core/fit_check.md`, same path resolution): liveness + location sanity, binary constraints screen, evidence-cited fit score 1–5 with its band, legitimacy tier — the verdict gets said **before anything is built**. Search budget: 2 WebSearch queries by default, 5 max when genuinely uncertain, no sub-agents; a user override wins and is recorded in `jd.md` and the tracker.
4. **ATS keyword check** (per `job_docs/standards/ats_rules.md`, via `scripts/ats_coverage.py`) **before writing anything**; verifiable gaps get mini-interviewed into the KB now.
5. **Company research** → `notes.md` — reuse the fit gate's findings first; WebSearch only for what's still missing.
6. **Select KB files** via `knowledge/INDEX.md` — targeted context, never the whole KB.
7. **Dispatch** the `cv-tailor` and `cover-letter-writer` agents in parallel (with the exemplar paths when verified masters exist), then run `scripts/trace_check.py` and `scripts/claim_ledger.py check` — plus `scripts/master_diff.py` with a master — passing their reports (and step 4's) to the `application-verifier` gate — **fix → re-verify until CLEAN**, then `scripts/claim_ledger.py record`. Fix and re-verify rounds **continue the same agents via SendMessage** (writer with the findings, verifier with what changed), never fresh launches; relaunch only if a continuation fails or the KB selection changed. Never present documents with open BLOCKER/MAJOR findings.
8. **Close**: present with the 3-line summary, update `tracker.csv` via `scripts/tracker.py` (per `job_docs/lifecycle/tracking.md`, `fit_score` included), offer rendering only if the user wants a file format (`job_docs/standards/rendering.md`).

If the user asks to include something the KB can't back, follow `job_docs/core/override_protocol.md` exactly: warn once, confirm, get details, record in `overrides.md` — never fight, never volunteer.

If context is tight (post-compaction or near the limit), read `job_docs/core/quickref.md` (same path resolution) — the distilled floor and the "when lost" protocol.

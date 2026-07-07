# Orchestration Registry — advised skills & the availability check

This plugin assumes **nothing is installed**. The workflow runs end-to-end with built-in tools and markdown output; the skills below are **advised, not required** — each raises quality or convenience for one role. Siblings: `dev-workflow`'s and `craft-workflow`'s `core/orchestration.md`.

## The availability check (run by `job-intake` on first use)

1. Inspect the **skills and tools actually available this session** (the available-skills list and built-in tools).
2. For each advised entry, mark **Available ✓** or **Not present**.
3. Report a compact table: role, skill, present/absent, with the one-line "adds" for anything missing.
4. **Never block.** Proceed regardless — markdown output and manual procedures cover every gap. A capability may exist under a different name (workspaces often namespace skills, e.g. `cs:capture`); any equivalent skill filling the same role counts.

## Built-in (always available)

| Tool              | Role                                                                                                                   |
| :---------------- | :--------------------------------------------------------------------------------------------------------------------- |
| `WebFetch`        | Pull the full text of a job posting from its URL (Step 1 of `core/tailoring_method.md`)                                |
| `WebSearch`       | Company research before writing (Step 3); salary benchmarks; market checks                                             |
| `AskUserQuestion` | Interview mechanics (`core/interview_protocol.md`), override confirmation, judgment calls                              |
| Agent tool        | Dispatch `cv-tailor`, `cover-letter-writer`, `application-verifier`; `general-purpose` for multi-step company research |

## Advised skills

### Document rendering — `pdf`, `docx` (Anthropic skills)
- **Adds:** rendering `cv.md` / `cover.md` to a submittable file when a portal demands one. Only invoked on user request — see `standards/rendering.md` for options and market caveats.
- **Without it:** deliver markdown; `pandoc` on the system is an alternative renderer.

### Tracker as spreadsheet — `xlsx`
- **Adds:** a formatted spreadsheet view of `tracker.csv` when the user wants one.
- **Without it:** `tracker.csv` is the source of truth and needs no tooling.

### Long-form co-drafting — `doc-coauthoring`
- **Adds:** structured collaborative refinement for a cover letter the user wants to work on line by line.
- **Without it:** iterate in chat against `standards/cover_letter_rules.md`.

### Brain-dump intake — e.g. `capture`
- **Adds:** converts an unstructured info dump (a pasted posting + commentary, scattered career notes) into structured input without losing items.
- **Without it:** structure the dump into the KB/`jd.md` templates yourself.

### Follow-up reminders — `schedule`
- **Adds:** automated reminders matching `next_action` dates in the tracker.
- **Without it:** the session-start tracker read surfaces due follow-ups (see `lifecycle/tracking.md`).

### Annotation review — e.g. `plannotator`
- **Adds:** per-section human annotation on a drafted CV or letter for precise feedback rounds.
- **Without it:** collect feedback in chat.

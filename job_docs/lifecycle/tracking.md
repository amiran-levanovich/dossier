# Tracking — the application log

`tracker.csv` in the job folder root is the single source of truth for where every application stands. It is plain CSV so it needs no tooling, diffs cleanly, and any session can read it in one call.

## Columns

```
company,role,date_applied,status,next_action,link,notes,stage_reached,date_closed
```

- `stage_reached` — how far the application got before closing: `none` (never reached a human — ATS/volume filter), `screen`, `tech`, or `final`. Blank while the application is active.
- `date_closed` — the date a terminal status (`offer` / `rejected` / `withdrawn`) was recorded. Together with `date_applied` it gives time-to-response; both columns feed `lifecycle/analytics.md`.
- **Migration**: trackers created before these columns existed just add the two names to the header row; old rows may stay short or gain trailing commas — both read fine, and blanks are legitimate (analytics infers what it can from `notes`).

## Status lifecycle

```
to_apply → applied → interview → offer
                └──────┴─────────┴──→ rejected | withdrawn
```

- `to_apply` — package prepared or posting shortlisted, not yet submitted
- `applied` — submitted; `date_applied` set the day it actually went out
- `interview` — any stage from recruiter screen to final panel; which stage goes in `notes`
- `offer` / `rejected` / `withdrawn` — terminal

## Rules

- **Update immediately on any status change** — the tracker never drifts behind reality. The session-start cross-check (`core/job_workflow.md`) exists to catch drift, not to excuse it.
- Every `applied` row has `date_applied`, `link`, and a **concrete, dated** `next_action` — default: "follow up if no reply by <date_applied + 2 weeks>". Vague next actions ("wait") are defects.
- Every `interview` row's `next_action` is the next concrete step ("prep for tech screen <date>", "send thank-you note").
- On any terminal status: set `date_closed` and `stage_reached` **in the same edit** — a closure without them is invisible to analytics.
- On rejection: record in `notes` whether it was a **generic auto-reply** (came fast, no personalization — that's the ATS/screening filter, not a human read) or a **human rejection** (took days, named specifics, or came post-interview). The distinction drives the post-mortem — see `lifecycle/postmortem.md` — and disambiguates `stage_reached` `none` vs `screen` when unsure.
- One row per application. Re-applying to the same company later gets a new row.

## Session integration

- **Session start:** read the tracker in full; surface due/overdue `next_action` dates unprompted.
- **Session close:** every company touched this session has a correct row; every active row has a dated `next_action`. (Full checklist in `core/job_workflow.md`.)
- If the user wants a formatted view, the `xlsx` skill can generate one from the CSV — the CSV remains the source of truth (`core/orchestration.md`).
- For patterns **across** applications (funnel, where applications die, pace), run `lifecycle/analytics.md`.

# Tracking — the application log

`tracker.csv` in the job folder root is the single source of truth for where every application stands. It is plain CSV so it needs no tooling, diffs cleanly, and any session can read it in one call.

## Columns

```
company,role,date_applied,status,next_action,link,notes
```

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
- On rejection: record in `notes` whether it was a **generic auto-reply** (came fast, no personalization — that's the ATS/screening filter, not a human read) or a **human rejection** (took days, named specifics, or came post-interview). The distinction drives the post-mortem — see `lifecycle/postmortem.md`.
- One row per application. Re-applying to the same company later gets a new row.

## Session integration

- **Session start:** read the tracker in full; surface due/overdue `next_action` dates unprompted.
- **Session close:** every company touched this session has a correct row; every active row has a dated `next_action`. (Full checklist in `core/job_workflow.md`.)
- If the user wants a formatted view, the `xlsx` skill can generate one from the CSV — the CSV remains the source of truth (`core/orchestration.md`).

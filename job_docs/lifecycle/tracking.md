# Tracking — the application log

`tracker.csv` in the job folder root is the single source of truth for where every application stands. It is plain CSV so it needs no tooling, diffs cleanly, and any session can read it in one call.

**Writing rows:** use `scripts/tracker.py --file tracker.csv {add|update|show}` (resolve `scripts/` as in `core/tailoring_method.md`). It handles column order, CSV quoting, and header migration deterministically, and warns on the defects below (an `applied` row missing `date_applied`/`link`/`next_action`; a terminal status missing `stage_reached`) — you still supply every value, since what to write is judgment. Hand-editing the CSV stays valid; the script is a convenience, not a gatekeeper.

## Columns

```
company,role,date_applied,status,next_action,link,notes,stage_reached,date_closed,fit_score
```

- `stage_reached` — how far the application got before closing: `none` (never reached a human — ATS/volume filter), `screen`, `tech`, or `final`. Blank while the application is active.
- `date_closed` — the date a terminal status (`offer` / `rejected` / `withdrawn`) was recorded. Together with `date_applied` it gives time-to-response; both columns feed `lifecycle/analytics.md`.
- `fit_score` — the overall score from the fit gate (`core/fit_check.md`), set when the row is created and never revised afterward — it records the pre-application judgment, and analytics reads it against outcomes to check the gate's calibration. If the user overrode the verdict, the override note lives in `notes` (per `core/fit_check.md`).
- **Migration**: trackers created before a column existed just add the missing names to the header row (in this order); old rows may stay short or gain trailing commas — both read fine, and blanks are legitimate (analytics infers what it can from `notes`; a blank `fit_score` simply predates the gate).

## Status lifecycle

```
to_apply → applied → interview → offer
                └──────┴─────────┴──→ rejected | withdrawn
```

- `to_apply` — package prepared or posting shortlisted, not yet submitted
- `applied` — submitted; `date_applied` set the day it actually went out
- `interview` — any stage from recruiter screen to final panel; which stage goes in `notes`
- `offer` / `rejected` / `withdrawn` — terminal. An `offer` row is terminal for analytics (`date_closed` + `stage_reached` set as usual) but stays *live for action*: it keeps a dated `next_action` through contract review and negotiation ("send questions by <date>", "counter by <date>", "sign-by deadline <date>") until the contract is signed or declined — see `lifecycle/offer.md`. The outcome lands in `notes`.

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

# Fit Check — evaluate before you apply

This is the gate between capturing a posting and building anything: five minutes of evaluation before forty minutes of production. It runs as **Step 2 of `core/tailoring_method.md`** — after `jd.md` is written, before the ATS keyword check. Its output is a filled `## Fit` block in `jd.md` and a verdict said out loud.

> **The verdict is advice, not a wall.** The user's decision always wins — an override is recorded, never argued with twice. What the gate refuses to do is stay silent while a weak application gets built.

**Research budget: at most 5 WebSearch queries for the whole check. No sub-agents.** The gate exists to save time; a gate that costs more than the application defeats itself. Spend the budget where the posting is uncertain (comp, legitimacy), skip it where the JD and KB already answer. When it runs out, score with what's on hand and mark the affected dimension *low confidence*. Anything found here (company news, salary data) is reusable in the Step 4 research notes — never search for the same fact twice.

---

## Step 1 — Liveness and location sanity

Before evaluating content, check the posting is real and readable:

- **Liveness.** If the posting came by URL, inspect what WebFetch actually returned — not just that it returned *something*. "No longer accepting applications", "position filled", an expired-posting notice, a redirect to a careers homepage, or a login wall with no JD text: the pipeline **stops here** — report it, and continue only if the user pastes the real text (note the source in `jd.md`). A dead link never proceeds silently on cached or remembered content.
- **Location consistency.** Compare the posting's location/remote field against the JD body. Aggregators and reposts routinely mislabel — a header saying "Remote — Germany" over a body requiring "3 days/week in the Munich office" is a mismatch. When they disagree, quote both **verbatim** in the `## Fit` block and score against the body — it is the authoritative text.

## Step 2 — Constraints screen (binary, before any scoring)

Read `knowledge/constraints.md` and `knowledge/lessons.md` first:

- A violated **hard constraint** (excluded industry, hard-no company type, a red line from `constraints.md`) is a **kill-switch, not a low score**: the verdict is *recommend against* regardless of everything else, citing the constraint verbatim. Constraints are never averaged away by a good salary.
- A **known-fatal lesson** — a `hard-filter` the search has already died at (e.g. a degree-gated ATS) — is surfaced the same way: name the lesson line and its date.

The user can still override (Step 5), but the screen result stays recorded either way.

## Step 3 — Fit score (1–5)

Four dimensions, each scored 1–5, **each citing its evidence** — a quote from the JD, a named KB entry, a `goals.md` line, or a search result. A score without a citation is inflation; where the evidence is missing, the score is a 3 marked *low confidence*, not an optimistic guess.

| Dimension           | 5 looks like                                                                   | 1 looks like                                                                 |
| :------------------ | :------------------------------------------------------------------------------ | :---------------------------------------------------------------------------- |
| **KB match**        | Every must-have covered by a verified KB entry                                 | Most must-haves are real gaps the KB can't back                              |
| **Goals alignment** | Title, seniority, location, remote policy all inside `goals.md` targets        | Wrong seniority band or a setup `goals.md` excludes                          |
| **Comp vs target**  | Reliable number at or above the `goals.md` target                              | Reliable number below the floor                                              |
| **Red flags**       | Specific, coherent JD; clear role scope                                        | Boilerplate JD, scope sprawl, "wear many hats" over a senior title           |

**Comp reliability weighting.** How much the comp dimension counts depends on how trustworthy the number is — by company type and source:

| Comp source                                                                  | Reliability | Weight |
| :---------------------------------------------------------------------------- | :----------- | :------ |
| Salary band printed in the posting (incl. legally mandated, e.g. AT KV)      | High        | 1.0    |
| Public company / large scaleup with dense salary data (kununu, Glassdoor, levels) | Medium      | 0.5    |
| SME / agency / early startup — thin or no data, estimate only                | Low         | 0.25   |

**Overall = (KB + goals + flags + weight × comp) ÷ (3 + weight)**, rounded to one decimal. With low reliability and no real evidence, score comp a flat 3 — an invented number weighted low is still an invented number.

| Overall   | Band                                                                              |
| :--------- | :--------------------------------------------------------------------------------- |
| ≥ 4.5     | **Apply now** — priority target, move straight on                                 |
| 4.0 – 4.4 | **Worth it** — solid, proceed                                                     |
| 3.5 – 3.9 | **Only with a reason** — proceed only if the user names one; the reason is recorded |
| < 3.5     | **Recommend against** — the same time invested elsewhere buys more                |

## Step 4 — Legitimacy tier (outside the score)

Legitimacy is orthogonal to fit — a perfect-fit posting can still be a ghost. Assign **High / Caution / Suspicious** from observable signals:

| Signal                   | Where to look                                                                       |
| :------------------------ | :----------------------------------------------------------------------------------- |
| Posting age & reposts    | Posting metadata; the same JD recurring across boards                               |
| Apply path               | Company ATS / own domain vs a free-mail address or a form on an unrelated domain    |
| JD specificity           | Real team/stack/product detail vs interchangeable boilerplate                       |
| Requirements realism     | Coherent stack and seniority vs impossible combos, senior scope at junior pay       |
| Company news             | Recent layoffs or hiring-freeze reports while "actively hiring"                     |
| Prior tracker rows       | Earlier applications to this company: ghosted, same role reposted since             |

**Signals, not accusations — mandatory framing.** Report what is observable ("posted 90+ days ago, reposted three times, applications go to a gmail.com address"), never a conclusion ("this is a scam", "this is a ghost posting"). The tier orders skepticism; it doesn't convict the company.

- **High** — proceed normally.
- **Caution** — proceed, but name the signals so the user invests accordingly.
- **Suspicious** — recommend not building the package; proceeding anyway is a user override.

## Step 5 — Record and decide

Fill the `## Fit` block in `jd.md`:

```markdown
## Fit

**Liveness:** live (fetched 2026-07-14)   **Location check:** consistent | MISMATCH: "<header>" vs "<body>"
**Constraints screen:** pass | FAIL — <constraint or lesson line, verbatim>
**Fit score: 3.9 — worth it** (KB 4 · goals 5 · comp 3 [low reliability] · flags 4)
- KB match 4: <evidence — must-haves vs named KB entries; real gaps land here after the ATS check>
- Goals 5: <evidence — the goals.md lines that match or clash>
- Comp 3: <evidence — the number, its source, its reliability tier>
- Red flags 4: <evidence — quoted JD signals, or "none">
**Legitimacy: High** — <the observed signals, or "no adverse signals">
**Decision:** proceed | skip | user override — <the user's stated reason, dated>
```

Then state the verdict in chat — score, band, tier, and the one or two decisive citations — **before anything is built**. Below *worth it*, or below a High tier, stop for the user's call.

**User override — always wins.** Same shape as the override protocol in `core/tailoring_method.md`: state the concern once, concretely; no second warning; never fight. Record the decision in the `Decision` line **and** in the tracker row's `notes` ("user override: applied at 3.1 — <reason>"). Skipping a high-score posting is recorded the same way. Either way the score lands in the tracker's `fit_score` column (`lifecycle/tracking.md`) when the row is created.

The score's afterlife: `lifecycle/analytics.md` reads `fit_score` across the whole tracker to check the gate's calibration — scores that don't separate outcomes are evidence of inflation, and the evidence rule above is the fix.

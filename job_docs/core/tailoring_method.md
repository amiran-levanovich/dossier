# Tailoring Method — the per-application pipeline

This is the procedure behind the `job-apply` skill: job posting in, verified application package out. It is the workflow's production line, and its quality bar is held by **traceability** and the **verifier gate** — not by trust in any single generation step.

**Preconditions.** A knowledge base exists **in the current working directory** with verified content, and `knowledge/goals.md` is current. This is one existence check, not a search — if `knowledge/` isn't there, stop immediately and route to `job-intake` / `job-goals`; never hunt for a knowledge base elsewhere on the filesystem, and do not tailor from a thin KB.

---

## Step 1 — Capture the posting

Get the full text: WebFetch for a URL (ask for a paste if it's behind a login wall), or take pasted text directly. Create `applications/<company>/` (kebab-case company name) and write `jd.md`:

```markdown
# <Company> — <Role Title>

**URL:** <link or "pasted">   **Location:** <location + remote policy>
**Salary:** <if listed>   **Language:** <posting language>   **Captured:** <date>

## Must-haves
- <hard requirements: skills, years, credentials, languages>

## Nice-to-haves
- <explicitly optional or "bonus" items>

## ATS keywords
<every named technology, tool, credential, and recurring phrase — exact spelling as in the posting>

## Fit
<filled by the fit gate — block template in core/fit_check.md>
```

## Step 2 — The fit gate (before any research or writing)

Run `core/fit_check.md` end to end: liveness and location sanity, the binary constraints screen (against `constraints.md` and `knowledge/lessons.md`), the evidence-cited fit score with its band, and the legitimacy tier. It fills the `## Fit` block in `jd.md` and the verdict gets said out loud **now** — whether to proceed against it is the user's call, recorded per that doc. Research inside the gate is capped at 5 WebSearch queries; whatever it finds feeds Step 4's notes.

## Step 3 — ATS keyword check (before writing anything)

Per `standards/ats_rules.md`: cross-check every ATS keyword from `jd.md` against the KB. Three buckets:

- **Covered** — a verified KB entry names it.
- **Verifiable gap** — the user plausibly has it but the KB doesn't record it → run a 2-minute mini-interview now, write the result into the KB (this is how the KB keeps growing after intake).
- **Real gap** — the user doesn't have it → record under the KB-match evidence line in `jd.md`'s `## Fit` block. It may only enter the documents through the override protocol below.

## Step 4 — Company research

Quick WebSearch: what the company does, size, recent news, product, tone of their own postings. Start from what the fit gate already found — don't repeat its queries. Write 5–8 lines into `applications/<company>/notes.md`. The cover letter must reference something real from this.

## Step 5 — Select knowledge

Read `knowledge/INDEX.md` and pick the files relevant to *this* posting — typically 2–3 role files, `skills.md`, plus the always-read set (`profile.md`, `constraints.md`, `goals.md`). Do not pass the whole KB to the agents; targeted context is what makes tailoring sharp.

If `knowledge/portfolio.md` exists, read it and apply its verdicts: only assets marked `showcase` whose **Cite when** guidance fits this posting may be linked. Include the register in the writers' KB selection when any asset qualifies — and leave it out (so no link appears) when none does.

`knowledge/lessons.md` is orchestrator context for the fit and keyword checks — it is **never** passed to the writer agents; their claims come from verified KB entries only.

## Step 6 — Dispatch the writers (parallel)

Launch **`cv-tailor`** and **`cover-letter-writer`** in one message, each with: the `jd.md` path, the selected KB file paths, `notes.md`, the standards docs (`standards/cv_rules.md`, `standards/ats_rules.md`, `standards/cover_letter_rules.md`, `standards/dach_conventions.md` when the market applies, `templates/cv_template.md` for the CV), the output paths, and `overrides.md` if it exists. Each agent writes its document **plus a trace file** mapping every claim to its source.

## Step 7 — The verifier gate (loop until CLEAN)

Launch **`application-verifier`** with the same inputs plus both documents and trace files. It returns CLEAN or severity-ordered findings.

- Findings → fix them (re-dispatch the relevant writer with the findings, or edit directly for trivial ones) → **re-verify the whole package**. A fix can break something else; only a fully CLEAN round counts.
- Re-verify rounds **continue the same verifier** (SendMessage with a short summary of which files changed and how) instead of launching a fresh agent — it already holds the KB and standards in context and only re-reads what changed, while still re-running every check on the whole package. Launch fresh only if the continuation fails or the KB selection changed.
- Never present documents to the user while BLOCKER or MAJOR findings are open. MINOR findings may be presented as a short list alongside the documents if the user is in a hurry — their call.

## Step 8 — Present and close

Present `cv.md` and `cover.md` with a 3-line summary: strongest matches surfaced, gaps and how they were handled, verifier result (including the override INFO line if any). Then:

- Update `tracker.csv` per `lifecycle/tracking.md` (new row `to_apply`, or `applied` with today's date once the user submits; `next_action` two weeks out by default; `fit_score` from the Step 2 gate, plus an override note in `notes` if the user went against the verdict).
- Offer rendering **only if the user wants a file format** — options and market caveats in `standards/rendering.md`. Markdown is the deliverable by default.

---

## User-directed overrides — the escape hatch

The no-fabrication rule binds **the agents, not the user**. If the user explicitly asks to include something the KB cannot back ("just add Kafka to this one"), do not fight them:

1. **Warn once, concretely.** One short paragraph: what an interviewer or background check could probe, and what the honest alternative would be (e.g. `"Kafka — actively ramping"`). No moralizing, no repetition, no second warning later.
2. **Confirm** via AskUserQuestion — proceed / use the honest alternative / drop it.
3. **Get details.** If they proceed, briefly interview for what exactly to claim (which role, what depth, what wording) so the addition is coherent and the user can defend it live.
4. **Record.** Write the claim to `applications/<company>/overrides.md`, marked `user-directed`, with date and scope. **It never enters `knowledge/`** — the KB stays true; the override is per-application.

Trace entries may then point at `overrides.md`. The verifier treats override-sourced claims as sourced and reports them as a single INFO line (`N user-directed claims present`) — never as findings. Agents never volunteer an override, never extend one beyond what the user specified, and never carry one silently into a different application.

---

## Trace file format

`cv_trace.md` / `cover_trace.md`, one line per claim-bearing element:

```markdown
- "<the bullet / sentence, abbreviated>" → roles/acme.md#achievements
- "<...>" → skills.md#databases
- "<...>" → overrides.md (user-directed, 2026-07-07)
```

Structural/neutral text (section headings, contact lines from `profile.md`, logistics phrasing) needs no trace line. Everything that asserts experience, a skill, an outcome, or a credential does.

# Tailoring Method — the per-application pipeline

The procedure behind the `job-apply` skill: job posting in, application package out. **Two LLM dispatches per application** — one writer, one verifier — and everything between them is deterministic script.

The quality bar is not re-earned per application. The exemplar (`master_cv.md`) was verified once and signed off (ADR-0004), and an application CV is trustworthy exactly to the degree that it is *unchanged* from it: the writer selects and orders slots and has no mechanism to reword one (ADR-0005). What still needs judgment is the letter and any one-off slot — which is what the single verifier round spends its budget on.

**Helper scripts.** The mechanical steps run dependency-free Python in `scripts/`, resolved like `job_docs` (project-root `scripts/`, else `../../../scripts/` from the skill dir). Each returns a short report; you apply judgment. If a script errors or is absent, do the step by hand — never a hard dependency.

**Preconditions.** A signed-off `master_cv.md`, a `story_bank.md`, and a current `goals.md` exist **in the current working directory**. One existence check, not a search. Signed off means `master_cv_signoff.md` exists and its last recorded hash matches `sha256sum master_cv.md` — a hash that no longer matches means the exemplar was edited since signing, so it counts as unsigned until re-signed (`lifecycle/exemplar.md`). Otherwise stop and route to `job-intake`; a deadline never justifies applying without the sign-off.

---

## Step 1 — Capture the posting

Get the full text: WebFetch for a URL (ask for a paste if it's login-walled), or take pasted text directly. Create `applications/<company>/` (kebab-case company name) and write `jd.md`:

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

Run `core/fit_check.md` end to end: liveness and location sanity, the binary constraints screen, the evidence-cited fit score with its band, and the legitimacy tier. It fills the `## Fit` block in `jd.md` and the verdict is said **now** — whether to proceed is the user's call, recorded per that doc. Research inside the gate defaults to 2 WebSearch queries (5 max when the posting is genuinely uncertain); whatever it finds feeds Step 4's notes.

## Step 3 — ATS keyword check (before writing anything)

Per `standards/ats_rules.md`: `scripts/ats_coverage.py jd.md --exemplar master_cv.md --bank story_bank.md` — literal whole-token matching, alias-aware, bucketed COVERED / PROMOTABLE / GAP, nothing read into the main session (fallback: batch-Grep both, ≤5 calls). Then:

- **Covered** (`COVERED`) — the exemplar names it; trimming can use it. The report names the sections (achievement-backed vs a bare skills-list mention) and marks `(as "…")` when the exemplar's spelling differs — assembly swaps that in.
- **Promotable** (`PROMOTABLE`) — the bank has it, the exemplar doesn't. The bank is wider by design (ADR-0006), so this is a decision, not a defect: promote the fact into the exemplar as a slot and verify that slot, or leave it unclaimed.
- **Real gap** (`GAP`) — neither has it → record in `jd.md`'s `## Fit` block. Feeds the fit score, never the documents.

## Step 4 — Company research

Start from what the fit gate found — its findings usually cover this step, so the default is **zero new searches**. WebSearch only for what's still missing (company, size, recent news, product, tone), never repeating a gate query. Write 5–8 lines into `applications/<company>/notes.md`; the cover letter must reference something real from this.

## Step 5 — Dispatch the writer (dispatch 1 of 2)

Extract the slot map first: `scripts/cv.py map master_cv.md --out slots.json`. The exemplar itself is **not** passed to the writer — the slot map is its whole view of it, which is what makes rewording unavailable rather than merely forbidden.

Launch **`application-writer`** with: `slots.json`, the `jd.md` path, `notes.md`, `story_bank.md`, the standards docs (`standards/cv_rules.md`, `standards/ats_rules.md`, `standards/cover_letter_rules.md`, `standards/dach_conventions.md` when the market applies), the coverage report from Step 3, and the output paths for `plan.json` and `cover.md`.

One agent produces both, so the **lead evidence** is picked once: the slot answering the posting's hardest requirement leads the CV, and the letter argues from that same slot. The bank is there for the letter's framing and motivation only — never for a fact, because the letter may assert nothing the assembled CV doesn't (ADR-0007). The writer reports gaps; it never proposes a one-off unprompted.

## Step 6 — Assemble (deterministic, no dispatch)

`scripts/cv.py build plan.json --exemplar master_cv.md --out-dir <app folder> --posting jd.md`

Kept slots are rendered byte-verbatim, proved by a verbatim self-test, and the alias pass then swaps in the posting's spellings and logs every swap to `alias_log.md` (ADR-0008). A faulty plan exits 1 and writes **nothing** — hand its diagnostic back to the *same* writer (SendMessage, findings only) for one re-dispatch. That is a repair, not a round: nothing was published.

## Step 7 — The gate (dispatch 2 of 2)

Launch **`application-verifier`** with `cv.md`, `cover.md`, `jd.md`, `story_bank.md`, the standards docs, and the `cv.py build` report pasted in. It runs **one round**. Two things are left to judge, and the inherited verdict covers everything else:

- **Fact containment** — every fact the letter asserts (number, technology, outcome, credential) appears in the assembled `cv.md`. Framing, motivation and company angle are free.
- **Any one-off slot** — the build report lists them. These are the only lines the exemplar's verdict does not cover, so they get full rigor against the bank.

There is no round cap because there is no loop. A finding is one of two things:

- **An invented fact** → the writer removes it (continue the same writer). Removal cannot introduce a claim, so it needs no re-verification.
- **A promotion candidate** → the user's decision, not a defect. If they promote it, add the slot to the exemplar, verify that slot, then re-run Steps 5–6; only the new slot needs judgment.

Never present with an open BLOCKER or MAJOR. MINOR findings may go in a short list alongside the documents if the user is in a hurry — their call.

## Step 8 — Present and close

Present `cv.md` and `cover.md` with a 3-line summary: the lead evidence surfaced, gaps and how handled, the verifier result. Then:

- Update `tracker.csv` per `lifecycle/tracking.md` via `scripts/tracker.py --file tracker.csv add …` (handles column order, quoting, migration); you supply the judgment values — `--status`, `--fit-score` from the Step 2 gate, and a dated `--next-action` (default two weeks out).
- Offer rendering **only if the user wants a file format** — `standards/rendering.md`. Markdown is the deliverable by default.

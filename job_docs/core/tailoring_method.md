# Tailoring Method — the per-application pipeline

The procedure behind the `job-apply` skill: job posting in, application package out. **Two LLM dispatches per application** — one writer, one verifier — and everything between them is deterministic script.

The quality bar is not re-earned per application. The exemplar (`master_cv.md`) was verified once and signed off (ADR-0004), and an application CV is trustworthy exactly to the degree that it is *unchanged* from it: the writer selects and orders slots and has no mechanism to reword one (ADR-0005). What still needs judgment is the letter and any one-off slot — which is what the single verifier round spends its budget on.

**Helper scripts.** The mechanical steps run dependency-free Python in `scripts/`, resolved like `job_docs` (project-root `scripts/`, else `../../../scripts/` from the skill dir). Each returns a short report; you apply judgment. If a script errors or is absent, do the step by hand — never a hard dependency.

**Preconditions.** A signed-off `master_cv.md`, a `story_bank.md`, and a current `goals.md` **in the current working directory** — one existence check, not a search. Signed off means `master_cv_signoff.md`'s last recorded hash matches `sha256sum master_cv.md`; a hash that no longer matches means the exemplar was edited after signing, so it counts as unsigned (`lifecycle/exemplar.md`). Otherwise stop and route to `job-intake` — a deadline never justifies applying without the sign-off.

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

## Step 2 — ATS keyword check (deterministic, before the gate)

Per `standards/ats_rules.md`: `scripts/ats_coverage.py jd.md --exemplar master_cv.md --bank story_bank.md` — literal whole-token matching, alias- and plural-aware, bucketed COVERED / PROMOTABLE / GAP, nothing read into the main session (fallback: batch-Grep both, ≤5 calls).

It runs **before** the gate because it costs no LLM call and no network, and the gate's coverage dimension is evidence-based only if it has this report to cite instead of an impression. The buckets:

- **Covered** (`COVERED`) — the exemplar names it; trimming can use it. The report names the sections (achievement-backed vs a bare skills-list mention) and marks `(as "…")` when the exemplar's spelling differs — assembly swaps that in.
- **Promotable** (`PROMOTABLE`) — the bank has it, the exemplar doesn't. The bank is wider by design (ADR-0006), so this is a decision, not a defect: promote the fact into the exemplar as a slot and verify that slot, or leave it unclaimed.
- **Real gap** (`GAP`) — neither has it → record in `jd.md`'s `## Fit` block. Feeds the fit score, never the documents.

## Step 3 — The fit gate (before any research or writing)

Run `core/fit_check.md` end to end: liveness, the binary constraints screen against the search meta at the job-folder root, the evidence-cited score — Step 2's report is what its coverage dimension cites — and the legitimacy tier. It fills `jd.md`'s `## Fit` block, and the verdict is said **now**: proceeding is the user's call, recorded per that doc. Gate research defaults to 2 WebSearch queries (5 max when the posting is genuinely uncertain) and feeds Step 4's notes.

## Step 4 — Company research

Start from what the fit gate found — its findings usually cover this step, so the default is **zero new searches**. WebSearch only for what's still missing (company, size, recent news, product, tone), never repeating a gate query. Write 5–8 lines into `applications/<company>/notes.md`; the cover letter must reference something real from this.

## Step 5 — Dispatch the writer (dispatch 1 of 2)

Extract the slot map first: `scripts/cv.py map master_cv.md --out slots.json`. The exemplar itself is **not** passed to the writer — the slot map is its whole view of it, which is what makes rewording unavailable rather than merely forbidden.

Launch **`application-writer`** with: `slots.json`, the `jd.md` path, `notes.md`, `story_bank.md`, the standards docs (`standards/cv_rules.md`, `standards/ats_rules.md`, `standards/cover_letter_rules.md`, `standards/dach_conventions.md` when the market applies), the coverage report from Step 2, and the output paths for `plan.json` and `cover.md`.

One agent produces both, so the **lead evidence** is picked once: the slot answering the posting's hardest requirement leads the CV, and the letter argues from that same slot. The bank supplies the letter's framing and motivation, never a fact (ADR-0007). The writer reports gaps; it never proposes a one-off unprompted.

### When the user directs a claim the exemplar lacks

The no-fabrication rule binds **the agents, not the user**. If the user asks for something the exemplar cannot back ("just add Kafka to this one"), don't fight them:

1. **Warn once, concretely** — what an interviewer or a background check could probe, and the honest alternative (`"Kafka — actively ramping"`). No moralizing, no second warning later.
2. **Confirm** via AskUserQuestion — proceed / honest alternative / drop it — then **get the details** (role, depth, wording) so the claim is defensible live.
3. **Record it as a one-off slot** in `plan.json`, never as a reworded slot. It is scoped to this application, the gate judges it at full rigor (Step 7), and it reaches `master_cv.md` only through a deliberate promotion (`lifecycle/exemplar.md`).

## Step 6 — Assemble (deterministic, no dispatch)

`scripts/cv.py build plan.json --exemplar master_cv.md --out-dir <app folder> --posting jd.md`

Kept slots are rendered byte-verbatim, proved by a verbatim self-test, then the alias pass swaps in the posting's spellings and logs each one to `alias_log.md` (ADR-0008). A faulty plan exits 1 and writes **nothing** — hand its diagnostic back to the *same* writer (SendMessage, findings only) for one re-dispatch: a repair, not a round, since nothing was published.

## Step 7 — The gate (dispatch 2 of 2)

Launch **`application-verifier`** with `cv.md`, `cover.md`, `jd.md`, `story_bank.md`, the standards docs, and the `cv.py build` report pasted in. It runs **one round**. Two things are left to judge, and the inherited verdict covers everything else:

- **Fact containment** — every fact the letter asserts (number, technology, outcome, credential) appears in the assembled `cv.md`, **attached to what the CV attaches it to**. Framing, motivation and company angle are free.
- **Any one-off slot** — the build report lists them. These are the only lines the exemplar's verdict does not cover, so they get full rigor against the bank.

There is no round cap because there is no loop. A finding is one of three things:

- **An invented fact** → the writer removes it (continue the same writer). Removal cannot introduce a claim, so it needs no re-verification.
- **A merged attribution** → the facts are all in the CV, joined into a claim it doesn't make: one bullet's metric on another's verb, *built* widened to *owns*, a past role written as present. The facts are contained; the sentence isn't. Continue the same writer to **split it back apart**, each half keeping its own slot's attribution.
- **A promotion candidate** → the user's decision, not a defect. If they promote it, add the slot to the exemplar, verify that slot, then re-run Steps 5–6; only the new slot needs judgment.

A split is new phrasing, so unlike a removal it *could* introduce a claim. It is constrained rather than re-judged: the writer only redistributes facts across attributions the kept slots already carry, and the **main session** — which holds both files and the finding — reads the rewritten sentences against `cv.md` before presenting. No dispatch, so a repair rather than a round. A split that can't be made from kept slots alone becomes a removal.

Never present with an open BLOCKER or MAJOR. MINOR findings may go in a short list alongside the documents if the user is in a hurry — their call.

## Step 8 — Present and close

Present `cv.md` and `cover.md` with a 3-line summary: the lead evidence surfaced, gaps and how handled, the verifier result. Then:

- Update `tracker.csv` per `lifecycle/tracking.md` via `scripts/tracker.py --file tracker.csv add …` (handles column order, quoting, migration); you supply the judgment values — `--status`, `--fit-score` from the Step 3 gate, and a dated `--next-action` (default two weeks out).
- Offer rendering **only if the user wants a file format** — `standards/rendering.md`. Markdown is the deliverable by default.

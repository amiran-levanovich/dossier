# Rejection Post-mortem — learn something from every no

Run when a rejection lands (offer it; don't force it). Goal: identify the most likely cause, state it plainly, and turn it into a concrete adjustment — to the knowledge base, the goals, or the next application. Never soften the analysis; a comforting wrong diagnosis costs future applications.

## Step 1 — Classify the rejection

**Read `knowledge/lessons.md` first** (`core/kb_schema.md`) — the diagnoses already made. If the picture emerging here repeats a logged lesson (same category, same root cause), say so explicitly and escalate to the strategy conversation (`lifecycle/analytics.md`) instead of applying another per-application fix: a lesson learned twice wasn't learned.

Then classify, from the tracker's `stage_reached` and `notes` (see `lifecycle/tracking.md`; legacy rows without `stage_reached` classify from `notes` alone):

- **Generic auto-reply, fast** → the application was filtered by ATS or a volume screen. *A human almost certainly never read it.* Analyze the machine pass (Step 2).
- **Human rejection, pre-interview** → a recruiter read it and passed. Analyze fit signaling: seniority match, summary framing, salary expectations, permit/notice logistics.
- **Post-interview rejection** → the materials worked; the interview didn't. Debrief the user on what was asked and where it wobbled; feed anything learned into the KB stories and `lifecycle/interview_prep.md` for next time.

## Step 2 — Cause checklist (ATS-stage rejections)

Work through in order, against the actual `jd.md` and `cv.md` from the application folder:

1. **Keyword gap** — compare the posting's ATS keywords word-for-word against the submitted CV. Machines are literal; a synonym is a miss. This is the most common cause.
2. **Missing hard credential** — "must have X" (degree level, certification, years, language) that the CV doesn't show. Some filters are binary on these.
3. **Seniority mismatch** — significantly over- or under-qualified on paper; years-of-experience filters are common.
4. **Volume** — 100+ applicants means an aggressive threshold; even small gaps eliminate. Not fixable per-application; informs targeting.
5. **Format** — only if a designed/rendered CV was submitted: complex layout, tables, or image text can fail parsing (`standards/ats_rules.md`).

## Step 3 — State the diagnosis and act

One paragraph: the most likely cause, the evidence, and **one specific fix**. Then apply it where it belongs:

- Missing-but-true keyword → mini-interview it into the KB now (it will serve every future application).
- Recurring hard-credential filter → note in `goals.md` targeting (e.g. avoid postings with a strict degree filter, or target company types that weigh it less).
- Pattern across 3+ rejections at the same stage → escalate from per-application fixes to a strategy conversation: targets, seniority band, market, or materials as a whole. `lifecycle/analytics.md` is the mechanized check — run it rather than counting by eye.

Then close out, three writes:

1. **One lesson line** appended to `knowledge/lessons.md` (format in `core/kb_schema.md`): the diagnosis and the action — `(applied)` when the fix landed this session, `(open)` when it didn't. This is what future fit checks, post-mortems, and analytics read; a post-mortem that skips it taught nothing.
2. The full conclusion in the application folder's `notes.md`.
3. The tracker row closed: `next_action` empty (terminal), `date_closed` and `stage_reached` filled — analytics needs the row complete.

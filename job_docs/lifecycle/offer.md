# Offer Stage — read it calmly, negotiate it deliberately

Run when an offer arrives (kernel routing: update the tracker first, then this doc). Two parts, strictly in order: **read the contract** with a describe-don't-judge companion, then **prepare the negotiation**. No new skill or agent — this is main-session work, and that is a rule, not a convenience:

> **The contract stays local.** Contract text is the most sensitive document this workflow ever touches. It is never passed to a sub-agent, never quoted into a WebSearch query, never rendered into an artifact. Reading, tagging, and drafting all happen in the main session against local files.

> **Never a legal verdict — the absolute boundary.** The companion describes what clauses *say* and how they compare to *common patterns*; it never states what the law is, never judges enforceability or lawfulness, never says "this is illegal", "unenforceable", or "don't sign". Every question of law goes on the questions-for-a-lawyer list instead of being answered. Recommending a lawyer's review is always in bounds; playing one never is.

---

## Part 1 — The contract reading companion

Posture: **describe, don't judge.** The output is understanding and good questions, not verdicts.

### 1. Extraction gate

Contracts usually arrive as PDFs. Before any analysis, confirm the extracted text is actually complete: page count matches, no garbled runs, tables and numbered clauses intact, both languages present if bilingual. If extraction is lossy, **stop and say so** — a clause walk over a partial contract is worse than none, because it reads as complete.

### 2. Promises intake — before reading the contract

Interview the user briefly: what was promised — verbally, by email, in the offer call — during the process? Salary and its parts, bonus terms, remote days, title and level, start date, vacation days, equipment, training budget, relocation help. Write them to `applications/<company>/offer_notes.md`, one line each with where/when it was made. This list is what the clause walk verifies against: **a promise that isn't in the contract is a finding.**

### 3. The clause walk

Go through the contract clause by clause, in document order — never skim, never summarize ranges. For each clause: a one-to-two-line plain-language description of what it says, plus one neutral tag:

| Tag         | Means                                                                                   |
| :----------- | :--------------------------------------------------------------------------------------- |
| `standard`  | Matches the common pattern for this market and role                                     |
| `favorable` | Better for the user than the common pattern                                             |
| `attention` | Deviates from the common pattern or from a recorded promise — worth asking about        |
| `unclear`   | Ambiguous wording — needs clarification before it can even be tagged                    |

Tags describe **deviation from patterns, not legal quality** — `attention` means "ask about this", not "this is wrong". For DACH contracts, walk with the clause taxonomy in `standards/dach_conventions.md` open; it names the clauses to expect and the common patterns to compare against.

### 4. Notable absences

After the walk, list what *isn't* there: recorded promises from `offer_notes.md` missing from the text, and clauses common in this market that the contract omits. Absences are findings of the same rank as deviations — the promise made in the call and missing on paper is the classic one.

### 5. Output — `applications/<company>/offer_prep.md`

```markdown
# <Company> — offer review (<date>)

## Clause walk
| # | Clause | Says (plain language) | Tag |
| :--- | :--- | :--- | :--- |

## Notable absences
- <promise or expected clause, and where the expectation comes from>

## Questions for the employer
- <clarifications, unclear wording, missing promises>

## Questions for a lawyer
- <everything touching law or enforceability — verbatim clause references>
```

Two question lists, never merged: the employer gets clarifications and promise follow-ups; **anything touching law or enforceability goes to the lawyer list** — unanswered. If the stakes feel high (unusual clauses, a non-compete, anything tagged `unclear` that matters), say once that a review by an employment-law specialist (in Germany: *Fachanwalt für Arbeitsrecht*) is a small cost against a bad contract — that is advice to get advice, and it is the only advice the boundary allows.

## Part 2 — Negotiation prep

Only after Part 1 — negotiating a contract you haven't fully read is how promises stay verbal.

- **Position the offer.** Where does it sit against `goals.md` target and floor, and against the fit gate's comp research with its reliability tier (`core/fit_check.md` — reuse it, don't re-research)? State it in one line: "offer X, target Y, market evidence Z (reliability: <tier>)".
- **Anchor claims in the KB.** Level and salary arguments are built like every other claim in this workflow — traced to verified achievements and scope, not adjectives. Pull the strongest 2–3 from the role files; the same traceability discipline applies to what the user says in a negotiation call.
- **Counter on at least one dimension** — salary, bonus, remote days, start date, title, vacation, development budget — anchored with a reason: "based on <market evidence> and my experience with <KB-traced scope>, I was expecting closer to Z." Never accept on the spot; "I'd like a day to review this fully" is always acceptable.
- **Draft, never send.** Reply emails and counter messages are drafted into chat or `offer_prep.md` for the user to send. Everything material ends up in writing before accepting.

## Tracker integration

Per `lifecycle/tracking.md`: status `offer` with `stage_reached` `final` and `date_closed` set — but the row keeps a **dated `next_action`** through review and negotiation ("send questions by <date>", "counter by <date>", "sign-by deadline <date>") until the contract is signed or declined; the outcome lands in `notes`. The debrief still runs: what the negotiation taught goes to `knowledge/lessons.md` as a `process` lesson.

# Cover Letter Rules — the formula and the bans

These rules bind the `application-writer` agent; the `application-verifier` checks against them. Market-specific additions (Anschreiben norms) are in `standards/dach_conventions.md`.

## Hard limits

- **Under 300 words.** Recruiters skim; length is a cost, not a signal of effort.
- **Specific to this company and role.** Every letter references something real about the company (from the Step 4 research notes — a product, a public decision, an initiative). A letter that would work with the company name swapped out is a defect.
- **Language matches the posting** unless the user says otherwise; if applying in a second language, close with a natural note ("Ich führe das Gespräch gerne auf Deutsch weiter." / "Happy to continue the conversation in German.").
- **Fact containment (ADR-0007).** The letter may assert no fact the assembled `cv.md` doesn't — no number, technology, outcome, or credential that isn't in a slot the trim kept. Framing, motivation, and the company angle are free, and the story bank is what they're drawn from; facts are not. This is the letter's half of the quality bar and the main thing the gate judges (`core/tailoring_method.md`).
- **Attribution is part of the fact.** Two contained facts can combine into an uncontained claim: a metric from one bullet attached to another bullet's verb, *built* widened to *owns*, a past role written as present, one project's outcome credited to a different employer. The test is not "does each word appear in the CV" but "does the CV attach it to this". A letter arguing from two adjacent bullets is exactly where this slips — keep each fact with the verb, employer, and tense its own slot gives it.

## Banned openers (automatic rewrite)

- "I am writing to express my interest…"
- "I believe I would be a great fit…"
- "Please find attached…" / "Please find my CV attached for your consideration…"
- "I have always admired your company…"

Open with substance: why this role, concretely, in one sentence.

## The 6-part formula (in order)

1. **Why applying** — one sentence, real and direct, no flattery. *"The role maps closely to what I've been building for the last four years."*
2. **Pitch** — 2–3 sentences: who the person is, what they do, with a concrete example matched to the company's type (B2B SaaS, fintech, agency, public sector…).
3. **Value proposition** — the letter's core: pick the posting's *hardest or most central requirement*, and answer it with direct experience and a concrete result **the CV also carries** — the lead evidence, picked once for both documents. One focused argument, not a CV summary. Name the exact thing — no "transferable skills".
4. **Broader coverage** — 1–2 sentences showing the baseline requirements are met.
5. **Portfolio / work samples** — one line with the link, if applicable, and only a link the assembled CV itself carries. No qualifying asset → skip the part entirely.
6. **Logistics close** — location, work permit status, notice period / availability, languages, invitation to talk. (In DACH applications the permit + notice period are expected here — never omit them; see `standards/dach_conventions.md`.)

## Tone

Match the employer, inferred from the posting and research notes: startup → direct and informal; traditional corporate / public sector → professional and measured, but never stiff. When in doubt, mirror the posting's own register. No exclamation marks doing enthusiasm's job; the concrete example carries it.

## The anti-slop pass — mandatory before the letter is written

A letter that reads as machine-written is a defect: the one document a human reads end to end is the one that must not sound generated. `application-writer` runs this pass over the letter draft **before** writing `cover.md`, so what the gate reads is the final text.

**Preferred tool: the `humanizer` skill**, when the session has it. It is advised, never required (`core/orchestration.md`) — without it, the writer applies the checklist below by hand. Either way the pass **runs**; only the instrument is optional.

**The pass edits prose, never claims.** No fact, metric, date, credential or named tool's spelling may change, and nothing may be added that the assembled CV doesn't hold. A "humanized" letter that gained a fact is a containment BLOCKER, not a style win. The CV is out of scope entirely — it is trimmed verbatim from the exemplar and prose polish cannot touch it.

### Banned patterns (each hit is a MAJOR)

- **Significance inflation** — "stands as a testament to", "plays a pivotal/crucial role", "underscores the importance of", "reflects a broader", "marks a turning point".
- **Promotional adjectives** — passionate, cutting-edge, seamless, robust, innovative, dynamic, world-class, best-in-class, deeply committed.
- **AI vocabulary** — delve, tapestry, landscape, realm, showcase, leverage (as a verb), foster, spearhead, meticulous, navigate (figurative), elevate, resonate.
- **Participle pile-ons** — a trailing "…, ensuring X" / "…, highlighting Y" / "…, leveraging Z" bolted on to fake depth.
- **Negative parallelism** — "It's not just X, it's Y"; "not only … but also".
- **Rule of three** — triads used as a rhythm ("built, scaled, and maintained") more than once in a letter.
- **Vague attribution** — "industry experts", "it is widely recognised", "studies show", with no named source.
- **Filler openers and closers** — "In today's fast-paced world", "I am confident that", "I look forward to the opportunity to contribute to your continued success".

### Voice (each note is a MINOR)

Uniform sentence length, bloodless neutrality, and perfectly balanced paragraphs read as generated even with zero banned patterns. Vary sentence length; let one sentence be short. Keep em dashes to at most one in the whole letter. State a real opinion where the content invites it — never a new fact.

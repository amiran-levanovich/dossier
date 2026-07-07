# Interview Prep — per-stage preparation

Run when an interview gets booked: update the tracker (`lifecycle/tracking.md`), ask which stage, then build `applications/<company>/prep.md` for **that stage specifically**. The knowledge base is the raw material — stories, metrics, and stack details come from `knowledge/`, tailored to what this company will probe (read the application's `jd.md` and `notes.md` first).

## Recruiter / initial screen

- **2-sentence pitch**: who the person is, what they do, why this company — built from the KB summary and the company research notes. Rehearsable, under 30 seconds.
- **Salary answer**: a range, never a point; anchored slightly above the target in `goals.md`. For DACH: annual gross, and have permit/notice-period answers ready — they will be asked (`standards/dach_conventions.md`).
- **Questions to ask**: team structure, what success looks like in 90 days, why the role is open.

## Hiring manager / technical

- Research the interviewer if named (LinkedIn, company page) — shared context, their team's work.
- From `jd.md`, list the 3–5 topics most likely probed; for each, pull the matching KB material: which role file covers it, which story demonstrates it, which metrics to have ready.
- For coding/technical screens: identify the stack and problem domain from the posting; list the specific concepts to refresh. **Flag honestly** anything the CV names that the user is rusty on — better surfaced in prep than discovered live. If the application carries `overrides.md` claims, prep those explicitly: the user chose to make them and must be able to sustain them.

## Behavioural — STAR

Format, per story: **S**ituation (1 sentence), **T**ask (1 sentence — what was needed from *you*), **A**ction (2–3 sentences, first person, specific), **R**esult (metric or concrete outcome). Under 90 seconds spoken; practice cutting, not expanding.

The 5 core stories were harvested at intake (`core/interview_protocol.md` Phase 4): leadership/initiative, conflict, failure and recovery, decision under uncertainty, cross-functional collaboration. Pull them from the role files, adapt the emphasis to this company's values (visible in the posting and research notes).

## Panel / assessment / system design

- Ask in advance: who's in the room, what format (presentation, case, competency grid).
- Presentations: know the audience, lead with the conclusion, anticipate the hardest question.
- Case/system design: state assumptions first; requirements → high-level structure → drill into components; always cover the data model, interfaces/contracts, the scaling bottleneck, and failure modes.

## Offer stage

- Never accept on the spot — "I'd like a day to review this fully" is always acceptable.
- Counter on at least one dimension (salary, bonus, start date, remote days, title, development budget), anchored with a reason, not a preference: "Based on the market rate for X and my experience with Y, I was expecting closer to Z."
- Everything material in writing before accepting.

## After every interview

Debrief while it's fresh: what was asked, what landed, what wobbled. Write durable findings back — a new story or corrected metric into the KB; company-specific signals into `notes.md`; the next stage into the tracker with a dated `next_action`.

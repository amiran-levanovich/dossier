# CV Rules — writing standards for the exemplar

Read together with `standards/ats_rules.md` (machine pass) and, for the German-speaking market, `standards/dach_conventions.md`. The skeleton is `templates/cv_template.md`.

**These rules bind the exemplar build** (`lifecycle/exemplar.md`) — substance, voice, section shape and titles are settled once, there, with the whole story bank in view. Every application inherits that shape by trimming the signed exemplar byte-verbatim, so there is no per-application shape check: the writer selects and orders slots and has no mechanism to reword one (ADR-0005). The rules that still apply at application time are marked **[trim]** below; `application-verifier` checks those and nothing else about the CV.

## Substance

- **Outcomes, not duties.** Every experience bullet states what changed because the person was there — "Reduced deploy time from 40 to 8 minutes", not "Responsible for CI/CD".
- **Metrics wherever the bank has them; honesty where it doesn't.** Use the numbers the interview established. Where the bank has none, a concrete qualifier is fine ("cut manual steps from 7 to 2"); an invented number is never fine.
- **Attribution stays accurate.** The bank records the person's part vs the team's; the exemplar keeps that distinction ("Designed and built X" ≠ "Contributed to X").
- **Everything the bank supports, at the strength it supports.** The exemplar is a superset — every bullet worth ever using belongs in it, because trimming can only remove. A claim left out here cannot reach any CV, so the build is not the place to be modest. The containment check is what holds the strength honest.
- **Each position gets a one-line company descriptor** — type, domain, rough scale ("B2B SaaS for logistics, ~200 people"). Readers rarely know the employer; without it the bullets float context-free. Domain terms (ecommerce, SaaS, fintech, marketplace) are ATS keywords in their own right.

## Voice

- Direct, active, first-person-implied: "Designed X", "Built Y", "Led Z". Never passive ("Was responsible for", "Assisted with").
- No corporate filler: "leveraged", "spearheaded", "results-driven", "passionate team player", "synergies" — cut all of it.
- Bullet length follows impact: a high-impact result may take two lines; routine work gets one or is cut.

## Structure

- **Order:** headline → summary → experience, reverse-chronological → projects → education → skills → languages. For technical/specialist roles a compact skills line may also appear in the headline area; the full skills section stays low — recruiters read experience first.
- **Length [trim]:** the exemplar itself runs long by design. The *assembled* CV is one page under ~7 years of experience, two pages maximum for anyone — the trim is what enforces it, by dropping what adds length but no signal for this posting.
- **Summary variants.** The exemplar may carry more than one summary block — one per role family the candidate targets, each 2–3 lines. The trim keeps the one closest to the posting's framing **[trim]** and drops the rest; it never rewrites one. For a career change, one variant is the bridge: two sentences connecting background to that kind of role.
- **Cut what doesn't serve this application [trim].** Tailoring is selection: lead with the slot answering the posting's hardest requirement, drop the rest.
- No objective statement (a bridging summary variant replaces it), no references, no "References available on request".
- **Links follow the portfolio verdicts.** The exemplar carries a header link or a Projects entry only for an asset the bank marks worth showing, with the posting types it suits. The trim may drop a link, never add one — a link to a stale or weak asset costs more than no link.

## Emphasis by field

| Field                 | Lead with                                                                                     |
| :-------------------- | :-------------------------------------------------------------------------------------------- |
| Software / technical  | Stack (exact names), scale, performance/reliability outcomes, what was designed vs maintained |
| Business / operations | Cost savings, revenue, efficiency gains, team size                                            |
| Marketing             | Campaign results, audience growth, conversion rates, channels owned                           |
| Finance               | Portfolio size, accuracy, compliance, process improvements                                    |
| Sales                 | Revenue closed, quota attainment, deal size                                                   |
| HR / people           | Hiring volume, retention, programmes built                                                    |
| Creative / design     | Portfolio link — it outranks any bullet                                                       |
| Research / academia   | Publications, grants, methods; teaching only if relevant                                      |

## Titles

Use the job title the person actually held, as the bank records it. A headline that borrows the market's phrasing is fine **only when factually safe** — check `constraints.md` at the job-folder root first: protected-title rules (e.g. "Ingenieur" in Germany, see `standards/dach_conventions.md`) and the person's own hard rules override any keyword benefit. This is a build-time decision: the headline is a single slot, and no application can reword it.

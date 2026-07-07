# CV Rules — writing standards for every generated CV

Read together with `standards/ats_rules.md` (machine pass) and, for the German-speaking market, `standards/dach_conventions.md`. The skeleton is `templates/cv_template.md`. These rules bind the `cv-tailor` agent and any manual CV edit; the `application-verifier` checks against them.

## Substance

- **Outcomes, not duties.** Every experience bullet states what changed because the person was there — "Reduced deploy time from 40 to 8 minutes", not "Responsible for CI/CD".
- **Metrics wherever the KB has them; honesty where it doesn't.** Use the verified numbers from the knowledge base. If a KB entry has no number, a concrete qualifier is fine ("cut manual steps from 7 to 2"); an invented number is never fine.
- **Attribution stays accurate.** The KB records the person's part vs the team's; the CV keeps that distinction ("Designed and built X" ≠ "Contributed to X").
- **Every claim traces.** Each bullet maps to a KB entry (or a user-directed override) in the trace file — see `core/tailoring_method.md`.
- **Each position gets a one-line company descriptor** — type, domain, rough scale ("B2B SaaS for logistics, ~200 people"), pulled from the role file's **Context** line. Readers rarely know the employer; without it the bullets float context-free. Emphasize the facet closest to the target company's own type, and note that domain terms (ecommerce, SaaS, fintech, marketplace) are ATS keywords in their own right.

## Voice

- Direct, active, first-person-implied: "Designed X", "Built Y", "Led Z". Never passive ("Was responsible for", "Assisted with").
- No corporate filler: "leveraged", "spearheaded", "results-driven", "passionate team player", "synergies" — cut all of it.
- Bullet length follows impact: a high-impact result may take two lines; routine work gets one or is cut.

## Structure

- **Length:** one page under ~7 years of experience; two pages maximum for anyone.
- **Order:** headline/summary (2–3 lines, tailored to the role's framing) → experience, reverse-chronological → projects (if they earn their space) → education → skills → languages. For technical/specialist roles a compact skills line may also appear near the top; the full skills section stays low — recruiters read experience first.
- **Summary is tailored, not generic.** It mirrors the posting's framing of the role using the candidate's verified strengths. For a stretch or career-change application, it is the bridge — two sentences connecting background to this role.
- **Cut what doesn't serve this application.** Tailoring is selection: reorder bullets so the most relevant experience leads, drop bullets that add length but no signal for *this* posting.
- No objective statement (career-changers get the bridging summary instead), no references, no "References available on request".

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

Use the job title the person actually held (as verified in the KB). Aligning a headline with the posting's phrasing is fine **only when factually safe** — check `knowledge/constraints.md` first: protected-title rules (e.g. "Ingenieur" in Germany, see `standards/dach_conventions.md`) and the person's own hard rules override any keyword benefit.

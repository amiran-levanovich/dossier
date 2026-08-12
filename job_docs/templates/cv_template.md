# CV Template — ATS-safe single-column skeleton

The shape of `master_cv.md`, and therefore of every `cv.md` trimmed from it. It satisfies `standards/ats_rules.md` by construction; section wording/order adapt per `standards/cv_rules.md` and, for German-language documents, `standards/dach_conventions.md` (which may add photo, extended personal data, and signature per the user's recorded choices).

```markdown
# <Full Name>
<Headline — the role identity, constraints-checked; one slot, never reworded per posting>

<City, Country> · <email> · <phone> · <LinkedIn> · <GitHub/portfolio if applicable>

## Summary
<2–3 lines: seniority + core strength + the angle one target role family cares about.
The exemplar may carry several summary blocks — the trim keeps the closest one.
Career-change applications: one variant is the bridge.>

## Experience

### <Title> — <Company>, <City or Remote>
<MM/YYYY> – <MM/YYYY or "present">
*<one-line company descriptor: type + domain + scale — e.g. "B2B SaaS for hotel operations, ~80 people">*

- <outcome bullet: verb + what + metric — every bullet worth ever using>
- <the trim keeps 3–5 for recent/relevant roles, 1–2 for old ones, and drops the rest>

### <Title> — <Company>, <City>
<MM/YYYY> – <MM/YYYY>
*<company descriptor>*

- <...>

## Projects            <!-- the trim keeps only those earning their space for THIS posting -->

### <Project name> — <one-line what/for whom> <link>
- <outcome or scope bullet>

## Education

**<Degree, field>** — <Institution>, <YYYY>
<Certifications: name, issuer, year — exact official names (ATS keywords)>

## Skills
<Grouped lines, exact tool names, most relevant group first:>
**<Group>:** <Tool>, <Tool>, <Tool (depth note if useful)>
**<Group>:** <...>

## Languages
<Language> (<CEFR level or native>) · <Language> (<level>)
```

Rules baked into the shape:

- One column, standard headings, no tables/images/footers — the parser pass.
- Experience before skills (recruiters read experience first); a one-line stack summary may appear in the headline area for technical roles.
- Reverse-chronological, both dates always present, consistent `MM/YYYY`.
- Every position carries its one-line company descriptor (from the role file's
  **Context** line) — recruiters rarely know the employer, and domain terms
  (SaaS, ecommerce, fintech…) double as ATS keywords.
- The header's GitHub/portfolio link and every Projects entry point only at assets
  the bank's portfolio verdicts mark worth showing.
- The parser in `scripts/cv.py` decomposes exactly this shape into slots — `# Name`,
  the headline line, `## Section`, `### <Title> — <Company>`, and the bullets under
  each. An exemplar that departs from it cannot be trimmed.

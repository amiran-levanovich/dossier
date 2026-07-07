# CV Template — ATS-safe single-column skeleton

The default shape for every generated `cv.md`. It satisfies `standards/ats_rules.md` by construction; section wording/order adapt per `standards/cv_rules.md` and, for German-language documents, `standards/dach_conventions.md` (which may add photo, extended personal data, and signature per the user's recorded choices).

```markdown
# <Full Name>
<Headline — the role identity, tailored to the posting's framing, constraints-checked>

<City, Country> · <email> · <phone> · <LinkedIn> · <GitHub/portfolio if applicable>

## Summary
<2–3 lines: seniority + core strength + the specific angle this posting cares about.
Career-change applications: this is the bridge.>

## Experience

### <Title> — <Company>, <City or Remote>
<MM/YYYY> – <MM/YYYY or "present">

- <outcome bullet: verb + what + metric — most relevant to this posting first>
- <3–5 bullets for recent/relevant roles; 1–2 for old or less relevant ones>

### <Title> — <Company>, <City>
<MM/YYYY> – <MM/YYYY>

- <...>

## Projects            <!-- only if they earn their space for THIS posting -->

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
- Every bullet that asserts experience or an outcome has a line in `cv_trace.md`.

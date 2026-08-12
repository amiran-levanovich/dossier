# ATS Rules — surviving the machine pass

Most mid-size and large employers run applications through an Applicant Tracking System before any human reads them. ATS matching is **literal**: it does not infer, translate, or understand analogies. These rules exist because good candidates get filtered out by phrasing, not by substance.

## The exact-keyword rule (the most important rule in this plugin)

Name the exact tool, credential, or phrase the posting uses. **Equivalency language is invisible to the machine:**

| Written on the CV                      | What the ATS finds |
| :------------------------------------- | :----------------- |
| "pytest-equivalent testing discipline" | no pytest          |
| "Alembic-style migrations"             | no Alembic         |
| "experience with similar CRM tools"    | no Salesforce      |
| "familiar with NoSQL patterns"         | no MongoDB         |

**Correct patterns:**

- Genuinely has it, differently deep: name it, contextualize in parentheses — `pytest (RSpec background — same TDD discipline)` → ATS finds pytest ✓
- Currently learning: `Kafka — actively ramping` → visible, honest, no overclaim.
- Doesn't have it: **omit it.** The gap is recorded in `jd.md`'s `## Fit` block and, if the user insists on claiming it, handled as a declared one-off slot (`core/tailoring_method.md`) — never through fuzzy wording.

Use the posting's exact spelling ("PostgreSQL" if they wrote PostgreSQL, "Postgres" if they wrote Postgres). On the CV this is not a writing decision: the exemplar is written in canonical spellings and assembly swaps in the posting's spelling for any **alias group** afterwards, logging every swap (ADR-0008). Recurring domain phrases from the posting ("payment reconciliation", "stakeholder management") belong in the exemplar where they are natural — never stuffed, and never invented at application time.

## The keyword check procedure (before writing anything)

1. Extract from the posting every named: language, framework, library, database, platform, tool, certification, degree requirement, spoken-language requirement — plus recurring domain phrases. Write them into `jd.md` under **ATS keywords**.
2. Cross-check each against the exemplar and the story bank with `scripts/ats_coverage.py` — literal whole-token matching, alias-aware, and singular/plural-aware on the keyword's last word, so a posting's "migrations" finds a bank that says "migration". Names the alias table knows never inflect: "Rails" minus its s is "Rail", which fires on prose. Bucket: **covered** (the exemplar names it) / **promotable** (the bank has it, the exemplar doesn't — promote it into the exemplar or don't claim it) / **real gap** (neither has it).
3. Only then gate and draft. The report is what the fit gate's coverage dimension cites (`core/fit_check.md`) and what the writer works from; it costs no LLM call, so it runs first.

## Format constraints (the parser pass)

- **Single column.** Multi-column layouts scramble in many parsers.
- **Standard section headings** — "Experience", "Education", "Skills" (or the posting language's standard equivalents). Clever headings ("My journey") break section detection.
- **No tables, no text in images, no headers/footers carrying real content** (some parsers drop them entirely), no icon fonts for contact info.
- **Standard fonts, real text.** If rendering to PDF, the text layer must be selectable — never a scanned or image-based PDF.
- Dates in a consistent, parseable format (`MM/YYYY – MM/YYYY`); every position has both dates.
- File naming when rendering: `CV_<Name>_<Company>.pdf` — some portals index the filename.

Markdown output (the default — see `standards/rendering.md`) trivially satisfies all of this; the constraints bind hardest when the user requests a designed/rendered format. A two-column designed CV is a deliberate, user-chosen trade-off for markets that expect it — see `standards/dach_conventions.md`.

## Honesty note

ATS optimization here means *making true things machine-visible* — never adding untrue things. The boundary is the superset invariant: a keyword reaches a CV only because the signed exemplar already carries it, or because the candidate promoted it there deliberately. A `GAP` keyword is recorded, never written in.

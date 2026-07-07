# ATS Rules — surviving the machine pass

Most mid-size and large employers run applications through an Applicant Tracking System before any human reads them. ATS matching is **literal**: it does not infer, translate, or understand analogies. These rules exist because good candidates get filtered out by phrasing, not by substance.

## The exact-keyword rule (the most important rule in this plugin)

Name the exact tool, credential, or phrase the posting uses. **Equivalency language is invisible to the machine:**

| Written on the CV | What the ATS finds |
| :--- | :--- |
| "pytest-equivalent testing discipline" | no pytest |
| "Alembic-style migrations" | no Alembic |
| "experience with similar CRM tools" | no Salesforce |
| "familiar with NoSQL patterns" | no MongoDB |

**Correct patterns:**

- Genuinely has it, differently deep: name it, contextualize in parentheses — `pytest (RSpec background — same TDD discipline)` → ATS finds pytest ✓
- Currently learning: `Kafka — actively ramping` → visible, honest, no overclaim.
- Doesn't have it: **omit it.** The gap is handled in `jd.md` Fit notes and, if the user insists, through the override protocol (`core/tailoring_method.md`) — never through fuzzy wording.

Use the posting's exact spelling ("PostgreSQL" if they wrote PostgreSQL, "Postgres" if they wrote Postgres); mirror recurring phrases from the posting where they're natural ("payment reconciliation", "stakeholder management") — naturally, not stuffed.

## The keyword check procedure (before writing anything)

1. Extract from the posting every named: language, framework, library, database, platform, tool, certification, degree requirement, spoken-language requirement — plus recurring domain phrases. Write them into `jd.md` under **ATS keywords**.
2. Cross-check each against the knowledge base (verified entries only). Bucket: **covered** / **verifiable gap** (user has it, KB doesn't record it yet — mini-interview it into the KB now) / **real gap**.
3. Only then draft. The `application-verifier` re-runs this check on the finished documents.

## Format constraints (the parser pass)

- **Single column.** Multi-column layouts scramble in many parsers.
- **Standard section headings** — "Experience", "Education", "Skills" (or the posting language's standard equivalents). Clever headings ("My journey") break section detection.
- **No tables, no text in images, no headers/footers carrying real content** (some parsers drop them entirely), no icon fonts for contact info.
- **Standard fonts, real text.** If rendering to PDF, the text layer must be selectable — never a scanned or image-based PDF.
- Dates in a consistent, parseable format (`MM/YYYY – MM/YYYY`); every position has both dates.
- File naming when rendering: `CV_<Name>_<Company>.pdf` — some portals index the filename.

Markdown output (the default — see `standards/rendering.md`) trivially satisfies all of this; the constraints bind hardest when the user requests a designed/rendered format. A two-column designed CV is a deliberate, user-chosen trade-off for markets that expect it — see `standards/dach_conventions.md`.

## Honesty note

ATS optimization here means *making true things machine-visible* — never adding untrue things. The boundary is the traceability contract: every keyword added must trace to a verified KB entry or an explicit user-directed override.

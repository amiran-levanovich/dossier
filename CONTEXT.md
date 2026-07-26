# Dossier

A self-hosting Claude Code plugin that runs a job search: build a verified knowledge base about the candidate, then produce per-posting application packages whose every claim traces back to it. The glossary below is the vocabulary the docs, skills, and agents must all use; general software terms don't belong here.

## The knowledge layer

**Knowledge base**:
The candidate's verified facts, in the user's own job folder under `knowledge/`. The plugin ships none of it.
_Avoid_: profile, corpus, candidate data

**Verified entry**:
A knowledge-base claim the intake interview confirmed. Only verified entries may feed a document; anything still marked `[unverified]` is invisible to the writer.
_Avoid_: confirmed fact, validated claim

**Override**:
A claim the user explicitly directed into one application that the knowledge base can't back. Recorded in that application's `overrides.md`, never in `knowledge/`.
_Avoid_: exception, manual claim

## The production layer

**Application package**:
The four files one posting produces — `cv.md`, `cv_trace.md`, `cover.md`, `cover_trace.md`. The unit the writer writes and the verifier passes or fails.
_Avoid_: application, documents, deliverables

**Trace file**:
The sidecar mapping every claim-bearing line in a document to one canonical knowledge-base file and anchor. A claim without one is a defect.
_Avoid_: source map, citations, provenance file

**Exemplar**:
A document built once, verified at full rigor, and reused across applications — `master_cv.md` and nothing else. The cover letter has no exemplar (ADR-0001).
_Avoid_: master document, template, boilerplate

**Anti-slop pass**:
The mandatory prose pass over the letter draft, before `cover.md` and its trace are written. Uses the `humanizer` skill when the session has it, the checklist in `standards/cover_letter_rules.md` when it doesn't. The pass never skips; only its instrument is optional.
_Avoid_: humanizing, polish, style pass

**Lead evidence**:
The single verified achievement answering the posting's hardest requirement. The CV surfaces it first and the letter's value proposition argues from it — one choice, made once, binding both documents.
_Avoid_: main selling point, key achievement

**The gate**:
`application-verifier`. It returns CLEAN or severity-ordered findings and never edits. Nothing reaches the user on a round with open BLOCKER or MAJOR findings.
_Avoid_: review step, QA, checker

**Round cap**:
Three verifier rounds per application. Findings still open at the cap have a structural cause — a knowledge-base gap, a claim needing an override, a standards conflict — so the loop stops and the findings go to the user rather than into a fourth round.
_Avoid_: retry limit, max attempts

## The maintenance layer

**Advised skill**:
A third-party or Anthropic skill that raises quality for one role but is never required. The plugin assumes nothing is installed and never blocks on absence.
_Avoid_: dependency, required skill, integration

**Budget row**:
A line in `TOKEN_ECONOMY.md` §5 capping a per-run doc's token count, parsed and enforced by `scripts/release_audit.py`. A file may exceed its row only with an `audit-ok: C7` marker stating why.
_Avoid_: token limit, quota

**Cover frame** — *retired*:
The removed cover-letter exemplar (`cover_frame.md`). Do not reintroduce the concept or the term; see ADR-0001.

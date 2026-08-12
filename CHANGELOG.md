# Changelog

Notable changes per release. Format follows [Keep a Changelog](https://keepachangelog.com);
versioning is [semantic](https://semver.org) — a major bump means the method changed shape,
not that the code broke.

Releases are tagged `v<version>` and published on GitHub. Consumers update with:

```
/plugin marketplace update dossier
/plugin update dossier@dossier
```

## [Unreleased]

Everything here came out of the first three live runs of the v4 pipeline — the method had
never been executed end to end before 2026-08-12, and every entry below is a defect or a gap
that running it exposed.

### Added
- `HOW_IT_WORKS.md` — the full flow in plain language, as a companion to the README.
- `## Availability` as an exemplar section, so the letter's logistics close can state work
  permit and notice period without breaking fact containment. Under DACH the close is not
  optional, which made this a structural contradiction before.
- Per-dispatch and per-repair cost reporting in `session_metrics.py`, read out of the Agent
  tool result and the task notifications. This closed ADR-0003's open commitment to measure
  the edit-plan saving: **192,878 tokens under v3 against 80,841 under v4**, −58%.
- A Tier-2 golden case for the one-off slot path, with a test that removing the declaration
  must fail the case.
- `cv.py map` now names any section it skipped, instead of silently dropping exemplar content
  that could then never reach a CV.

### Changed
- The gate has a third finding class, **merged attribution**: facts each present in the CV,
  joined into a claim it does not make. Its repair is a split rather than a removal, and the
  single-round property survives because the split may only redistribute facts kept slots
  already carry.
- Paraphrase drift now has one mechanical test — put the CV's words back into the letter's
  sentence and see whether the meaning narrows — after the same sentence got two different
  verdicts in two runs. Verb, scope noun, employer and tense must survive the swap.
- `eval_score.py` can score a live application folder where it lies, resolving the exemplar
  upward, and can score a run with no golden case of its own: self-checking signals gate,
  reference-dependent ones read `n/a` instead of failing against another application's bands.
- Keyword coverage is singular/plural aware, so a posting's "migrations" finds a bank that
  says "migration" — a false `GAP` costs a promotion the candidate would have wanted.
- The writer reports what its self-check caught before writing, so the open question of
  whether that instruction pays for itself can be answered from evidence rather than faith.

### Fixed
- A one-letter keyword (`R`, `C`) no longer matches a candidate's initial. `R` was reported
  `COVERED` against a CV headed "R. Vogel" — a false `COVERED` inflates the fit score and
  tells the writer a keyword is available that no slot supports.

## [4.0.0] — 2026-08-12

**Trim from a once-verified exemplar; retire the knowledge base.**

Rigor is paid once, on one document, and inherited by every application after it.

### Added
- **Story bank** (`story_bank.md`) — the candidate's career in free-form prose. No schema, no
  index, no heading anchors (ADR-0006).
- **The exemplar** (`master_cv.md`) — one superset CV holding every claim any application may
  ever make, machine-checked for containment against the bank and then **signed off by the
  candidate**, blocking (ADR-0004).
- **`cv.py`** — `map` decomposes the exemplar into slots, `build` renders an edit plan
  byte-verbatim and proves it, writing nothing on any fault (ADR-0005).
- **Alias groups** (`aliases.py` + a shipped table) — the posting's spelling swapped in after
  the verbatim proof, every swap logged (ADR-0008).
- **Three-way ATS coverage** — `COVERED` / `PROMOTABLE` / `GAP`, so "I have this but it isn't
  on my CV" stops looking like "I don't have this".
- **One-off slots** — content the candidate directs into a single application, always a new
  slot, judged at full rigor by the gate.
- **Migration** (`lifecycle/migration.md`) — a v3 folder converted rather than re-interviewed,
  including a superset sweep, because a v3 exemplar was never required to be complete.

### Changed
- **Two LLM dispatches per application** (writer, verifier) instead of up to five; everything
  between them is deterministic script.
- The verifier runs **one round** and judges only what the inherited verdict does not cover:
  the letter's fact containment and any one-off slot.
- CV rules bind the **exemplar build**; per-application shape checking is gone.
- Cover-letter rules carry **fact containment** in place of the trace contract.

### Removed
- The schema'd `knowledge/` directory, `INDEX.md`, per-claim heading anchors, and the
  `[unverified]` marker.
- Trace files and trace resolution, the claim ledger, the standalone master diff, and the
  slot module they served (`trace_check.py`, `claim_ledger.py`, `master_diff.py`,
  `master_slots.py`).
- The per-application override protocol — replaced by the one-off slot.
- The three-round verifier loop.

## [3.2.1] — 2026-07-27
Refuse an exemplar the slot parser cannot read, rather than silently producing an empty map.

## [3.2.0] — 2026-07-27
The CV assembles from an **edit plan** against a slot map, so the writer stops retyping lines
it did not change (ADR-0003).

## [3.1.0] — 2026-07-26
A cap on verifier rounds.

## [3.0.0] — 2026-07-26
One writer for both documents, the cover-letter exemplar removed (ADR-0001), and the anti-slop
pass made mandatory.

## [2.7.0] – [2.7.2] — 2026-07-23
Doc budgets counted in **tokens** rather than words; the C7 check fails loudly rather than
skipping, and its `audit-ok` opt-out is a comment with a stated reason.

## [2.6.0] — 2026-07-23
Enforced release gates and the eval harness.

## [2.5.0] – [2.5.1] — 2026-07-18/19
Exemplar documents, and read discipline for the writer working from one.

## [2.3.0] – [2.4.0] — 2026-07-18
The deterministic pipeline scripts, and the verifier's first cost levers.

## [2.0.0] — 2026-07-16
`job-workflow` extracted from `claude_setup` into this standalone repo as **dossier**. Earlier
`v1.x` tags were migrated from `job-workflow-v1.x` and cover the pre-split history
(2026-07-07 onward).

[Unreleased]: https://github.com/amiran-levanovich/dossier/compare/v4.0.0...HEAD
[4.0.0]: https://github.com/amiran-levanovich/dossier/releases/tag/v4.0.0
[3.2.1]: https://github.com/amiran-levanovich/dossier/releases/tag/v3.2.1
[3.2.0]: https://github.com/amiran-levanovich/dossier/releases/tag/v3.2.0
[3.1.0]: https://github.com/amiran-levanovich/dossier/releases/tag/v3.1.0
[3.0.0]: https://github.com/amiran-levanovich/dossier/releases/tag/v3.0.0
[2.7.2]: https://github.com/amiran-levanovich/dossier/releases/tag/v2.7.2
[2.7.0]: https://github.com/amiran-levanovich/dossier/releases/tag/v2.7.0
[2.6.0]: https://github.com/amiran-levanovich/dossier/releases/tag/v2.6.0
[2.5.1]: https://github.com/amiran-levanovich/dossier/releases/tag/v2.5.1
[2.5.0]: https://github.com/amiran-levanovich/dossier/releases/tag/v2.5.0
[2.4.0]: https://github.com/amiran-levanovich/dossier/releases/tag/v2.4.0
[2.3.0]: https://github.com/amiran-levanovich/dossier/releases/tag/v2.3.0
[2.0.0]: https://github.com/amiran-levanovich/dossier/releases/tag/v2.0.0

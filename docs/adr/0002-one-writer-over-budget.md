# One writer agent, deliberately over the per-agent token budget

`cv-tailor` and `cover-letter-writer` were merged into a single `application-writer` in v3.0.0. They read the same `jd.md`, the same `overrides.md`, and an overlapping KB slice — twice — and nothing in the pipeline compared their outputs, so a CV leading with one achievement while the letter argued from another surfaced only as a verifier finding, costing a whole fix→re-verify round. One agent reads those inputs once and picks the lead evidence once, which makes the contradiction impossible rather than merely detectable.

The merged file is **2,350 tokens against a 1,640 per-agent budget row**, and carries an `audit-ok: C7` marker rather than being compressed to fit. The row in `TOKEN_ECONOMY.md` §5 was calibrated to the fullest file under it (`application-verifier.md`, 99.7% full) and measures one file at a time, so it cannot see that 2,350 in one agent replaces 3,097 across two. Adding a per-file row would not have helped: `release_audit.check_doc_weights` expands every glob independently, so the file would still be measured against the 1,640 row and still fail.

## Consequences

The two documents are no longer written in parallel, so the writing stage's wall-clock is roughly the sum of the old two rather than the max — accepted, because the parallel dispatch bought latency, not tokens. A writer failure now takes out the whole package instead of half of it. `application-verifier` gained a cross-document consistency clause so a divergence is still caught if one ever appears, and the exception here is the only `audit-ok: C7` marker on an agent file — a second one should be argued on its own merits, not by pointing at this one.

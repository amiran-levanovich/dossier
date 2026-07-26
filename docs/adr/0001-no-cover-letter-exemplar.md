# No exemplar for the cover letter

The master-CV pattern — build one superset document, verify it once, then subtract from it per application — was mirrored for cover letters as a `cover_frame.md`: a 6-part skeleton with the stable parts pre-written and slots for the two generated paragraphs. It produced bad letters. In v3.0.0 the frame and its trace, ledger record, and frame-mode writer path were removed; `master_cv.md` was kept unchanged.

The two documents are not symmetric. A CV is a superset you subtract from, so a verbatim line stays as true for the tenth company as the first. A letter's *stable* parts are precisely the parts that make it swappable between companies — the defect `job_docs/standards/cover_letter_rules.md` exists to prevent. The frame was buying a verbatim-shortcut discount on exactly the phrasing that should never be reused, and the anti-slop pass introduced in the same release (ADR-0002's sibling change) would rewrite reused framing anyway.

## Consequences

Every letter is generated fresh, so no letter claim ever comes back PRE-VERIFIED from a `--document` hash; the ledger still memoizes per-claim across applications, which covers the repeated content. `scripts/claim_ledger.py --document` and `scripts/master_diff.py` now serve the master CV alone. Anyone reading `lifecycle/master_documents.md` and wondering why the letter has no equivalent should read this file rather than build one.

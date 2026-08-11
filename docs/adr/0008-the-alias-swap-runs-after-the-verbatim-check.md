# The alias swap runs after the verbatim check, not inside the slot model

Pure trim (ADR-0005) means a posting spelling a technology differently from the exemplar — "Postgres" against "PostgreSQL", "RoR" against "Ruby on Rails" — gets whatever the exemplar says, which costs real ATS keyword matches for no substantive reason. Alias groups fix that: a plugin-shipped, user-extendable table of interchangeable surface spellings, applied deterministically when the posting uses a different member of the group.

Where the swap happens matters more than that it happens. Slot ids are a hash of the slot's own text (ADR-0003), so rewriting a word inside a slot changes its id, which means the assembled CV is no longer byte-verbatim from the exemplar and `master_diff.py`'s self-test fails. Aliasing and the verbatim guarantee collide unless they are ordered. So they are: assemble pure-trim, run the verbatim self-test — which must come back 100%, proving the trim was clean — and *then* apply the alias pass as a final deterministic rewrite, logging every swap. The guarantee is stated against the pre-alias artifact and the log is the audit trail for everything after it.

The trigger rule stays judgment-free, as `scripts/` requires: the posting contains variant X, the slot contains variant Y, X and Y are in the same alias group, so emit X. Pure string matching, no model call.

## Considered options

**Canonical-plus-variants stored in the exemplar**, with slot ids hashing only the canonical form, is more elegant — one artifact, no post-pass, no divergence between what was checked and what is sent. Rejected because the slot parser and the hash function would both have to know about alias groups, putting vocabulary knowledge inside a layer whose whole discipline is that it makes no judgments about content.

**Both spellings inline in the exemplar** — "PostgreSQL (Postgres)" — needs no machinery at all, and was rejected because it reads badly on a human-facing document and ATS parsers handle the parenthetical inconsistently, which defeats the purpose.

## Consequences

**The delivered `cv.md` is not byte-identical to the exemplar's text once aliases fire**, so anyone re-running `master_diff.py` on a *delivered* CV may see differences. The verbatim claim applies to the assembly output before the alias pass; the swap log is what reconciles the two, and any tooling that checks verbatimness must run at the right point in the order.

**The alias table is generic technology vocabulary, so it ships with the plugin** without violating the no-personal-data rule. Users extend it in their own job folder, and the two merge at read time.

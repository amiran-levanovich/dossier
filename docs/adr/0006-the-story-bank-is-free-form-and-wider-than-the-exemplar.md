# The story bank is free-form, and wider than the exemplar by design

v3.x stored candidate facts in `knowledge/` under the schema in `core/kb_schema.md`: one file per role, an `INDEX.md`, and heading anchors every trace line had to resolve against. v4.0.0 replaces it with a single free-form story bank — ordinary prose about the candidate's career, with no schema, no index, and no anchors. The exemplar is built from it once.

The schema existed to serve the trace contract. A trace line is `claim → file#anchor`, so knowledge had to be chopped into anchorable units whether or not that was the natural shape of a career. With traces retired (ADR-0004) the schema has no consumer left, and its remaining effect would be to make the intake interview fight the material: the useful thing about a story is its context, and the schema's job was to strip context into addressable fragments.

The bank and the exemplar are **peers with an asymmetry**, not source and derivative. The bank is the wider fact set; the exemplar is the subset cleared for documents. A fact in the bank but not the exemplar is not a defect — it is simply not on the CV, which is a decision, not a drift. This is what removes the rebuild-trigger machinery that `lifecycle/master_documents.md` carried in v3.x: there is no sync obligation because the two were never supposed to match.

## Considered options

**Deriving the exemplar from the bank** would give a clean regeneration story, and was rejected because it reintroduces exactly the two-artifact sync problem this release exists to remove — "the source grew, should the master?" is v3.x's rebuild section restated. Regeneration is available anyway by rerunning the terminal build pass; what is rejected is the *obligation* that the exemplar track the bank.

**Forbidding facts in the bank**, so that all hard numbers live only in the exemplar and the two are disjoint, was briefly attractive because it makes drift unrepresentable. Rejected: `interview-briefer` reads the bank, and an interview story stripped of its numbers is useless for the one consumer that needs them most.

## Consequences

**The exemplar will lag the bank, and that is correct.** Everything the candidate has done is in the bank; what is on the exemplar is what they decided was worth a CV slot. The ATS coverage step makes the lag visible exactly when it matters, by checking a posting's keywords against the bank as well as the exemplar — a keyword present in the bank but absent from the exemplar is a promotion candidate, not a gap.

**Interview prep may use bank facts freely, documents may not.** The user speaks for themselves in an interview and no ATS parses them there; a CV and a letter are artifacts that outlive the conversation. The asymmetry is intentional and should not be "fixed" by widening what documents may draw on.

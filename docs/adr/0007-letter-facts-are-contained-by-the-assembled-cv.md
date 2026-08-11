# The letter's facts are contained by the assembled CV, not by the exemplar

The CV is safe by construction in v4.0.0 — byte-verbatim from a verified exemplar, mechanically checked. The letter is not: it is generated prose, written fresh for every company (ADR-0001), drawn from a free-form bank with no anchors (ADR-0006). It is the one place the system can lie. The rule that holds it: **the letter may assert no fact the assembled `cv.md` doesn't.** Numbers, technologies, outcomes, credentials, scope, and dates must already be on the CV going out; the letter re-argues them and never adds. Motivation, framing, and the company angle are unconstrained, because they are not falsifiable claims about the candidate's record.

The reference point is deliberately the assembled `cv.md` and **not** the exemplar. Under pure trim the two are equivalent, since `cv.md ⊆ master_cv.md`. They diverge only when a one-off slot exists (ADR-0005) — and there, checking against the exemplar would either reject a letter that correctly cites the one-off, or force the check to consider two sources and dilute what it guarantees. Anchoring on the artifact actually being sent keeps the rule single-source in every case, including the ones that do not exist yet.

## Consequences

**One verifier round replaces three.** The check needs only the letter and the CV, both small, both in one context. There is no trace file to parse, no anchors to resolve, and no ledger to consult, so the round-cap escalation that v3.x needed — where findings surviving three rounds signalled a structural cause — has nothing left to escalate. A finding here is either a fact the letter invented, which the writer removes, or a fact worth promoting, which is the user's call.

**The exemplar must carry numbers even for bullets rarely surfaced**, because a letter cannot reach past the CV for evidence. This costs nothing: the exemplar is a superset already, and the constraint simply means the superset must be complete in *detail*, not only in coverage.

**A genuinely good letter sometimes wants a story the CV has no room for.** Under this rule the story may still be told — it is the hard numbers inside it that must already be on the CV. If they aren't, that is a promotion, not an exception.

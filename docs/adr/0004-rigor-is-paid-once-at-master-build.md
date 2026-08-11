# Full rigor is paid once, at master build, never per application

Through v3.x every application re-earned its own trustworthiness: the writer read a selection of `knowledge/` files, wrote a CV and a letter plus a trace file each, and `application-verifier` adjudicated every claim against those traces across up to three rounds. The claim ledger and `master_diff.py` existed to stop the *same* claim being re-judged, which is an admission that the per-application judgment was mostly redundant work. In v4.0.0 the redundancy is removed at the source: the exemplar is verified once, at build, and everything downstream inherits that verdict.

The verification the exemplar gets is not weaker for being singular — it is the strongest in the system's history. `application-verifier` receives the whole story bank and the whole exemplar in context and checks that every exemplar claim is contained by the bank, and the build then **blocks on the user reading it**. Those catch different failures. The machine catches the model inventing or inflating during a pass the user did not write; the user catches the claim that is technically supported but that they would not want to defend in a room, which no machine can assess. Both are cheap because both happen once per job search rather than once per posting.

## Considered options

**Keeping a reduced per-application check** was the obvious middle path and was rejected because it preserves the machinery whose *existence* is the cost. Trace files, `trace_check.py`, `claim_ledger.py`, anchor discipline in every knowledge file, and the round-cap loop are not expensive because they run — they are expensive because every doc, skill, and agent in the repo has to describe them. Twenty-seven files referenced `knowledge/` or traces at the time of this decision. A check that fires rarely still costs its full description.

**Response rate as the acceptance signal** was rejected as unmeasurable at this volume: twelve applications is far too noisy a baseline, and by the time N is large enough to read, months have passed. The stated kill condition is instead behavioural and early — if three of the first five v4 applications are hand-edited before sending, the design's core bet is wrong and this should be reverted rather than patched.

## Consequences

**Applications go out without per-claim verification, and that is the intended shape, not an oversight.** A reader who finds this surprising should note what makes it safe: the CV is byte-verbatim from the verified exemplar (ADR-0005), and the letter is fact-contained by that CV (ADR-0007). Nothing unverified can reach a document except a one-off slot, which the user asked for by name and which pays full judgment.

**The exemplar's quality is now a single point of failure for the whole job search.** This is the trade. It is mitigated by the build being blocking, unhurried, and outside any application deadline — which is the opposite of v3.x, where the highest-stakes judgment happened under time pressure, per posting, in a subagent the user never read.

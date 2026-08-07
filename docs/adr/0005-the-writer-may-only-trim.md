# The writer may only trim — it may not reword a slot

ADR-0003 gave the writer four operations against the slot map: keep, drop, patch, and new. In v4.0.0 patch is removed and new is restricted to user-initiated one-off slots. The writer's entire authority over the CV becomes selection and ordering, so every line of every `cv.md` is byte-verbatim from a verified exemplar.

The reason is that patch is what keeps the whole verification apparatus alive. A reworded line is new text, new text is an unverified claim, an unverified claim needs a trace and a judge — and because the writer decides *at its own discretion* when to reword, that machinery has to be present and described for every application even when no application uses it. Forbidding patch is what makes the CV path structurally safe rather than merely checked, and it is what lets `master_diff.py` stop being a discovery step and become a self-test that must come back 100% verbatim.

The bet underneath: if patching is rare, forbidding it costs almost nothing; if patching is common, that is evidence the **exemplar** is wrong, and the fix belongs in the exemplar via promotion, where it is made once and helps every future application, rather than per posting, where it is made under deadline and thrown away.

## Considered options

**Patch allowed but gated** — reword freely, and any non-verbatim line wakes the verifier — was the natural incremental option and is essentially v3.x with `knowledge/` removed. Rejected: it retains trace files, the ledger, and the multi-round loop for a case that should be rare, which is precisely the complexity this release exists to delete.

**One-off slots as patches of existing slots** was rejected in favour of new-slot-only. A patched slot would carry different text under the same slot id across applications, which makes the id lie about its content and voids `master_diff.py`'s self-test. Dropping the ill-fitting slot and adding a one-off beside it expresses the same intent while staying visible in the plan.

## Consequences

**No bullet is ever phrased for the posting.** This is a real tailoring loss, taken deliberately. The narrow escape valve is `alias groups` (ADR-0008), which match the posting's surface spelling of a technology without touching the claim; anything beyond spelling requires promotion or a one-off.

**A one-off slot is user-initiated only.** The writer may never conclude on its own that a slot is needed — it may only report the gap. Without this rule the writer's discretion returns by the back door and the per-application cost profile reverts to v3.x.

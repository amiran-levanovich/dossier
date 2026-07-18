# Token Economy — identifying, fixing, and preventing runtime cost issues

Maintenance doc for the `dossier` repo. The plugin's recurring failure mode is not wrong
output — it is **correct output that costs too much**: an application cycle that eats
10–15% of a 5-hour usage budget, a verifier that runs 5 minutes and 60k tokens. This doc
is the plan for finding those issues, fixing them, and not reintroducing them.

**Why this is critical:** the plugin's whole value proposition is "apply to more jobs,
better." A pipeline that burns the usage budget in 6–8 applications per window defeats
that purpose exactly the way a slow fit gate defeats the fit gate.

---

## 1. The failure taxonomy

Every cost incident so far falls into one of these classes. Diagnose new incidents
against this list first — most "slow run" reports are one of these wearing a new hat.

| # | Class | Mechanism | Smell |
|---|-------|-----------|-------|
| C1 | **Model-tier leak** | An agent runs on `inherit` or a frontier model for mechanical work (templated writing, checklist verification) | `model: inherit` in any agent frontmatter; budget drains fast even on short runs |
| C2 | **Per-item read loops** | A discipline like "check every X against its source" implemented as one Read/Grep *per item*, re-reading the same few files dozens of times; context grows with every round-trip, so cost compounds | An agent's transcript shows the same file path in many tool calls; runtime scales with list length, not file count |
| C3 | **Web content bloat** | WebFetch of a job posting pulls 10–30k tokens of nav/footer/HTML noise; WebSearch budgets unstated or generous by default | Long orchestrator turns before any writing starts; searches answering questions the JD/KB already answered |
| C4 | **Respawn instead of continue** | Fix/re-verify rounds launch fresh agents that re-read all inputs cold instead of continuing (SendMessage) an agent that already holds them | Each verify round costs as much as the first |
| C5 | **Over-broad context passing** | Whole directories or irrelevant standards passed to agents (whole KB instead of the INDEX selection; `dach_conventions.md` outside DACH) | Agent input lists longer than the task needs; "just in case" files |
| C6 | **Loop multipliers** | The verify→fix→re-verify loop multiplies every other class: a C2 verifier in a 3-round loop is 3× the damage | More than 2 verify rounds as the norm, not the exception |
| C7 | **Doc weight creep** | Skill/agent definitions and standards docs are read on *every* run — every added word is a per-application tax, forever | Doc word counts drifting up release over release |

## 2. Measurement — how to identify issues (before guessing)

Token counts per sub-agent aren't directly exposed, so use these proxies. They are
cheap, observable, and correlate tightly with burn. `scripts/session_metrics.py
<session.jsonl>` computes most of them from a transcript in one call — tool-call counts
(main vs subagent), WebFetch/WebSearch counts, subagent spawns, and the real per-turn
`usage` token totals when the transcript records them. Point it at a real job-apply
session to capture the baseline this doc keeps asking for.

1. **Tool-call count per agent.** The primary proxy. Count the calls in the transcript
   (`session_metrics.py` does this). Past ~20 calls for any dossier agent, something is
   wrong (usually C2).
2. **Verify rounds per application.** Read off the session. Target: 1–2. Three or more
   means either writers are under-instructed or the verifier is flagging style noise.
3. **Wall-clock per stage.** Capture→gate→research→writers→verify. Any single stage
   over ~2 minutes is an anomaly worth a transcript look.
4. **WebSearch/WebFetch count per application.** Target: ≤ 2 gate searches (5-cap only
   when uncertain), 0 new Step-4 searches by default, ≤ 1 WebFetch.
5. **Doc weight sweep** (repo-side, at release time):
   `find . -name "*.md" -not -path "./.git/*" | xargs wc -w | sort -rn`
   against the budget table in §5.

**When the user reports a slow/expensive run:** get the numbers above from that session
first, map to a taxonomy class, and only then edit docs. The v2.2.0 verifier fix was
found exactly this way — "5 minutes, 60k tokens" → tool-call count → C2.

**Runaway tripwire (runtime):** any dossier agent past ~2 minutes or ~20 tool calls
gets interrupted, not waited out — diagnose from its partial transcript, fix the agent
definition, relaunch. A runaway never gets cheaper by finishing.

**Prompt-cache TTL:** the API prompt cache expires after ~5 idle minutes. A verify/fix
loop that stalls (typically on a user question) pays a full context re-write when it
resumes — observed as a single 69k-token cache_write turn mid-loop in the v2.2 baseline.
Keep loops moving; batch questions to the user at the loop's start or end, not inside it.

## 3. Budgets — the targets that define "too long / too much"

An issue exists when a number is exceeded; without numbers, "too slow" is a mood.

| Metric | Target | Hard ceiling |
|---|---|---|
| Full application cycle (capture → present) | ≤ 4 min | 7 min |
| Budget share per application (5h window) | ≤ 5% | 8% |
| Writer agent, first pass | ≤ 10 tool calls | 15 |
| Verifier, first pass | 10–15 tool calls | 20 |
| Verifier/writer continuation round | ≤ 5 tool calls | 8 |
| Verify rounds per application | 1–2 | 3 |
| Fit-gate WebSearch queries | 2 default | 5 (uncertain postings only) |
| Step-4 (company research) new queries | 0 default | 2 |
| WebFetch per application | ≤ 1 | 2 |

Revisit ceilings when the pipeline changes shape; a ceiling nobody has hit in months is
stale, a ceiling hit every run is a design defect being tolerated.

## 4. Design rules — how new/edited components stay cheap

Apply this checklist to **every** PR that touches an agent, skill, or core doc. Each
rule kills one taxonomy class at the design stage:

- [ ] **Explicit model per agent** — frontmatter sets the *cheapest model that survives
      the verifier gate*; `model: inherit` is banned. Quality is held by the gate and
      the traceability contract, never by writer model tier. (C1)
- [ ] **Batch reads, never per-item lookups** — any "check every X" instruction must
      say: read each input file once, in one parallel batch, then verify in-context.
      Include a tool-call budget *inside the agent definition* with a self-correction
      line ("if you re-read a file you already hold, you are off the rails"). (C2)
- [ ] **Numeric budget on every research step** — no WebSearch/WebFetch instruction
      ships without a default count and a cap; findings are written down once
      (`jd.md`, `notes.md`) and never re-fetched. (C3)
- [ ] **Continue, don't respawn** — every loop instruction names SendMessage
      continuation as the default and respawn as the exception (continuation failed, or
      the input selection changed). (C4)
- [ ] **Targeted context only** — agents receive a selected file list (via
      `knowledge/INDEX.md`), never a directory; conditional standards
      (`dach_conventions.md`) are passed only when their condition holds. (C5)
- [ ] **Writers pre-empt the loop** — writer instructions encode the verifier's
      cheapest-to-avoid findings (exact keyword spelling, no equivalency language,
      trace every claim) so round 1 is usually CLEAN. (C6)
- [ ] **Word budget respected** — the edit keeps the doc inside its §5 budget; if new
      substance needs room, cut old substance or split the doc so runs load less. (C7)

## 5. Doc weight budgets

These files are loaded on every application run (directly or by an agent). Keep them at
or under budget; check with the sweep command in §2.5 before each release.

| File | Budget (words) |
|---|---|
| `.claude/skills/*/SKILL.md` (each — thin routers) | 500 |
| `.claude/agents/*.md` (each) | 800 |
| `job_docs/core/tailoring_method.md` | 1,400 |
| `job_docs/core/fit_check.md` | 1,400 |
| `job_docs/standards/*` (each) | 1,300 |
| `job_docs/core/quickref.md` (the compaction floor) | 450 |

Docs read only occasionally (`lifecycle/*`, `interview_protocol.md`, README) are not
per-run taxes and get no hard budget — but the same restraint applies.

## 6. Release audit — recurring, before every version bump

1. `grep -rn "model: inherit" .claude/agents/` → must be empty. (C1)
2. Grep for unbounded-loop language in agents and core docs: `every`, `each`, `per
   keyword`, `per claim` near Read/Grep/WebSearch instructions → each hit either has a
   batch discipline and call budget, or gets one. (C2)
3. Grep for `WebSearch`/`WebFetch` in skills + core docs → every mention carries a
   numeric budget. (C3)
4. Grep for agent-loop instructions (`re-verify`, `fix round`, `relaunch`) → each names
   continuation as the default. (C4)
5. Doc weight sweep vs §5 table. (C7)
6. One live smoke run (a real or synthetic posting): record the §2 metrics, compare to
   §3, and note the numbers in the release PR description.

## 7. Fixed-issue log (regression markers)

Recognize regressions by knowing what already burned us:

- **v2.1.0** — fix/re-verify rounds respawned fresh agents (C4) → SendMessage
  continuation became the default across the pipeline.
- **v2.2.0** — writers on `model: inherit` ran on the session's frontier model (C1) →
  pinned to `sonnet`. Fit gate defaulted to 5 searches, Step 4 searched again (C3) →
  2-query default, Step-4 reuse. Verifier did a Read/Grep per trace line, ~60k
  tokens/5 min per round (C2) → one batched read per KB file, all checks in-context,
  10–15-call budget.

- **v2.4.0** — the 2026-07 baseline showed the verifier at **45% of an application's
  tokens** (39 calls vs the 20 ceiling, 4 rounds): it re-read its own deliverables per
  finding (cover.md ×11 — the batch discipline covered KB files but not the package,
  C2), redid script-covered bookkeeping in-agent, and spent rounds on findings the
  writers could have pre-empted (C6) → batch discipline extended to the package files,
  script reports passed into the verifier prompt, writer self-checks, and the
  verified-claim ledger (§7b).

If a symptom matches a log entry, first check whether the fix's wording was weakened or
worked around by a later edit.

## 7b. Implemented levers — mechanical steps moved to scripts (v2.3.0+)

The cheapest token savings is deleting an LLM call for a step that never needed language
understanding. These pipeline steps now run through `scripts/` (dependency-free Python,
stdlib-only tests in `scripts/tests/`) instead of the main session or an agent:

- **ATS keyword coverage** (`ats_coverage.py`) — literal whole-token matching of the
  `jd.md` keyword list against the KB. Was an inline Grep-and-reason step; now one script
  call returning COVERED/UNVERIFIED/GAP buckets. (kills the inline work behind C2/C5.)
- **Trace-map pre-check** (`trace_check.py`) — confirms every trace target resolves to a
  real file and `#anchor` before `application-verifier` runs, so the verifier spends its
  budget on claim-strength judgment, not bookkeeping. (shrinks the verifier's per-round
  work — C2/C6.)
- **Tracker writes** (`tracker.py`) — column order, quoting, and header migration for
  `tracker.csv`, so the orchestrator never reads the whole CSV back to re-emit it.
- **Session metrics** (`session_metrics.py`) — the §2 measurement harness itself.
- **Verified-claim ledger** (`claim_ledger.py`, v2.4.0) — `record` memoizes (claim
  text, source path + anchor, source content hash) on every CLEAN verdict; `check`
  marks byte-identical repeats PRE-VERIFIED before the verifier runs, so it judges only
  new/changed claims. Any drift in claim wording, cited anchor, or source content
  auto-invalidates; app-local sources are never carried over. (shrinks the verifier's
  judgment set across applications — C2/C6.)
- **Master-CV subset check** (`master_diff.py` + ledger `--document` records, v2.5.0) —
  with exemplar documents (`lifecycle/master_documents.md`: one verified master CV +
  cover frame, built once at intake close), the writers subtract/edit instead of
  regenerating and this script proves which cv.md lines are verbatim from a
  hash-VERIFIED master; only CHANGED lines get judged. Turns per-application generation
  and judgment into a delta against a one-time investment. (C5 for the writers' inputs,
  C6 for the verifier's judgment set.)

The judgment in each of these steps stays with the orchestrator/agents; only the
mechanical part moved. Scripts are a convenience the pipeline falls back from gracefully
if absent — never a hard runtime dependency.

## 8. Known open levers (not yet implemented)

Candidates for future releases, in rough order of value:

1. **Paste-first capture.** For login-walled or noisy boards (LinkedIn et al.), ask for
   pasted JD text *before* attempting WebFetch — saves the single largest orchestrator
   token sink and the dead-link failure path. (C3)
2. **KB role-file size budget** (~1,500 words each) enforced at intake, so
   `INDEX.md` selection yields small slices; oversized files get split. (C5)
3. **Main-session model guidance** — a README note that job sessions don't need a
   frontier orchestrator model; the pipeline is procedural by design. (C1, user-side)

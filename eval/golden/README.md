# Tier-2 golden cases — live agent-agreement eval

Tier 1 (`eval/fixtures/`) guards the deterministic scripts. Tier 2 guards what
only the LLM produces: that the **agents** still turn a known posting into a
CLEAN, verbatim, in-budget application after edits to their definitions or the
standards docs. It scores *agreement on discrete signals*, never prose.

## Layout

```
eval/golden/<case>/
├── reference.json     # frozen expected signals (committed)
└── bundle/            # a recorded reference run (committed, PII-free)
    ├── master_cv.md   # the exemplar the run trimmed
    ├── story_bank.md  # the slice the letter and the coverage report drew on
    ├── jd.md          # the posting, including its ATS keyword list
    ├── plan.json      # the writer's edit plan, incl. any one-off slot
    ├── cv.md          # the assembled CV
    ├── cover.md       # the letter
    ├── alias_log.md   # every spelling the alias pass swapped in
    ├── report.md      # the application report; its `## Machine Summary` block
    │                  # supplies the verdict and is cross-checked on line count
    ├── verdict.txt    # fallback verdict source when report.md has no block
    └── session.jsonl  # optional transcript -> cost-metric scoring
```

The verdict is read from `report.md`'s `## Machine Summary` block when present
(falling back to `verdict.txt`). Line counts are always verified independently:
the scorer re-reads `master_cv.md` and checks every `cv.md` line against it, so a
bundle whose CV drifted from its exemplar fails regardless of what the report
claims. A line may also match a **declared** one-off in `plan.json`, or the
posting's alias spelling — the build applies those after proving the document
verbatim (ADR-0008), so they are differences with provenance, not rewordings.

## Two kinds of signal

**Self-checking** — computed from the run's own artifacts, and meaningful for any run:

- `verbatim_fraction` — every `cv.md` line accounted for by the exemplar, an alias swap, or a declared one-off
- `summary_consistency` — the report's self-reported line count against the independent one

**Reference-dependent** — judged against expectations someone recorded for *this* case:

- `verdict`, `cv_lines`, and the `metric_ceilings`

Scoring a run with no case of its own (`--run` without `--case`) reports the first kind and
marks the second `[n/a] — recorded, not judged`. That is the point of the split: a live run's
verdict and length are facts about that application, and failing them against another
application's bands produced a `FAIL` that meant nothing.

`reference.json` fields:

| field | meaning |
|---|---|
| `expected_verdict` | gate — must equal the recorded verdict (`CLEAN`) |
| `verbatim_fraction_min` | gate — fraction of cv.md lines accounted for by the exemplar, an alias swap, or a declared one-off (`1.0`) |
| `cv_lines_expected` / `cv_lines_tolerance` | band — content-line count of `cv.md`, ± tolerance |
| `metric_ceilings` | band — each `session.jsonl`-derived metric ≤ its §3 ceiling |

## Scoring a run

Scoring needs no model, so the recorded bundle replays for **$0** and the scorer
is exercised in CI (`test_eval_tier2.py`). Producing a *fresh* bundle needs the
live pipeline:

1. Run a real `job-apply` on the case's posting (headless: `claude -p`), in a job
   folder whose `master_cv.md` and `story_bank.md` match this bundle's.
2. Score the application folder **where it lies** — nothing to collect:

   ```bash
   python3 scripts/eval_score.py --case acme-backend \
     --run <job folder>/applications/<company> --verdict CLEAN
   ```

   The exemplar is found beside the documents or at the job-folder root above
   them; `--exemplar` overrides that. `--verdict` supplies the gate's final call,
   which a live run does not leave on disk — it is said in the session. A run that
   wrote a `report.md` with a `## Machine Summary` block needs neither flag.

   Missing either one is reported as an input fault and exits 2, rather than
   scoring 0.0 and failing a gate as though the run were bad.
3. To score cost metrics too, drop the session `.jsonl` in the run dir.

   Exit 0 = agreement; exit 1 = a gate failed or a band was exceeded (the
   scorecard names which). Run this before a release that touched an agent or a
   standards doc — the on-demand analogue of TOKEN_ECONOMY.md §6's live smoke run.

## Adding a case

Record one good run as `bundle/`, write `reference.json` to match, keep it
PII-free (synthetic company/skills; no real names, emails, or salary figures).

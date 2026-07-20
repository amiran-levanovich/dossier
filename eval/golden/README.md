# Tier-2 golden cases — live agent-agreement eval

Tier 1 (`eval/fixtures/`) guards the deterministic scripts. Tier 2 guards what
only the LLM produces: that the **agents** still turn a known posting into a
CLEAN, fully-traced, in-budget application after edits to their definitions or
the standards docs. It scores *agreement on discrete signals*, never prose.

## Layout

```
eval/golden/<case>/
├── reference.json     # frozen expected signals (committed)
└── bundle/            # a recorded reference run (committed, PII-free)
    ├── cv_trace.md
    ├── cover_trace.md
    ├── knowledge/     # the KB slice the run used
    ├── verdict.txt    # line 1: CLEAN or FINDINGS (the verifier's final call)
    └── session.jsonl  # optional transcript -> cost-metric scoring
```

`reference.json` fields:

| field | meaning |
|---|---|
| `expected_verdict` | gate — must equal the recorded verdict (`CLEAN`) |
| `traced_fraction_min` | gate — fraction of trace lines that resolve (`1.0`) |
| `claims_expected` / `claims_tolerance` | band — total trace-line count, ± tolerance |
| `metric_ceilings` | band — each `session.jsonl`-derived metric ≤ its §3 ceiling |

## Scoring a run

Scoring needs no model, so the recorded bundle replays for **$0** and the scorer
is exercised in CI (`test_eval_tier2.py`). Producing a *fresh* bundle needs the
live pipeline:

1. Run a real `job-apply` on the case's posting (headless: `claude -p`), pointing
   at a KB that matches `bundle/knowledge/`.
2. Collect the outputs into a run dir: `cv_trace.md`, `cover_trace.md`, the
   `knowledge/` slice, `verdict.txt` (paste the verifier's final CLEAN/FINDINGS),
   and the session `.jsonl` if you want cost metrics scored.
3. Score it:

   ```bash
   python3 scripts/eval_score.py --case acme-backend --run <run-dir>
   ```

   Exit 0 = agreement; exit 1 = a gate failed or a band was exceeded (the
   scorecard names which). Run this before a release that touched an agent or a
   standards doc — the on-demand analogue of TOKEN_ECONOMY.md §6's live smoke run.

## Adding a case

Record one good run as `bundle/`, write `reference.json` to match, keep it
PII-free (synthetic company/skills; no real names, emails, or salary figures).

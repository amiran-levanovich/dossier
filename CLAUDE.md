# CLAUDE.md — maintaining the `dossier` repo

This file is **memory for working *on* this repo**, not guidance for a job search that uses the plugin. Read it before editing.

## What this repo is
`dossier` is a **self-hosting Claude Code plugin repo**: `.claude-plugin/marketplace.json` is a single-entry marketplace whose one plugin (`source: "./"`) is this repo itself. Method: discovery → plan → **criteria-first** → produce → review-loop until clean.

## This is a docs/plugin repo with a thin deterministic helper layer
The substance is Markdown method + JSON manifests. The one exception is `scripts/` — small, dependency-free Python helpers for the **mechanical, no-judgment** steps of the pipeline (ATS keyword coverage, tracker CSV writes, trace-map pre-check, session metrics). They exist because doing that bookkeeping with an LLM call is pure token waste; they never make application-quality judgments (that stays with the agents + the verifier gate). Rule: a script may only replace a step that is deterministic — string/regex matching, CSV manipulation, file/anchor existence. Anything requiring judgment stays an LLM step.

Verification = JSON validates (`python3 -c 'import json…'`), markdown links resolve, a stale-reference sweep is clean, **and** `python3 -m unittest discover -s scripts/tests` passes. `scripts/` uses the standard library only — no third-party test framework, no runtime dependencies.

## Layout
```
.claude-plugin/
├── marketplace.json         # single-entry marketplace, source "./"
└── plugin.json              # the plugin manifest (name: dossier)
.claude/
├── skills/                  # thin routers: job-intake · job-goals · job-apply
└── agents/                  # application-writer · application-verifier · interview-briefer
job_docs/
├── core/                    # job_workflow.md (kernel) · interview_protocol.md · tailoring_method.md · fit_check.md · orchestration.md · quickref.md
├── standards/               # cv_rules · ats_rules · cover_letter_rules · dach_conventions · rendering
├── lifecycle/               # tracking · postmortem · interview_prep · analytics · offer · exemplar · migration
└── templates/               # cv_template.md
eval/
├── fixtures/                # Tier-1: synthetic job folders + blessed snapshots (eval_run.py)
└── golden/                  # Tier-2: agent-agreement cases (eval_score.py)
docs/adr/                    # architecture decisions — why the shape is the shape
docs/agents/                 # per-repo config for the engineering skills: issue-tracker · triage-labels · domain
scripts/                     # deterministic helpers: cv (slot map + verbatim assembly) · aliases (+ alias_groups.md, the shipped table) · ats_coverage · tracker · session_metrics · release_audit · privacy_scan · machine_summary · eval_run/eval_score (+ _common, tests/)
README.md                    # detailed guide    HOW_IT_WORKS.md  # the full flow, plain language
CHANGELOG.md                 # per-release history, Unreleased kept current
CLAUDE.md                    # this file         TOKEN_ECONOMY.md # cost-maintenance doc
CONTEXT.md                   # the glossary — the vocabulary docs/skills/agents must all use
```

## Maintenance conventions
- **No hook, no fixer agents — by design.** Application quality is a judgment; enforcement is the `application-verifier` gate + the superset invariant (every CV line verbatim from the signed exemplar). Don't add a commit hook.
- **Never commit personal data** (names, employers, salaries, application material). The docs are generic method; anything candidate-specific belongs in the user's job folder, not the plugin. Sweep before committing.
- **Skills are thin pointers**, not content: a skill's `SKILL.md` detects context and routes to the authoritative `job_docs/` file. Put substance in the docs, not the skill. Path resolution: project-root copy first, else `../../../job_docs/…` relative to the skill dir.
- **Versioning**: bump `version` in `plugin.json` on a meaningful change (breaking → major; currently 4.x). Bump with a targeted line edit — a JSON load/dump round-trip reformats the manifest. Move the `CHANGELOG.md` Unreleased entries under the new version and date them in the same commit. After the bump's PR merges, tag `main` as `v<version>` and publish a GitHub release; notes end with the consumer update commands (`/plugin marketplace update dossier`, `/plugin update dossier@dossier`). Pre-split history carries `v1.x` tags migrated from `job-workflow-v1.x`.
- **Git**: feature branch → PR into `main` (never commit to `main`); [Conventional Commits](https://www.conventionalcommits.org), subject ≤ 60 chars.
- **Use `CONTEXT.md`'s vocabulary.** It is the glossary, not a spec — when a doc, skill, or agent names a domain concept, use the term defined there and avoid the listed synonyms. A concept missing from it is a signal: either the language is being invented (reconsider) or the glossary has a gap. Decisions that a future reader would find surprising go in `docs/adr/`; contradicting an existing ADR is fine, but say so out loud rather than silently overriding it.
- When editing a doc, update README.md and this layout if the structure changed; run the verification checks above before committing.

## The v4 kill condition — read this before patching around a failure

v4.0.0 bets that **trim-only is sufficient**: that a signed superset exemplar can answer
every posting by selection alone, with no rewording. The bet has a stated failure signal,
recorded in epic #24 and repeated here because that is where a future session will look:

> If **three or more of the first five v4 applications are hand-edited before sending**,
> the bet is wrong, and v4 should be **reverted rather than patched**. v3.x is preserved by
> the `v3.2.1` tag, so returning costs a checkout.

Hand-editing is the trigger because it is the behaviour that would signal it, it fires
within days rather than months, and it is countable. Wall-clock time and method-layer file
count are worth reporting alongside but are **not** the trigger — speed was never in doubt.

The single point of failure, stated plainly: the exemplar's quality now determines the whole
job search. That is the trade. It is mitigated by the build being blocking, unhurried, and
outside any deadline — the opposite of v3, where the highest-stakes judgment happened per
posting, under time pressure, inside a subagent the candidate never read.

## Agent skills

### Issue tracker

Issues live as GitHub issues on `amiran-levanovich/dossier`, managed with the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical triage roles, each label string equal to its name. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context — one `CONTEXT.md` plus `docs/adr/` at the repo root. See `docs/agents/domain.md`.

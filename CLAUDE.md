# CLAUDE.md — maintaining the `dossier` repo

This file is **memory for working *on* this repo**, not guidance for a job search that uses the plugin. Read it before editing.

## What this repo is
`dossier` is a **self-hosting Claude Code plugin repo**: `.claude-plugin/marketplace.json` is a single-entry marketplace whose one plugin (`source: "./"`) is this repo itself. Method: discovery → plan → **criteria-first** → produce → review-loop until clean.

## This is a docs/plugin repo, NOT an app
Markdown and JSON only — no test suite, no language tooling. Verification = JSON validates (`python3 -c 'import json…'`), markdown links resolve, and a stale-reference sweep is clean.

## Layout
```
.claude-plugin/
├── marketplace.json         # single-entry marketplace, source "./"
└── plugin.json              # the plugin manifest (name: dossier)
.claude/
├── skills/                  # thin routers: job-intake · job-goals · job-apply
└── agents/                  # cv-tailor · cover-letter-writer · application-verifier · interview-briefer
job_docs/
├── core/                    # job_workflow.md (kernel) · kb_schema.md · interview_protocol.md · tailoring_method.md · fit_check.md · orchestration.md · quickref.md
├── standards/               # cv_rules · ats_rules · cover_letter_rules · dach_conventions · rendering
├── lifecycle/               # tracking · postmortem · interview_prep · analytics · offer
└── templates/               # cv_template.md
README.md                    # detailed guide    CLAUDE.md  # this file
```

## Maintenance conventions
- **No hook, no fixer agents — by design.** Application quality is a judgment; enforcement is the `application-verifier` gate + the claim→KB traceability contract. Don't add a commit hook.
- **Never commit personal data** (names, employers, salaries, application material). The docs are generic method; anything candidate-specific belongs in the user's job folder, not the plugin. Sweep before committing.
- **Skills are thin pointers**, not content: a skill's `SKILL.md` detects context and routes to the authoritative `job_docs/` file. Put substance in the docs, not the skill. Path resolution: project-root copy first, else `../../../job_docs/…` relative to the skill dir.
- **Versioning**: bump `version` in `plugin.json` on a meaningful change (breaking → major; currently 2.x). Bump with a targeted line edit — a JSON load/dump round-trip reformats the manifest. After the bump's PR merges, tag `main` as `v<version>` and publish a GitHub release; notes end with the consumer update commands (`/plugin marketplace update dossier`, `/plugin update dossier@dossier`). Pre-split history carries `v1.x` tags migrated from `job-workflow-v1.x`.
- **Git**: feature branch → PR into `main` (never commit to `main`); [Conventional Commits](https://www.conventionalcommits.org), subject ≤ 60 chars; end commit messages with the `Co-Authored-By` trailer.
- When editing a doc, update README.md and this layout if the structure changed; run the verification checks above before committing.

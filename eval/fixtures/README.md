# Tier-1 fixtures — the deterministic regression net

Tiny synthetic job folders. `scripts/eval_run.py` runs the deterministic scripts
over each one and asserts the output is byte-identical to the blessed
`expected/` snapshot; `scripts/tests/test_eval_tier1.py` runs the same
comparison under `unittest`, so drift fails CI without anyone remembering to
look. Nothing here is real: no real person, employer, or number, and
`scripts/privacy_scan.py` runs over the tree.

## What a fixture holds

```
eval/fixtures/<case>/
├── jd.md            # the posting — its `## ATS keywords` block drives coverage,
│                    # and its prose is what the alias pass reads for spellings
├── master_cv.md     # the exemplar, in the templates/cv_template.md shape
├── story_bank.md    # the bank: wider than the exemplar, by design (ADR-0006)
├── plan.json        # the edit plan a writer would have emitted
└── expected/        # blessed snapshots, one per check (committed)
```

`out/` and `out-aliased/` are build byproducts and are gitignored — the snapshot
in `expected/` is what holds their content.

A directory without a `jd.md` is not a fixture and is skipped.

## The trap: slot ids are content hashes

`plan.json` names slots by id, and an id is a hash of the slot's own text
(ADR-0003). **Editing `master_cv.md` renames every slot it touched, and the plan
stops resolving** — the build then fails with `unknown slot id`, which is correct
behaviour and a broken fixture at the same time. After changing an exemplar:

```sh
python3 scripts/cv.py map eval/fixtures/<case>/master_cv.md   # read the new ids
$EDITOR eval/fixtures/<case>/plan.json                        # update them
python3 scripts/eval_run.py --bless                           # re-record
```

Review the blessed diff before committing it. That diff is the whole point of
the bless step: an intentional change reads as one reviewable hunk, and an
unintentional one reads as a surprise.

## The cases

| Fixture | Pins |
| :-- | :-- |
| `acme-backend` | The happy path — a slot map, an assembly that keeps, drops, reorders and carries one declared one-off slot, the same build with the alias pass on, and a three-way coverage report with one keyword in each bucket (including two matched through an alias group) |
| `rejected-plan` | The refusal — a plan carrying `patch[]` (which ADR-0005 removed) and an unknown slot id must exit 1 and write **no `cv.md` at all**; the snapshot records the file as `<not written>`, so a build that started emitting a partial CV would be caught |

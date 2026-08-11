# Story bank

Synthetic fixture data. No real person, employer, or number appears here.

## Acme — Senior Backend Developer

Built a Rails API serving 2M requests/day with a p99 under 120ms. Owned the
billing service end to end, including the on-call rotation for it.

We trialled Go for one throughput-bound service and dropped it after a quarter —
the team could not staff two languages. Worth telling as a scoping story, and
the reason it is not on the CV.

## Things that went wrong

A migration I ran without a backfill plan locked a table for nine minutes in
production. What I changed afterwards: every migration gets a dry run against a
restored snapshot first.

# Tracker Analytics — patterns across the whole search

Per-application learning lives in `lifecycle/postmortem.md`; this doc reads **across** applications: the funnel, where applications die, pace, and what to change strategically. The numbers come from `tracker.csv` — computed by the recipe below, never estimated by eye.

## When to run

- The user asks: "how's my search going", "any patterns", a strategy or monthly review.
- The post-mortem escalation fires: **3+ rejections at the same stage** (`lifecycle/postmortem.md` Step 3) — this doc is the mechanized version of that check.
- Roughly every 10 closed applications, offer it unprompted.

## Step 1 — Compute

Run this from the job folder root (stdlib only; tolerant of legacy rows without the `stage_reached`/`date_closed` columns). Present its output; do not recount by hand.

```bash
python3 - <<'EOF'
import csv, re, statistics
from datetime import date, timedelta

TODAY = date.today()
def d(s):
    try: return date.fromisoformat((s or '').strip())
    except ValueError: return None

rows = [r for r in csv.DictReader(open('tracker.csv')) if (r.get('company') or '').strip()]
for r in rows:
    r['status'] = (r.get('status') or '').strip()
    r['stage'] = (r.get('stage_reached') or '').strip()
    # legacy rows: infer 'none' from the auto-reply note
    if not r['stage'] and r['status'] == 'rejected' and re.search(r'auto-reply|generic', r.get('notes') or '', re.I):
        r['stage'] = 'none'

submitted = [r for r in rows if r['status'] != 'to_apply']
reached   = [r for r in submitted if r['stage'] in ('screen','tech','final') or r['status'] in ('interview','offer')]
closed    = [r for r in rows if r['status'] in ('rejected','withdrawn','offer')]
offers    = [r for r in rows if r['status'] == 'offer']

print(f"FUNNEL  total {len(rows)} | submitted {len(submitted)} | reached a human {len(reached)} | offers {len(offers)}")
by_status = {}
for r in rows: by_status[r['status']] = by_status.get(r['status'], 0) + 1
print('STATUS  ' + ' | '.join(f'{k} {v}' for k, v in sorted(by_status.items())))
if len(closed) >= 10:
    print(f"RATES   submitted→human {len(reached)}/{len(submitted)} = {100*len(reached)//max(len(submitted),1)}% | human→offer {len(offers)}/{max(len(reached),1)} = {100*len(offers)//max(len(reached),1)}%")
else:
    print(f"RATES   only {len(closed)} closed rows — too few for percentages, read the counts")

rej = [r for r in rows if r['status'] == 'rejected']
prof = {}
for r in rej: prof[r['stage'] or 'unknown'] = prof.get(r['stage'] or 'unknown', 0) + 1
print('DIED AT ' + (' | '.join(f'{k} {v}' for k, v in sorted(prof.items(), key=lambda kv: -kv[1])) or '—'))

recent = [r for r in rows if (a := d(r['date_applied'])) and (TODAY - a).days <= 28]
spans  = [((d(r['date_closed']) - d(r['date_applied'])).days) for r in rows if d(r['date_applied']) and d(r['date_closed'])]
print(f"PACE    {len(recent)} applications in the last 4 weeks"
      + (f" | median days to close {statistics.median(spans):g}" if spans else ""))

stale   = [r for r in rows if r['status'] == 'applied' and (a := d(r['date_applied'])) and (TODAY - a).days > 21]
undated = [r for r in rows if r['status'] in ('to_apply','applied','interview') and not re.search(r'\d{4}-\d{2}-\d{2}', r.get('next_action') or '')]
noclose = [r for r in closed if not d(r['date_closed'])]
for label, bad in (('STALE   >21d no response:', stale), ('HYGIENE no dated next_action:', undated), ('HYGIENE terminal w/o date_closed:', noclose)):
    if bad: print(label, ', '.join(r['company'] for r in bad))
EOF
```

Notes on the output:

- **Small-N guard**: under 10 closed rows the recipe refuses percentages — rates on tiny samples read as signal and aren't. Report counts and say so.
- `DIED AT unknown` means legacy rejected rows whose stage can't be inferred — offer to backfill `stage_reached` from the application folders' notes.
- STALE/HYGIENE lines are tracker-discipline defects (`lifecycle/tracking.md`); fix them with the user before interpreting anything — bad data makes every pattern below unreliable.

## Step 2 — Interpret

Rules of thumb, **not market benchmarks** — they order the investigation, they don't grade the user. Read the dominant pattern, not single data points; act on the first row that matches.

| Pattern in the numbers                                       | Most likely problem              | Do this                                                                                                         |
| :----------------------------------------------------------- | :------------------------------- | :-------------------------------------------------------------------------------------------------------------- |
| Rejections mostly `DIED AT none` (auto-replies, closed fast) | The machine pass — ATS or volume | Run `postmortem.md` Step 2 across the folders: recurring keyword gaps → KB; hard filters → `goals.md` targeting |
| Rejections cluster at `screen`                               | Fit signaling to a human reader  | Review summary framing, seniority band, salary answer, logistics against `goals.md` and recent screens          |
| Rejections cluster at `tech`/`final`                         | Materials work; interviews don't | Debrief harder after each round (`lifecycle/interview_prep.md`); feed wobbles back into KB stories              |
| Funnel healthy but PACE low                                  | Volume, not quality              | More applications at current standards beats another materials pass                                             |
| Everything stuck `applied`, little closure                   | Pipeline going cold              | Work the STALE list: follow up or close out; consider channels beyond portals (referrals, direct)               |

**3+ rejections at the same stage** is the formal escalation trigger (from `postmortem.md` Step 3): stop per-application fixes and have the strategy conversation — targets, seniority band, market, or the materials as a whole.

## Step 3 — Diagnose and act

Same contract as the post-mortem: one paragraph — the dominant pattern, the evidence, **one specific strategy adjustment** — stated plainly; a comforting wrong diagnosis costs future applications. Then apply it where it belongs: targeting changes in `goals.md`, missing-but-true keywords into the KB, prep focus for the next interview. The report itself is presented in chat and not saved — the learning, not the report, carries forward.

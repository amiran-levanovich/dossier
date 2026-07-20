#!/usr/bin/env python3
"""eval_score.py — Tier-2 agent-agreement scorer (on-demand, mostly zero-LLM).

Tier 1 (eval_run.py) guards the deterministic pipeline. Tier 2 guards the part
only the LLM can produce: that the *agents* still turn a known posting into a
CLEAN, fully-traced, in-budget application after edits to their definitions or
the standards docs. You can't assert generated prose, so — like career-ops'
golden eval — this scores **agreement on the stable, discrete signals**, gating
the pass/fail ones and tolerance-banding the continuous ones:

  gate  verdict == CLEAN           (the verifier's final call, recorded)
  gate  traced_fraction >= 1.0     (every claim resolves to a real source)
  band  |claims_count - expected| <= tolerance
  band  each cost metric <= its §3 ceiling   (skipped if no transcript)

Producing a fresh run bundle needs the live pipeline (a `claude -p` job-apply
run); SCORING a bundle does not — so a recorded bundle replays for $0 and keeps
the scorer itself CI-testable. See eval/golden/README.md for the workflow.

A run bundle is a directory holding: cv_trace.md, cover_trace.md, knowledge/,
and optionally session.jsonl. The verdict comes from report.md's `## Machine
Summary` block when present (falling back to a verdict.txt whose first line is
CLEAN or FINDINGS); if that block also self-reports a claim count, it is
cross-checked against the independent trace count as an extra gate. Claims are
always counted independently — the self-report is never trusted for them.

Usage:
  eval_score.py --case <id>                 score the case's recorded bundle
  eval_score.py --case <id> --run <dir>      score a fresh live-run bundle
  eval_score.py --case <id> --json           machine-readable scorecard

Exit codes: 0 agreement · 1 disagreement · 2 usage/IO error.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import machine_summary
import session_metrics
import trace_check

TRACE_FILES = ("cv_trace.md", "cover_trace.md")


@dataclass(frozen=True)
class Signal:
    name: str
    kind: str          # "gate" | "band"
    actual: object
    target: str
    passed: bool
    skipped: bool = False


@dataclass
class Scorecard:
    signals: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(s.passed for s in self.signals if not s.skipped)


def metrics_from_stats(stats: dict) -> dict:
    """Reduce a session_metrics.analyze() stats dict to scored metrics."""
    tool_calls = sum(stats.get("tools", {}).values()) + sum(stats.get("sidechain_tools", {}).values())
    return {
        "web_fetch": stats.get("web_fetch", 0),
        "web_search": stats.get("web_search", 0),
        "tool_calls_total": tool_calls,
        "subagent_spawns": sum(stats.get("subagents", {}).values()),
    }


def compute_metrics(session_path: Path) -> dict:
    p = Path(session_path)
    if not p.is_file():
        return {}
    return metrics_from_stats(session_metrics.analyze(p))


def read_verdict(bundle_dir) -> str:
    path = Path(bundle_dir) / "verdict.txt"
    if not path.is_file():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            return line.strip().upper()
    return ""


def traced_fraction(bundle_dir):
    bundle_dir = Path(bundle_dir)
    kb_dir = bundle_dir / "knowledge"
    total_lines = 0
    total_ok = 0
    for name in TRACE_FILES:
        tf = bundle_dir / name
        if not tf.is_file():
            continue
        n_lines, n_ok, _ = trace_check.check_file(tf, kb_dir, bundle_dir)
        total_lines += n_lines
        total_ok += n_ok
    frac = (total_ok / total_lines) if total_lines else 0.0
    return total_ok, total_lines, frac


def score(reference: dict, verdict: str, n_ok: int, n_lines: int, metrics: dict) -> Scorecard:
    card = Scorecard()

    exp_verdict = reference["expected_verdict"].upper()
    card.signals.append(Signal(
        "verdict", "gate", verdict, f"== {exp_verdict}", verdict == exp_verdict))

    frac = (n_ok / n_lines) if n_lines else 0.0
    frac_min = reference["traced_fraction_min"]
    card.signals.append(Signal(
        "traced_fraction", "gate", round(frac, 3), f">= {frac_min}", frac >= frac_min))

    expected = reference["claims_expected"]
    tol = reference["claims_tolerance"]
    card.signals.append(Signal(
        "claims_count", "band", n_lines, f"{expected} +/-{tol}", abs(n_lines - expected) <= tol))

    for name, ceiling in reference.get("metric_ceilings", {}).items():
        if name in metrics:
            card.signals.append(Signal(
                name, "band", metrics[name], f"<= {ceiling}", metrics[name] <= ceiling))
        else:
            card.signals.append(Signal(
                name, "band", None, f"<= {ceiling}", True, skipped=True))
    return card


def load_summary(bundle_dir):
    """The run's `## Machine Summary` block from report.md, or None."""
    report = Path(bundle_dir) / "report.md"
    if not report.is_file():
        return None
    return machine_summary.parse(report.read_text(encoding="utf-8"))


def score_bundle(bundle_dir, reference: dict) -> Scorecard:
    bundle_dir = Path(bundle_dir)
    summary = load_summary(bundle_dir)

    # The verdict is the verifier's judgment — not something this scorer can
    # recompute — so take it from the structured Machine Summary block when the
    # run recorded one, falling back to verdict.txt. Claims stay INDEPENDENTLY
    # counted below; the block's self-report is never trusted for those.
    verdict = (summary.get("verdict", "").upper() if summary else "") or read_verdict(bundle_dir)
    n_ok, n_lines, _ = traced_fraction(bundle_dir)
    metrics = compute_metrics(bundle_dir / "session.jsonl")

    card = score(reference, verdict, n_ok, n_lines, metrics)

    # Cross-check: if the run self-reported a claim count, it must match the
    # independent trace count. Consuming the block makes the eval stronger — a
    # run whose self-report disagrees with reality fails here.
    if summary and isinstance(summary.get("claims_total"), int):
        card.signals.append(Signal(
            "summary_consistency", "gate", summary["claims_total"],
            f"== {n_lines} (independent count)", summary["claims_total"] == n_lines))
    return card


def load_reference(path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _render(card: Scorecard) -> str:
    lines = []
    for s in card.signals:
        if s.skipped:
            mark = "SKIP"
        else:
            mark = "ok  " if s.passed else "FAIL"
        lines.append(f"  [{mark}] {s.kind:4} {s.name}: {s.actual} (want {s.target})")
    lines.append(f"RESULT: {'PASS' if card.ok else 'FAIL'}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--case", required=True, help="golden case id (a dir under --golden-root)")
    ap.add_argument("--golden-root", default="eval/golden", help="golden cases root")
    ap.add_argument("--run", help="a fresh run bundle to score (default: the case's recorded bundle)")
    ap.add_argument("--json", action="store_true", help="emit the scorecard as JSON")
    args = ap.parse_args(argv)

    case_dir = Path(args.golden_root) / args.case
    ref_path = case_dir / "reference.json"
    if not ref_path.is_file():
        print(f"eval_score: no reference at {ref_path}", file=sys.stderr)
        return 2

    reference = load_reference(ref_path)
    bundle = Path(args.run) if args.run else case_dir / "bundle"
    if not bundle.is_dir():
        print(f"eval_score: no bundle at {bundle}", file=sys.stderr)
        return 2

    card = score_bundle(bundle, reference)

    if args.json:
        print(json.dumps(
            [{"name": s.name, "kind": s.kind, "actual": s.actual,
              "target": s.target, "passed": s.passed, "skipped": s.skipped}
             for s in card.signals], indent=1))

    print(f"EVAL-SCORE case={args.case} bundle={bundle}", file=sys.stderr)
    print(_render(card), file=sys.stderr)
    return 0 if card.ok else 1


if __name__ == "__main__":
    sys.exit(main())

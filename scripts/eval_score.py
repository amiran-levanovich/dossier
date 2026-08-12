#!/usr/bin/env python3
"""eval_score.py — Tier-2 agent-agreement scorer (on-demand, mostly zero-LLM).

Tier 1 (eval_run.py) guards the deterministic pipeline. Tier 2 guards the part
only the LLM can produce: that the *agents* still turn a known posting into a
CLEAN, verbatim, in-budget application after edits to their definitions or the
standards docs. You can't assert generated prose, so — like career-ops' golden
eval — this scores **agreement on the stable, discrete signals**, gating the
pass/fail ones and tolerance-banding the continuous ones:

  gate  verdict == CLEAN            (the gate's final call, recorded)
  gate  verbatim_fraction >= 1.0    (every cv.md line is exemplar text or a
                                     declared one-off)
  band  |cv_lines - expected| <= tolerance
  band  each cost metric <= its §3 ceiling   (skipped if no transcript)

Producing a fresh run bundle needs the live pipeline (a `claude -p` job-apply
run); SCORING a bundle does not — so a recorded bundle replays for $0 and keeps
the scorer itself CI-testable. See eval/golden/README.md for the workflow.

A run bundle is a directory holding: master_cv.md, plan.json, cv.md, cover.md,
report.md, verdict.txt, and optionally session.jsonl. The verdict comes from
report.md's `## Machine Summary` block when present (falling back to a
verdict.txt whose first line is CLEAN or FINDINGS); if that block also
self-reports a line count, it is cross-checked against the independent one as an
extra gate. Lines are always counted independently — by re-reading the exemplar,
never by trusting the self-report.

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

import _common
import aliases
import cv
import machine_summary
import session_metrics


@dataclass(frozen=True)
class Signal:
    name: str
    kind: str          # "gate" | "band"
    actual: object
    target: str
    passed: bool
    skipped: bool = False
    reason: str = ""   # why it was skipped: no transcript, no reference


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


class MissingExemplar(FileNotFoundError):
    """No exemplar to check the CV against — an input fault, not a bad run."""


class MissingVerdict(FileNotFoundError):
    """No recorded gate verdict — also an input fault, and worth saying so.

    A live application folder has no report.md or verdict.txt: the gate returns
    its call in the session, not as an artifact. Scoring one without a verdict
    would fail the verdict gate as though the run had been judged and found
    wanting, which is the same wrong-reason failure a missing exemplar caused.
    """


# `<job folder>/applications/<company>/` is two levels below the root, and a
# recorded bundle keeps its own copy beside the documents. Searching further up
# would start finding other people's job folders on a shared machine.
EXEMPLAR_SEARCH_DEPTH = 2


def resolve_exemplar(bundle_dir, explicit=None):
    """The exemplar to check against: the given one, or the nearest above.

    A recorded bundle carries its own `master_cv.md`; a *live* run does not —
    the exemplar sits at the job-folder root while the documents sit in
    `applications/<company>/`. Walking up is what lets an application folder be
    scored where it lies, instead of being copied into bundle shape by hand.
    """
    if explicit is not None:
        return Path(explicit)
    here = Path(bundle_dir)
    for candidate in [here, *list(here.parents)[:EXEMPLAR_SEARCH_DEPTH]]:
        found = candidate / "master_cv.md"
        if found.is_file():
            return found
    return None


def verbatim_fraction(bundle_dir, exemplar=None):
    """Re-check the recorded cv.md against the exemplar, independently.

    The run's own build already ran this self-test, which is exactly why the
    scorer runs it again from the artifacts rather than reading the run's word
    for it: a bundle whose cv.md drifted from its master_cv.md fails here.
    """
    bundle_dir = Path(bundle_dir)
    doc = bundle_dir / "cv.md"
    exemplar = resolve_exemplar(bundle_dir, exemplar)
    if exemplar is None or not exemplar.is_file():
        raise MissingExemplar(
            f"no master_cv.md beside {bundle_dir} or within "
            f"{EXEMPLAR_SEARCH_DEPTH} directories above it — pass --exemplar")
    if not doc.is_file():
        raise MissingExemplar(f"no cv.md in {bundle_dir}")

    exempt = set()
    plan_path = bundle_dir / "plan.json"
    if plan_path.is_file():
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        for one_off in cv.one_offs_by_id(plan).values():
            for _, norm in _common.content_lines(one_off.get("text", "")):
                exempt.add(norm)

    # A delivered cv.md may differ from the exemplar by the posting's alias
    # spellings, which the build applies after its own verbatim proof (ADR-0008).
    # Rather than trust alias_log.md, re-run that pass over the exemplar and
    # accept either spelling: the exemplar is verbatim against itself, so the
    # empty self-test result below is the honest one.
    exemplar_text = exemplar.read_text(encoding="utf-8")
    jd = bundle_dir / "jd.md"
    if jd.is_file():
        groups, _ = aliases.load_table([aliases.PLUGIN_TABLE])
        aliased, _ = aliases.apply(exemplar_text.splitlines(),
                                   jd.read_text(encoding="utf-8"), groups,
                                   cv.VerbatimResult(0, 0, []))
        for _, norm in _common.content_lines("\n".join(aliased)):
            exempt.add(norm)

    result = cv.verbatim_report(doc.read_text(encoding="utf-8").splitlines(),
                                exemplar_text, exempt)
    n_ok = result.verbatim + result.exempted
    frac = (n_ok / result.total) if result.total else 0.0
    return n_ok, result.total, frac


# Without a reference these have nothing to be judged against — a run's verdict
# and length are facts about that application, not regressions. The other
# signals check the run against *itself*, so they hold either way.
NO_REFERENCE = "no reference — this run is not a golden case"


def score(reference, verdict: str, n_ok: int, n_lines: int, metrics: dict) -> Scorecard:
    card = Scorecard()
    ref = reference or {}

    if reference:
        exp_verdict = ref["expected_verdict"].upper()
        card.signals.append(Signal(
            "verdict", "gate", verdict, f"== {exp_verdict}", verdict == exp_verdict))
    else:
        card.signals.append(Signal(
            "verdict", "gate", verdict, "recorded", True,
            skipped=True, reason=NO_REFERENCE))

    # Self-consistent: computed from the run's own artifacts, so it means the
    # same thing with or without a case to compare against.
    frac = (n_ok / n_lines) if n_lines else 0.0
    frac_min = ref.get("verbatim_fraction_min", 1.0)
    card.signals.append(Signal(
        "verbatim_fraction", "gate", round(frac, 3), f">= {frac_min}", frac >= frac_min))

    if reference:
        expected = ref["cv_lines_expected"]
        tol = ref["cv_lines_tolerance"]
        card.signals.append(Signal(
            "cv_lines", "band", n_lines, f"{expected} +/-{tol}",
            abs(n_lines - expected) <= tol))
    else:
        card.signals.append(Signal(
            "cv_lines", "band", n_lines, "recorded", True,
            skipped=True, reason=NO_REFERENCE))

    for name, ceiling in ref.get("metric_ceilings", {}).items():
        if name in metrics:
            card.signals.append(Signal(
                name, "band", metrics[name], f"<= {ceiling}", metrics[name] <= ceiling))
        else:
            card.signals.append(Signal(
                name, "band", None, f"<= {ceiling}", True,
                skipped=True, reason="no transcript"))
    return card


def load_summary(bundle_dir):
    """The run's `## Machine Summary` block from report.md, or None."""
    report = Path(bundle_dir) / "report.md"
    if not report.is_file():
        return None
    return machine_summary.parse(report.read_text(encoding="utf-8"))


def score_bundle(bundle_dir, reference, exemplar=None, verdict_override=None) -> Scorecard:
    bundle_dir = Path(bundle_dir)
    summary = load_summary(bundle_dir)

    # The verdict is the gate's judgment — not something this scorer can
    # recompute — so take it from the structured Machine Summary block when the
    # run recorded one, falling back to verdict.txt. Lines stay INDEPENDENTLY
    # counted below; the block's self-report is never trusted for those.
    # The exemplar is checked first: without it there is nothing to score at all,
    # so reporting a missing verdict ahead of it would send the operator after
    # the smaller of two faults.
    n_ok, n_lines, _ = verbatim_fraction(bundle_dir, exemplar)
    verdict = (verdict_override or "").upper() or (
        summary.get("verdict", "").upper() if summary else "") or read_verdict(bundle_dir)
    if not verdict:
        raise MissingVerdict(
            f"no gate verdict for {bundle_dir}: no `## Machine Summary` block in report.md"
            " and no verdict.txt — pass --verdict CLEAN|FINDINGS")
    metrics = compute_metrics(bundle_dir / "session.jsonl")

    card = score(reference, verdict, n_ok, n_lines, metrics)

    # Cross-check: if the run self-reported a line count, it must match the
    # independent count. Consuming the block makes the eval stronger — a run
    # whose self-report disagrees with reality fails here.
    if summary and isinstance(summary.get("cv_lines"), int):
        card.signals.append(Signal(
            "summary_consistency", "gate", summary["cv_lines"],
            f"== {n_lines} (independent count)", summary["cv_lines"] == n_lines))
    return card


def load_reference(path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _render(card: Scorecard) -> str:
    lines = []
    for s in card.signals:
        if s.skipped:
            mark = "n/a " if s.reason == NO_REFERENCE else "SKIP"
        else:
            mark = "ok  " if s.passed else "FAIL"
        if s.reason == NO_REFERENCE:
            lines.append(f"  [{mark}] {s.kind:4} {s.name}: {s.actual} — recorded, not judged")
            continue
        note = f" — {s.reason}" if s.reason else ""
        lines.append(f"  [{mark}] {s.kind:4} {s.name}: {s.actual} (want {s.target}){note}")
    lines.append(f"RESULT: {'PASS' if card.ok else 'FAIL'}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--case", help="golden case id (a dir under --golden-root); omit to score"
                                   " a run against itself only")
    ap.add_argument("--golden-root", default="eval/golden", help="golden cases root")
    ap.add_argument("--run", help="a run to score: a bundle, or an application folder in place"
                                 " (default: the case's recorded bundle)")
    ap.add_argument("--exemplar", help="path to master_cv.md, when it is not beside the"
                                       " documents or at the job-folder root")
    ap.add_argument("--verdict", choices=["CLEAN", "FINDINGS"],
                    help="the gate's final call, for a run that recorded no report.md")
    ap.add_argument("--json", action="store_true", help="emit the scorecard as JSON")
    args = ap.parse_args(argv)

    if not args.case and not args.run:
        print("eval_score: give --case, --run, or both", file=sys.stderr)
        return 2

    reference = None
    if args.case:
        ref_path = Path(args.golden_root) / args.case / "reference.json"
        if not ref_path.is_file():
            print(f"eval_score: no reference at {ref_path}", file=sys.stderr)
            return 2
        reference = load_reference(ref_path)

    bundle = Path(args.run) if args.run else Path(args.golden_root) / args.case / "bundle"
    if not bundle.is_dir():
        print(f"eval_score: no bundle at {bundle}", file=sys.stderr)
        return 2

    try:
        card = score_bundle(bundle, reference, args.exemplar, args.verdict)
    except (MissingExemplar, MissingVerdict) as exc:
        print(f"eval_score: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(
            [{"name": s.name, "kind": s.kind, "actual": s.actual,
              "target": s.target, "passed": s.passed, "skipped": s.skipped}
             for s in card.signals], indent=1))

    label = f"case={args.case}" if args.case else "case=none (self-check only)"
    print(f"EVAL-SCORE {label} bundle={bundle}", file=sys.stderr)
    print(_render(card), file=sys.stderr)
    return 0 if card.ok else 1


if __name__ == "__main__":
    sys.exit(main())

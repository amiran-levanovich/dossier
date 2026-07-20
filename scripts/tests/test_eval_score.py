#!/usr/bin/env python3
"""Tests for eval_score.py — the Tier-2 agent-agreement scorer.

Run: python3 -m unittest discover scripts/tests

Stdlib only. The gate/band logic (`score`) and the metric extraction are pure
and tested with synthetic inputs; a small recorded golden bundle exercises the
end-to-end path deterministically (no model needed to SCORE a recorded run).
"""

import json
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import eval_score  # noqa: E402


REF = {
    "expected_verdict": "CLEAN",
    "claims_expected": 3,
    "claims_tolerance": 1,
    "traced_fraction_min": 1.0,
    "metric_ceilings": {"web_fetch": 2, "subagent_spawns": 8},
}


class TmpMixin(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p


# --------------------------------------------------------------------------
# score() — the gate/band contract
# --------------------------------------------------------------------------
class TestScore(unittest.TestCase):
    def score(self, verdict="CLEAN", n_ok=3, n_lines=3, metrics=None):
        return eval_score.score(REF, verdict, n_ok, n_lines, metrics or {})

    def test_clean_run_passes(self):
        card = self.score()
        self.assertTrue(card.ok)

    def test_verdict_gate_fails_when_not_clean(self):
        card = self.score(verdict="FINDINGS")
        self.assertFalse(card.ok)
        sig = next(s for s in card.signals if s.name == "verdict")
        self.assertEqual(sig.kind, "gate")
        self.assertFalse(sig.passed)

    def test_traced_fraction_gate_fails_below_one(self):
        card = self.score(n_ok=2, n_lines=3)  # fraction 0.67 < 1.0
        self.assertFalse(card.ok)
        self.assertFalse(next(s for s in card.signals if s.name == "traced_fraction").passed)

    def test_zero_claims_fails_fraction_gate(self):
        card = self.score(n_ok=0, n_lines=0)
        self.assertFalse(card.ok)

    def test_claims_band_within_tolerance_passes(self):
        # expected 3, tolerance 1 -> 4 is within band
        self.assertTrue(self.score(n_ok=4, n_lines=4).ok)

    def test_claims_band_outside_tolerance_fails(self):
        card = self.score(n_ok=5, n_lines=5)  # |5-3| = 2 > 1
        self.assertFalse(card.ok)
        self.assertEqual(next(s for s in card.signals if s.name == "claims_count").kind, "band")

    def test_metric_over_ceiling_fails(self):
        card = self.score(metrics={"web_fetch": 3, "subagent_spawns": 2})  # 3 > 2
        self.assertFalse(card.ok)
        self.assertFalse(next(s for s in card.signals if s.name == "web_fetch").passed)

    def test_metric_under_ceiling_passes(self):
        self.assertTrue(self.score(metrics={"web_fetch": 1, "subagent_spawns": 8}).ok)

    def test_absent_metric_is_skipped_not_failed(self):
        # No transcript -> metrics {} -> ceiling checks skipped, not failed.
        card = self.score(metrics={})
        self.assertTrue(card.ok)
        self.assertTrue(any(s.skipped for s in card.signals if s.name in REF["metric_ceilings"]))


# --------------------------------------------------------------------------
# metric extraction from a session_metrics stats dict
# --------------------------------------------------------------------------
class TestMetricsFromStats(unittest.TestCase):
    def test_maps_and_sums(self):
        stats = {
            "tools": Counter({"Read": 5, "WebFetch": 1}),
            "sidechain_tools": Counter({"Grep": 4}),
            "web_fetch": 1,
            "web_search": 2,
            "subagents": Counter({"cv-tailor": 1, "application-verifier": 2}),
        }
        m = eval_score.metrics_from_stats(stats)
        self.assertEqual(m["web_fetch"], 1)
        self.assertEqual(m["web_search"], 2)
        self.assertEqual(m["tool_calls_total"], 10)  # 5+1+4
        self.assertEqual(m["subagent_spawns"], 3)


# --------------------------------------------------------------------------
# artifact readers over a bundle
# --------------------------------------------------------------------------
class TestBundleReaders(TmpMixin):
    def _bundle(self, verdict="CLEAN"):
        self.write("knowledge/skills.md", "# Skills\n\n## Languages\nPython.\n")
        self.write("cv_trace.md", '- "wrote Python" → skills.md#languages\n')
        self.write("cover_trace.md", '- "Python focus" → skills.md#languages\n')
        self.write("verdict.txt", verdict + "\n")
        return self.root

    def test_read_verdict_uppercases_first_line(self):
        self._bundle(verdict="clean")
        self.assertEqual(eval_score.read_verdict(self.root), "CLEAN")

    def test_traced_fraction_all_resolve(self):
        self._bundle()
        n_ok, n_lines, frac = eval_score.traced_fraction(self.root)
        self.assertEqual((n_ok, n_lines), (2, 2))
        self.assertEqual(frac, 1.0)

    def test_traced_fraction_flags_dangling(self):
        self._bundle()
        self.write("cv_trace.md", '- "x" → skills.md#nope\n')  # bad anchor
        n_ok, n_lines, frac = eval_score.traced_fraction(self.root)
        self.assertLess(frac, 1.0)

    def test_score_bundle_end_to_end(self):
        ref = dict(REF, claims_expected=2)
        card = eval_score.score_bundle(self._bundle(), ref)
        self.assertTrue(card.ok)


# --------------------------------------------------------------------------
# load_reference + main
# --------------------------------------------------------------------------
class TestMain(TmpMixin):
    def _case(self, verdict="CLEAN"):
        # golden/acme/reference.json + a recorded bundle beside it
        ref = dict(REF, claims_expected=2)
        self.write("golden/acme/reference.json", json.dumps(ref))
        self.write("golden/acme/bundle/knowledge/skills.md", "# Skills\n\n## Languages\nPython.\n")
        self.write("golden/acme/bundle/cv_trace.md", '- "wrote Python" → skills.md#languages\n')
        self.write("golden/acme/bundle/cover_trace.md", '- "Python focus" → skills.md#languages\n')
        self.write("golden/acme/bundle/verdict.txt", verdict + "\n")

    def run_main(self, argv):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = eval_score.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_recorded_bundle_scores_pass(self):
        self._case()
        code, _, err = self.run_main(["--case", "acme", "--golden-root", str(self.root / "golden")])
        self.assertEqual(code, 0)
        self.assertIn("PASS", err)

    def test_regressed_bundle_scores_fail(self):
        self._case(verdict="FINDINGS")
        code, _, err = self.run_main(["--case", "acme", "--golden-root", str(self.root / "golden")])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()

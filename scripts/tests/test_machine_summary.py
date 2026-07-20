#!/usr/bin/env python3
"""Tests for machine_summary.py — parse/validate a report's `## Machine Summary`.

Run: python3 -m unittest discover scripts/tests

Stdlib only. The Machine Summary is an optional, flat key:value block a report
MAY carry so scripts (analytics, the eval layer) read structured signals instead
of re-parsing prose. Absence is fine; a present block must be well-formed.
"""

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import machine_summary  # noqa: E402


VALID_BLOCK = """\
# Acme — Backend Developer

Some prose about the application.

## Machine Summary

    verdict: CLEAN
    verify_rounds: 1
    claims_traced: 3
    claims_total: 3
    ats_covered: 4
    ats_unverified: 1
    ats_gap: 1
    ledger_preverified: 0

## Something After
More prose that must not be parsed as summary fields.
"""


class TestParse(unittest.TestCase):
    def test_parses_typed_fields(self):
        d = machine_summary.parse(VALID_BLOCK)
        self.assertEqual(d["verdict"], "CLEAN")
        self.assertEqual(d["claims_traced"], 3)          # int
        self.assertEqual(d["claims_total"], 3)
        self.assertIsInstance(d["verify_rounds"], int)

    def test_stops_at_next_heading(self):
        d = machine_summary.parse(VALID_BLOCK)
        self.assertNotIn("more", d)  # "More prose..." after the next heading is ignored
        self.assertEqual(set(d), {
            "verdict", "verify_rounds", "claims_traced", "claims_total",
            "ats_covered", "ats_unverified", "ats_gap", "ledger_preverified"})

    def test_absent_block_returns_none(self):
        self.assertIsNone(machine_summary.parse("# Report\n\nNo summary here.\n"))


class TestValidate(unittest.TestCase):
    def good(self):
        return {"verdict": "CLEAN", "claims_traced": 3, "claims_total": 3}

    def test_valid_has_no_errors(self):
        self.assertEqual(machine_summary.validate(self.good()), [])

    def test_missing_required_key(self):
        d = self.good(); del d["verdict"]
        self.assertTrue(any("verdict" in e for e in machine_summary.validate(d)))

    def test_bad_verdict_value(self):
        d = self.good(); d["verdict"] = "MAYBE"
        self.assertTrue(machine_summary.validate(d))

    def test_traced_exceeds_total(self):
        d = self.good(); d["claims_traced"] = 4  # > total 3
        self.assertTrue(any("claims_traced" in e for e in machine_summary.validate(d)))

    def test_negative_count(self):
        d = self.good(); d["claims_total"] = -1
        self.assertTrue(machine_summary.validate(d))

    def test_findings_verdict_is_valid(self):
        d = self.good(); d["verdict"] = "FINDINGS"
        self.assertEqual(machine_summary.validate(d), [])


class TestMain(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def write(self, text):
        p = self.root / "report.md"
        p.write_text(text, encoding="utf-8")
        return p

    def run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = machine_summary.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_valid_block_check_passes(self):
        p = self.write(VALID_BLOCK)
        code, _, _ = self.run_main([str(p), "--check"])
        self.assertEqual(code, 0)

    def test_invalid_block_check_fails(self):
        p = self.write(VALID_BLOCK.replace("claims_traced: 3", "claims_traced: 9"))
        code, _, err = self.run_main([str(p), "--check"])
        self.assertEqual(code, 1)
        self.assertIn("claims_traced", err)

    def test_absent_block_check_is_ok(self):
        p = self.write("# Report\n\nNo block.\n")
        code, _, _ = self.run_main([str(p), "--check"])
        self.assertEqual(code, 0)  # optional artifact

    def test_json_output(self):
        p = self.write(VALID_BLOCK)
        code, out, _ = self.run_main([str(p), "--json"])
        self.assertEqual(code, 0)
        import json
        self.assertEqual(json.loads(out)["verdict"], "CLEAN")


class TestRealGoldenReport(unittest.TestCase):
    def test_golden_bundle_report_block_is_valid(self):
        repo = Path(machine_summary.__file__).resolve().parents[1]
        report = repo / "eval" / "golden" / "acme-backend" / "bundle" / "report.md"
        summary = machine_summary.parse(report.read_text(encoding="utf-8"))
        self.assertIsNotNone(summary, "golden report should carry a Machine Summary")
        self.assertEqual(machine_summary.validate(summary), [])
        # Consistent with the recorded bundle: CLEAN, 3 fully-traced claims.
        self.assertEqual(summary["verdict"], "CLEAN")
        self.assertEqual(summary["claims_total"], 3)


if __name__ == "__main__":
    unittest.main()

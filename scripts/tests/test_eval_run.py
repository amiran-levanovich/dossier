#!/usr/bin/env python3
"""Tests for eval_run.py — the Tier-1 (zero-LLM) golden-fixture harness.

Run: python3 -m unittest discover scripts/tests

Stdlib only. These test the harness's pure logic with an injected runner, so
they never shell out. The separate test_eval_tier1.py drives the REAL fixtures
through the real subprocess runner and is the regression net that runs in CI.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import eval_run  # noqa: E402


class TmpMixin(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def mkfixture(self, name, has_jd=True):
        d = self.root / name
        d.mkdir(parents=True)
        if has_jd:
            (d / "jd.md").write_text("# fixture\n", encoding="utf-8")
        return d


class TestRender(unittest.TestCase):
    def test_render_prepends_exit_line(self):
        self.assertEqual(eval_run.render(0, "hello\n"), "exit 0\nhello\n")
        self.assertEqual(eval_run.render(1, "boom"), "exit 1\nboom")


class TestDiscover(TmpMixin):
    def test_finds_only_dirs_with_jd(self):
        self.mkfixture("acme", has_jd=True)
        self.mkfixture("beta", has_jd=True)
        self.mkfixture("not-a-fixture", has_jd=False)
        found = [p.name for p in eval_run.discover_fixtures(self.root)]
        self.assertEqual(found, ["acme", "beta"])  # sorted, jd-only

    def test_missing_root_is_empty(self):
        self.assertEqual(eval_run.discover_fixtures(self.root / "nope"), [])


class TestCompareAndBless(TmpMixin):
    def checks(self):
        return [eval_run.Check("ats_coverage", ["ats_coverage.py", "jd.md"])]

    def stub_runner(self, exit_code, out):
        return lambda fixture_dir, check: (exit_code, out)

    def test_missing_expected_is_a_mismatch(self):
        fx = self.mkfixture("acme")
        diffs = eval_run.compare_fixture(fx, self.checks(), self.stub_runner(0, "x\n"))
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0].check, "ats_coverage")

    def test_bless_then_compare_is_clean(self):
        fx = self.mkfixture("acme")
        runner = self.stub_runner(0, "ATS-COVERAGE ...\n  [COVERED] X\n")
        eval_run.bless_fixture(fx, self.checks(), runner)
        # Blessed file exists and round-trips.
        self.assertTrue((fx / "expected" / "ats_coverage.txt").is_file())
        self.assertEqual(eval_run.compare_fixture(fx, self.checks(), runner), [])

    def test_output_drift_is_caught(self):
        fx = self.mkfixture("acme")
        eval_run.bless_fixture(fx, self.checks(), self.stub_runner(0, "old output\n"))
        # A script whose output changed (format/bucketing regression).
        diffs = eval_run.compare_fixture(fx, self.checks(), self.stub_runner(0, "new output\n"))
        self.assertEqual(len(diffs), 1)
        self.assertIn("old output", diffs[0].expected)
        self.assertIn("new output", diffs[0].actual)

    def test_exit_code_drift_is_caught(self):
        fx = self.mkfixture("acme")
        eval_run.bless_fixture(fx, self.checks(), self.stub_runner(0, "same\n"))
        diffs = eval_run.compare_fixture(fx, self.checks(), self.stub_runner(1, "same\n"))
        self.assertEqual(len(diffs), 1)  # exit line differs even though stdout matches


class TestSubprocessRunner(TmpMixin):
    def test_runs_a_real_script_with_fixture_cwd(self):
        # A trivial script that echoes cwd-relative file contents, proving the
        # runner invokes with cwd=fixture and captures stdout + exit code.
        scripts = self.root / "scripts"
        scripts.mkdir()
        (scripts / "echo.py").write_text(
            "import sys,pathlib\n"
            "print('SEEN', pathlib.Path(sys.argv[1]).read_text().strip())\n"
            "sys.exit(3)\n",
            encoding="utf-8",
        )
        fx = self.mkfixture("acme")
        run = eval_run.subprocess_runner(scripts)
        exit_code, out = run(fx, eval_run.Check("echo", ["echo.py", "jd.md"]))
        self.assertEqual(exit_code, 3)
        self.assertIn("SEEN # fixture", out)


if __name__ == "__main__":
    unittest.main()

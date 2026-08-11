#!/usr/bin/env python3
"""Tier-1 regression net: drive the REAL eval fixtures through the REAL
deterministic scripts and assert their output matches the blessed snapshots.

Run: python3 -m unittest discover scripts/tests

This is the check that runs in CI (via unittest discover). If it fails, a
deterministic script's output drifted from its golden — run
`python3 scripts/eval_run.py` to see the exact diff, and `--bless` if the
change was intentional.
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import eval_run  # noqa: E402

REPO_ROOT = Path(eval_run.__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "eval" / "fixtures"


class TestTier1Fixtures(unittest.TestCase):
    def test_fixtures_exist(self):
        self.assertTrue(eval_run.discover_fixtures(FIXTURES), "no Tier-1 fixtures found")

    def test_the_fixtures_cover_every_deterministic_step(self):
        """A net that quietly stopped covering assembly would still pass."""
        self.assertEqual({c.name for c in eval_run.CHECKS},
                         {"cv_map", "cv_build", "cv_build_aliased", "ats_coverage"})

    def test_no_fixture_references_a_retired_artifact(self):
        """Trace files, the claim ledger and `knowledge/` are gone in v4. A
        fixture still carrying one would assert a contract nothing honours."""
        stale = [p for p in FIXTURES.rglob("*")
                 if "trace" in p.name or "ledger" in p.name or p.name == "knowledge"]
        self.assertEqual(stale, [])

    def test_a_deliberate_change_to_a_covered_output_is_caught(self):
        """The net's own regression test. Edit a fixture's exemplar in a copy and
        the harness must report drift — here twice over, since a changed slot
        text also renames its id and the edit plan stops resolving."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = Path(tmp) / "acme-backend"
            shutil.copytree(FIXTURES / "acme-backend", fx)
            exemplar = fx / "master_cv.md"
            exemplar.write_text(
                exemplar.read_text(encoding="utf-8").replace("2M requests/day",
                                                             "40M requests/day"),
                encoding="utf-8")
            run_fn = eval_run.subprocess_runner(REPO_ROOT / "scripts")
            drift = eval_run.compare_fixture(fx, eval_run.CHECKS, run_fn)
            self.assertTrue(drift, "a changed exemplar must be caught as drift")
            self.assertIn("cv_map", {d.check for d in drift})

    def test_no_drift_against_blessed_snapshots(self):
        run_fn = eval_run.subprocess_runner(REPO_ROOT / "scripts")
        drift = []
        for fx in eval_run.discover_fixtures(FIXTURES):
            drift.extend(eval_run.compare_fixture(fx, eval_run.CHECKS, run_fn))
        self.assertEqual(
            drift, [],
            "deterministic-pipeline drift; run `python3 scripts/eval_run.py` for the diff",
        )


if __name__ == "__main__":
    unittest.main()

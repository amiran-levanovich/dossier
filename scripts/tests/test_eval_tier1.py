#!/usr/bin/env python3
"""Tier-1 regression net: drive the REAL eval fixtures through the REAL
deterministic scripts and assert their output matches the blessed snapshots.

Run: python3 -m unittest discover scripts/tests

This is the check that runs in CI (via unittest discover). If it fails, a
deterministic script's output drifted from its golden — run
`python3 scripts/eval_run.py` to see the exact diff, and `--bless` if the
change was intentional.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import eval_run  # noqa: E402

REPO_ROOT = Path(eval_run.__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "eval" / "fixtures"


class TestTier1Fixtures(unittest.TestCase):
    def test_fixtures_exist(self):
        self.assertTrue(eval_run.discover_fixtures(FIXTURES), "no Tier-1 fixtures found")

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

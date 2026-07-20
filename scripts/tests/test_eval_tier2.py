#!/usr/bin/env python3
"""Tier-2 CI check: score the recorded golden bundle(s) against their reference.

Run: python3 -m unittest discover scripts/tests

Scoring a recorded bundle needs no model, so this runs in CI: it guards the
scorer and the internal consistency of each golden case (edit a bundle's traces
without updating reference.json and this fails). Scoring a *fresh* live run is
the on-demand step — see eval/golden/README.md.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import eval_score  # noqa: E402

REPO_ROOT = Path(eval_score.__file__).resolve().parents[1]
GOLDEN = REPO_ROOT / "eval" / "golden"


class TestTier2Golden(unittest.TestCase):
    def cases(self):
        return sorted(p.name for p in GOLDEN.iterdir()
                      if p.is_dir() and (p / "reference.json").is_file())

    def test_at_least_one_case(self):
        self.assertTrue(self.cases(), "no Tier-2 golden cases found")

    def test_recorded_bundles_agree_with_reference(self):
        for case in self.cases():
            with self.subTest(case=case):
                code = eval_score.main(["--case", case, "--golden-root", str(GOLDEN)])
                self.assertEqual(code, 0, f"golden case {case} does not score PASS")


if __name__ == "__main__":
    unittest.main()

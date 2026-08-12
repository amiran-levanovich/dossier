#!/usr/bin/env python3
"""Tier-2 CI check: score the recorded golden bundle(s) against their reference.

Run: python3 -m unittest discover scripts/tests

Scoring a recorded bundle needs no model, so this runs in CI: it guards the
scorer and the internal consistency of each golden case (edit a bundle's cv.md
or exemplar without updating reference.json and this fails). Scoring a *fresh* live run is
the on-demand step — see eval/golden/README.md.
"""

import json
import shutil
import sys
import tempfile
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


class TestOneOffCaseProvesSomething(unittest.TestCase):
    """A golden case that passes whatever you do to it guards nothing.

    The one-off case exists because a declared one-off is the only CV content
    the exemplar's verdict does not cover. If the scorer treated the extra line
    as ordinary drift the case would fail; if it exempted *any* unmatched line
    the case would pass even with the declaration removed. Both are checked.
    """

    CASE = "acme-oneoff"

    def bundle(self):
        return GOLDEN / self.CASE / "bundle"

    def test_the_case_carries_a_declared_one_off(self):
        plan = json.loads((self.bundle() / "plan.json").read_text(encoding="utf-8"))
        self.assertEqual(len(plan.get("one_off", [])), 1)

    def test_removing_the_declaration_fails_the_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "bundle"
            shutil.copytree(self.bundle(), run)
            plan = json.loads((run / "plan.json").read_text(encoding="utf-8"))
            plan.pop("one_off")
            (run / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
            code = eval_score.main(["--case", self.CASE, "--golden-root", str(GOLDEN),
                                    "--run", str(run)])
            self.assertEqual(code, 1, "an undeclared extra line must fail the case")


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Tests for release_audit.py — the enforced version of TOKEN_ECONOMY.md's
release checklist. Run: python3 -m unittest discover scripts/tests

Stdlib only. These tests are the contract. This release covers the two
deterministic, zero-false-positive checks:
  C1  no agent runs on `model: inherit`
  C7  each budgeted doc is at or under its §5 word budget
The §5 budgets are parsed FROM TOKEN_ECONOMY.md so the doc stays the single
source of truth (the script never hard-codes a number).
"""

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import release_audit  # noqa: E402


TOKEN_ECON_SAMPLE = """\
# Token Economy

## 3. Budgets

| Metric | Target | Hard ceiling |
|---|---|---|
| Writer agent, first pass | <= 10 tool calls | 15 |
| WebFetch per application | <= 1 | 2 |

## 5. Doc weight budgets

Some prose about the sweep.

| File | Budget (words) |
|---|---|
| `.claude/agents/*.md` (each) | 800 |
| `job_docs/core/tailoring_method.md` | 1,400 |
| `job_docs/standards/*` (each) | 1,300 |

## 6. Release audit
"""


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
# §5 budget parsing — the single-source-of-truth mechanism
# --------------------------------------------------------------------------
class TestParseBudgets(unittest.TestCase):
    def test_parses_only_section5_backticked_rows(self):
        budgets = dict(release_audit.parse_budgets(TOKEN_ECON_SAMPLE))
        self.assertEqual(budgets[".claude/agents/*.md"], 800)
        self.assertEqual(budgets["job_docs/core/tailoring_method.md"], 1400)
        self.assertEqual(budgets["job_docs/standards/*"], 1300)

    def test_excludes_section3_prose_rows(self):
        globs = [g for g, _ in release_audit.parse_budgets(TOKEN_ECON_SAMPLE)]
        # "Writer agent, first pass" has no backticked path -> not a doc budget.
        self.assertTrue(all("Writer agent" not in g for g in globs))
        self.assertEqual(len(globs), 3)

    def test_strips_thousands_separator(self):
        budgets = dict(release_audit.parse_budgets(TOKEN_ECON_SAMPLE))
        self.assertEqual(budgets["job_docs/core/tailoring_method.md"], 1400)


class TestWordCount(unittest.TestCase):
    def test_matches_wc_w(self):
        self.assertEqual(release_audit.word_count("one two three"), 3)
        self.assertEqual(release_audit.word_count("  spaced \n out\ttokens "), 3)


# --------------------------------------------------------------------------
# C1 — model: inherit
# --------------------------------------------------------------------------
class TestModelInherit(TmpMixin):
    def test_flags_inherit(self):
        self.write(".claude/agents/writer.md", "---\nname: writer\nmodel: inherit\n---\nbody")
        v = release_audit.check_model_inherit(self.root)
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0].check, "C1")

    def test_clean_when_pinned(self):
        self.write(".claude/agents/writer.md", "---\nmodel: sonnet\n---\nbody")
        self.assertEqual(release_audit.check_model_inherit(self.root), [])

    def test_no_agents_dir_is_clean(self):
        self.assertEqual(release_audit.check_model_inherit(self.root), [])


# --------------------------------------------------------------------------
# C7 — doc weight budgets
# --------------------------------------------------------------------------
class TestDocWeights(TmpMixin):
    def budgets(self):
        return [("job_docs/core/tailoring_method.md", 5), ("job_docs/standards/*", 5)]

    def test_flags_over_budget(self):
        self.write("job_docs/core/tailoring_method.md", "one two three four five six")  # 6 > 5
        v = release_audit.check_doc_weights(self.budgets(), self.root)
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0].check, "C7")
        self.assertIn("tailoring_method.md", v[0].path)

    def test_clean_when_under_budget(self):
        self.write("job_docs/core/tailoring_method.md", "one two three")  # 3 <= 5
        self.assertEqual(release_audit.check_doc_weights(self.budgets(), self.root), [])

    def test_glob_checks_each_matched_file(self):
        self.write("job_docs/standards/a.md", "one two three")            # ok
        self.write("job_docs/standards/b.md", "one two three four five six")  # over
        v = release_audit.check_doc_weights(self.budgets(), self.root)
        self.assertEqual([x.path.split("/")[-1] for x in v], ["b.md"])

    def test_missing_budgeted_file_is_not_a_violation(self):
        # A budget for a file that doesn't exist yet simply has nothing to check.
        self.assertEqual(release_audit.check_doc_weights(self.budgets(), self.root), [])


# --------------------------------------------------------------------------
# run_audit + main
# --------------------------------------------------------------------------
class TestMain(TmpMixin):
    def _repo(self, over=False):
        self.write("TOKEN_ECONOMY.md", TOKEN_ECON_SAMPLE)
        self.write(".claude/agents/writer.md", "---\nmodel: sonnet\n---\nbody")
        body = "word " * (1401 if over else 3)
        self.write("job_docs/core/tailoring_method.md", body)

    def run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = release_audit.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_clean_repo_exit_zero(self):
        self._repo(over=False)
        code, _, err = self.run_main(["--root", str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn("pass", err.lower())

    def test_violation_exit_one(self):
        self._repo(over=True)
        code, _, err = self.run_main(["--root", str(self.root)])
        self.assertEqual(code, 1)
        self.assertIn("C7", err)

    def test_json_output(self):
        self._repo(over=True)
        code, out, _ = self.run_main(["--root", str(self.root), "--json"])
        self.assertEqual(code, 1)
        import json
        data = json.loads(out)
        self.assertTrue(any(v["check"] == "C7" for v in data))


if __name__ == "__main__":
    unittest.main()

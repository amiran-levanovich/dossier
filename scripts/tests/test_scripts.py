#!/usr/bin/env python3
"""Tests for the dossier pipeline scripts. Run: python3 -m unittest discover scripts/tests

Uses only the standard library (the amended CLAUDE.md principle allows helper
scripts + their tests, not a third-party test framework).
"""

import csv
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import _common  # noqa: E402
import ats_coverage  # noqa: E402
import session_metrics  # noqa: E402
import tracker  # noqa: E402
import trace_check  # noqa: E402


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


class TestCommon(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(_common.slugify_heading("## Achievements"), "achievements")
        self.assertEqual(_common.slugify_heading("Data & APIs"), "data--apis")

    def test_keyword_pattern_whole_token(self):
        self.assertTrue(_common.keyword_pattern("Go").search("wrote Go services"))
        self.assertFalse(_common.keyword_pattern("Go").search("using Google Cloud"))

    def test_keyword_pattern_punctuated_tech(self):
        self.assertTrue(_common.keyword_pattern("C++").search("strong C++ background"))
        self.assertTrue(_common.keyword_pattern("Node.js").search("built on Node.js here"))


class TestTraceCheck(TmpMixin):
    def _kb(self):
        self.write("knowledge/roles/acme.md", "# Acme\n\n## Achievements\n- did things\n")
        self.write("knowledge/skills.md", "# Skills\n\n## Databases\n- PostgreSQL\n")
        return self.root / "knowledge"

    def test_all_resolve(self):
        kb = self._kb()
        trace = self.write(
            "app/cv_trace.md",
            '- "led work" → roles/acme.md#achievements\n- "db" → skills.md#databases\n',
        )
        n, ok, findings = trace_check.check_file(trace, kb, trace.parent)
        self.assertEqual((n, ok, findings), (2, 2, []))

    def test_missing_file_and_anchor(self):
        kb = self._kb()
        trace = self.write(
            "app/cv_trace.md",
            '- "x" → roles/ghost.md#achievements\n- "y" → skills.md#nosuch\n',
        )
        _, _, findings = trace_check.check_file(trace, kb, trace.parent)
        kinds = sorted(f[1] for f in findings)
        self.assertEqual(kinds, ["ANCHOR", "FILE"])

    def test_override_needs_no_anchor(self):
        kb = self._kb()
        self.write("app/overrides.md", "user-directed: Kafka\n")
        trace = self.write("app/cv_trace.md", '- "kafka" → overrides.md (user-directed, 2026-07-07)\n')
        _, ok, findings = trace_check.check_file(trace, kb, trace.parent)
        self.assertEqual((ok, findings), (1, []))

    def test_arrow_inside_claim_splits_at_last_arrow(self):
        kb = self._kb()
        trace = self.write(
            "app/cv_trace.md",
            '- "migrated Redis → Kafka pipeline" → roles/acme.md#achievements\n',
        )
        n, ok, findings = trace_check.check_file(trace, kb, trace.parent)
        self.assertEqual((n, ok, findings), (1, 1, []))

    def test_malformed_line(self):
        kb = self._kb()
        trace = self.write("app/cv_trace.md", '- "no arrow here"\n')
        _, _, findings = trace_check.check_file(trace, kb, trace.parent)
        self.assertEqual(findings[0][1], "MALFORMED")

    def test_main_exit_code(self):
        kb = self._kb()
        trace = self.write("app/cv_trace.md", '- "x" → roles/ghost.md\n')
        with redirect_stdout(io.StringIO()):
            rc = trace_check.main([str(trace), "--kb-dir", str(kb)])
        self.assertEqual(rc, 1)


class TestAtsCoverage(TmpMixin):
    def test_extract_keywords(self):
        jd = "## Must-haves\n- x\n\n## ATS keywords\n- PostgreSQL, Redis\n- Kafka\n\n## Fit\n- y\n"
        self.assertEqual(ats_coverage.extract_keywords(jd), ["PostgreSQL", "Redis", "Kafka"])

    def test_buckets(self):
        self.write("knowledge/skills.md", "## Databases\n- PostgreSQL deep\n- Kafka [unverified]\n")
        jd = self.root / "jd.md"
        jd.write_text("## ATS keywords\n- PostgreSQL\n- Kafka\n- Terraform\n", encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = ats_coverage.main([str(jd), "--kb-dir", str(self.root / "knowledge")])
        out = buf.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("[COVERED]    PostgreSQL", out)
        self.assertIn("[UNVERIFIED] Kafka", out)
        self.assertIn("[GAP]        Terraform", out)

    def test_lessons_excluded(self):
        self.write("knowledge/lessons.md", "- gammasoft: posting named Sidekiq\n")
        jd = self.root / "jd.md"
        jd.write_text("## ATS keywords\n- Sidekiq\n", encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            ats_coverage.main([str(jd), "--kb-dir", str(self.root / "knowledge")])
        self.assertIn("[GAP]        Sidekiq", buf.getvalue())


class TestTracker(TmpMixin):
    def _rows(self, path):
        with open(path, newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))

    def test_add_creates_with_full_header(self):
        f = self.root / "tracker.csv"
        with redirect_stdout(io.StringIO()):
            rc = tracker.main(["--file", str(f), "add", "--company", "Acme", "--role", "Backend Dev", "--fit-score", "4"])
        self.assertEqual(rc, 0)
        rows = self._rows(f)
        self.assertEqual(rows[0]["company"], "Acme")
        self.assertEqual(rows[0]["status"], "to_apply")
        self.assertEqual(rows[0]["fit_score"], "4")

    def test_quoting_of_commas(self):
        f = self.root / "tracker.csv"
        with redirect_stdout(io.StringIO()):
            tracker.main(["--file", str(f), "add", "--company", "Acme", "--notes", "fast, generic reject"])
        self.assertEqual(self._rows(f)[0]["notes"], "fast, generic reject")

    def test_update_and_terminal_autofills_date_closed(self):
        f = self.root / "tracker.csv"
        with redirect_stdout(io.StringIO()):
            tracker.main(["--file", str(f), "add", "--company", "Acme", "--role", "Dev"])
            rc = tracker.main(["--file", str(f), "update", "--company", "Acme",
                               "--set", "status=rejected", "--set", "stage_reached=screen"])
        self.assertEqual(rc, 0)
        row = self._rows(f)[0]
        self.assertEqual(row["status"], "rejected")
        self.assertTrue(row["date_closed"])  # auto-filled

    def test_ambiguous_update_errors(self):
        f = self.root / "tracker.csv"
        with redirect_stdout(io.StringIO()):
            tracker.main(["--file", str(f), "add", "--company", "Acme", "--role", "A"])
            tracker.main(["--file", str(f), "add", "--company", "Acme", "--role", "B"])
        with redirect_stdout(io.StringIO()):
            rc = tracker.main(["--file", str(f), "update", "--company", "Acme", "--set", "status=applied"])
        self.assertEqual(rc, 1)

    def test_migration_pads_old_header(self):
        f = self.root / "tracker.csv"
        f.write_text("company,role,status\nAcme,Dev,applied\n", encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            tracker.main(["--file", str(f), "update", "--company", "Acme", "--set", "next_action=follow up"])
        rows = self._rows(f)
        self.assertIn("fit_score", rows[0])  # header migrated to full schema
        self.assertEqual(rows[0]["next_action"], "follow up")

    def test_unknown_column_errors(self):
        f = self.root / "tracker.csv"
        with redirect_stdout(io.StringIO()):
            tracker.main(["--file", str(f), "add", "--company", "Acme"])
            rc = tracker.main(["--file", str(f), "update", "--company", "Acme", "--set", "bogus=1"])
        self.assertEqual(rc, 1)


class TestSessionMetrics(TmpMixin):
    def test_counts_and_tokens(self):
        import json
        lines = [
            {"type": "assistant", "message": {"usage": {"input_tokens": 100, "output_tokens": 20,
                "cache_creation_input_tokens": 5, "cache_read_input_tokens": 200},
                "content": [{"type": "tool_use", "name": "Read"},
                            {"type": "tool_use", "name": "WebSearch"},
                            {"type": "tool_use", "name": "Task", "input": {"subagent_type": "cv-tailor"}}]}},
            {"type": "assistant", "isSidechain": True, "message": {"usage": {"output_tokens": 10},
                "content": [{"type": "tool_use", "name": "Grep"}]}},
            {"type": "user", "message": {}},
            "{ broken json",
        ]
        f = self.root / "s.jsonl"
        f.write_text("\n".join(l if isinstance(l, str) else json.dumps(l) for l in lines), encoding="utf-8")
        s = session_metrics.analyze(f)
        self.assertEqual(s["assistant_turns"], 1)
        self.assertEqual(s["sidechain_turns"], 1)
        self.assertEqual(s["web_search"], 1)
        self.assertEqual(s["subagents"]["cv-tailor"], 1)
        self.assertEqual(s["tokens"]["input_tokens"], 100)
        self.assertEqual(s["malformed"], 1)

    def test_usage_deduped_by_message_id(self):
        import json
        # One turn split into two per-block entries sharing message.id — the
        # real transcript shape. Usage must count once; tool calls per block.
        entry = {"type": "assistant", "message": {"id": "msg_1",
            "usage": {"input_tokens": 100, "output_tokens": 20},
            "content": [{"type": "tool_use", "name": "Read"}]}}
        f = self.root / "s.jsonl"
        f.write_text(json.dumps(entry) + "\n" + json.dumps(entry) + "\n", encoding="utf-8")
        s = session_metrics.analyze(f)
        self.assertEqual(s["assistant_turns"], 1)
        self.assertEqual(s["tokens"]["input_tokens"], 100)
        self.assertEqual(s["tools"]["Read"], 2)


if __name__ == "__main__":
    unittest.main()

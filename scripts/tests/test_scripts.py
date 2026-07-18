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
import claim_ledger  # noqa: E402
import master_diff  # noqa: E402
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

    def test_normalize_anchor_tolerant(self):
        # Title case, raw heading text, and single- vs double-hyphen all collapse
        # to one normalised form so a hand-written anchor matches a real slug.
        self.assertEqual(_common.normalize_anchor("Achievements"), "achievements")
        self.assertEqual(_common.normalize_anchor("Data & infra"), "data-infra")
        self.assertEqual(_common.normalize_anchor("data-infra"), "data-infra")
        self.assertEqual(
            _common.normalize_anchor("data--infra"),
            _common.normalize_anchor("Data & infra"),
        )

    def test_keyword_pattern_whole_token(self):
        self.assertTrue(_common.keyword_pattern("Go").search("wrote Go services"))
        self.assertFalse(_common.keyword_pattern("Go").search("using Google Cloud"))

    def test_keyword_pattern_punctuated_tech(self):
        self.assertTrue(_common.keyword_pattern("C++").search("strong C++ background"))
        self.assertTrue(_common.keyword_pattern("Node.js").search("built on Node.js here"))


class TestTraceCheck(TmpMixin):
    def _kb(self):
        self.write(
            "knowledge/roles/acme.md",
            "# Acme\n\n## Achievements\n- did things\n\n## Data & infra\n- pipelines\n",
        )
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

    def test_anchor_case_insensitive(self):
        kb = self._kb()
        trace = self.write("app/cv_trace.md", '- "x" → roles/acme.md#Achievements\n')
        _, ok, findings = trace_check.check_file(trace, kb, trace.parent)
        self.assertEqual((ok, findings), (1, []))

    def test_anchor_raw_heading_and_single_hyphen(self):
        # Raw '#Data & infra' and hand-written '#data-infra' both match the
        # '&'-derived slug 'data--infra'.
        kb = self._kb()
        trace = self.write(
            "app/cv_trace.md",
            '- "a" → roles/acme.md#Data & infra\n- "b" → roles/acme.md#data-infra\n',
        )
        n, ok, findings = trace_check.check_file(trace, kb, trace.parent)
        self.assertEqual((n, ok, findings), (2, 2, []))

    def test_knowledge_prefix_stripped(self):
        kb = self._kb()
        trace = self.write("app/cv_trace.md", '- "x" → knowledge/skills.md#databases\n')
        _, ok, findings = trace_check.check_file(trace, kb, trace.parent)
        self.assertEqual((ok, findings), (1, []))

    def test_app_local_notes_and_jd_resolve_against_app_dir(self):
        kb = self._kb()
        self.write("app/notes.md", "# Notes\n\n## Company\n- funded 2021\n")
        self.write("app/jd.md", "# JD\n\n## Must-haves\n- Rails\n")
        trace = self.write(
            "app/cv_trace.md",
            '- "co" → notes.md#company\n- "req" → jd.md#must-haves\n',
        )
        n, ok, findings = trace_check.check_file(trace, kb, trace.parent)
        self.assertEqual((n, ok, findings), (2, 2, []))

    def test_headingless_file_with_cited_anchor_is_a_finding(self):
        # tailoring_method.md: app-local targets other than overrides.md are
        # anchor-checked. A cited anchor into a heading-less file cannot be
        # verified — that IS a dangling reference, it must not pass silently.
        kb = self._kb()
        self.write("app/notes.md", "just freeform prose, no headings here\n")
        trace = self.write("app/cv_trace.md", '- "x" → notes.md#company\n')
        _, ok, findings = trace_check.check_file(trace, kb, trace.parent)
        self.assertEqual(ok, 0)
        self.assertEqual(findings[0][1], "ANCHOR")

    def test_cv_and_cover_are_not_valid_sources(self):
        # A document cannot source its own claims: cv.md / cover.md never
        # resolve as trace targets, even though they exist in the app folder.
        kb = self._kb()
        self.write("app/cv.md", "# CV\n\n## Experience\n- stuff\n")
        self.write("app/cover.md", "# Cover\n\n## Body\n- text\n")
        trace = self.write(
            "app/cv_trace.md",
            '- "x" → cv.md#experience\n- "y" → cover.md#body\n',
        )
        _, ok, findings = trace_check.check_file(trace, kb, trace.parent)
        self.assertEqual(ok, 0)
        self.assertEqual([f[1] for f in findings], ["FILE", "FILE"])

    def test_near_miss_anchor_still_fails(self):
        # Normalisation tolerates spelling variants of the SAME heading, not
        # references to headings that don't exist.
        kb = self._kb()
        trace = self.write("app/cv_trace.md", '- "x" → roles/acme.md#achievement\n')
        _, ok, findings = trace_check.check_file(trace, kb, trace.parent)
        self.assertEqual(ok, 0)
        self.assertEqual(findings[0][1], "ANCHOR")

    def test_knowledge_prefix_missing_file_still_fails(self):
        kb = self._kb()
        trace = self.write("app/cv_trace.md", '- "x" → knowledge/ghost.md#x\n')
        _, ok, findings = trace_check.check_file(trace, kb, trace.parent)
        self.assertEqual(ok, 0)
        self.assertEqual(findings[0][1], "FILE")

    def test_missing_app_local_target_fails(self):
        kb = self._kb()  # note: no app/notes.md written
        trace = self.write("app/cv_trace.md", '- "x" → notes.md#company\n')
        _, ok, findings = trace_check.check_file(trace, kb, trace.parent)
        self.assertEqual(ok, 0)
        self.assertEqual(findings[0][1], "FILE")

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
        self.write("knowledge/lessons.md", "- examplecorp: posting named Sidekiq\n")
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


class TestClaimLedger(TmpMixin):
    """Contract: on a CLEAN verdict, `record` memoizes (claim text, resolved KB
    source, source content hash); `check` marks exact matches PRE-VERIFIED so
    the verifier judges only new/changed claims. Any drift — claim wording,
    source content, cited anchor — invalidates. Advisory only: exit 0, never a
    gate; missing/corrupt ledger degrades to "everything is NEW"."""

    def _kb(self):
        self.write(
            "knowledge/roles/acme.md",
            "# Acme\n\n## Achievements\n- did things\n\n## Data & infra\n- pipelines\n",
        )
        self.write("knowledge/skills.md", "# Skills\n\n## Databases\n- PostgreSQL\n")
        return self.root / "knowledge"

    def _run(self, cmd, trace, kb, ledger):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = claim_ledger.main(
                [cmd, str(trace), "--kb-dir", str(kb), "--ledger", str(ledger)]
            )
        return rc, buf.getvalue()

    def test_record_then_check_roundtrip_pre_verified(self):
        kb = self._kb()
        ledger = self.root / "ledger.json"
        trace = self.write(
            "app/cv_trace.md",
            '- "led work" → roles/acme.md#achievements\n- "db" → skills.md#databases\n',
        )
        rc, _ = self._run("record", trace, kb, ledger)
        self.assertEqual(rc, 0)
        rc, out = self._run("check", trace, kb, ledger)
        self.assertEqual(rc, 0)
        self.assertIn("pre-verified: 2", out)
        self.assertIn("new: 0", out)

    def test_changed_claim_text_is_new(self):
        kb = self._kb()
        ledger = self.root / "ledger.json"
        trace = self.write("app/cv_trace.md", '- "led work" → roles/acme.md#achievements\n')
        self._run("record", trace, kb, ledger)
        trace2 = self.write("app2/cv_trace.md", '- "led major work" → roles/acme.md#achievements\n')
        _, out = self._run("check", trace2, kb, ledger)
        self.assertIn("pre-verified: 0", out)
        self.assertIn("new: 1", out)

    def test_changed_source_content_invalidates(self):
        kb = self._kb()
        ledger = self.root / "ledger.json"
        trace = self.write("app/cv_trace.md", '- "led work" → roles/acme.md#achievements\n')
        self._run("record", trace, kb, ledger)
        self.write(
            "knowledge/roles/acme.md",
            "# Acme\n\n## Achievements\n- did DIFFERENT things\n\n## Data & infra\n- pipelines\n",
        )
        _, out = self._run("check", trace, kb, ledger)
        self.assertIn("pre-verified: 0", out)
        self.assertIn("source changed", out)

    def test_changed_anchor_is_new(self):
        # Same claim, same file, different cited section — the support moved,
        # so the previous CLEAN judgment does not carry over.
        kb = self._kb()
        ledger = self.root / "ledger.json"
        trace = self.write("app/cv_trace.md", '- "led work" → roles/acme.md#achievements\n')
        self._run("record", trace, kb, ledger)
        trace2 = self.write("app2/cv_trace.md", '- "led work" → roles/acme.md#data--infra\n')
        _, out = self._run("check", trace2, kb, ledger)
        self.assertIn("pre-verified: 0", out)

    def test_app_local_targets_never_pre_verified(self):
        # jd.md / notes.md / overrides.md are per-application by definition —
        # a past CLEAN on another application's files must never carry over.
        kb = self._kb()
        ledger = self.root / "ledger.json"
        self.write("app/notes.md", "# Notes\n\n## Company\n- funded 2021\n")
        trace = self.write("app/cv_trace.md", '- "funded" → notes.md#company\n')
        rc, out = self._run("record", trace, kb, ledger)
        self.assertEqual(rc, 0)
        self.assertIn("skipped (app-local): 1", out)
        _, out = self._run("check", trace, kb, ledger)
        self.assertIn("pre-verified: 0", out)
        self.assertIn("app-local", out)

    def test_unresolved_target_not_recorded(self):
        # record runs post-CLEAN so this shouldn't happen — but a dangling
        # target must degrade to "not recorded", never crash or poison entries.
        kb = self._kb()
        ledger = self.root / "ledger.json"
        trace = self.write("app/cv_trace.md", '- "x" → roles/ghost.md#achievements\n')
        rc, out = self._run("record", trace, kb, ledger)
        self.assertEqual(rc, 0)
        self.assertIn("skipped (unresolved): 1", out)
        self.assertIn("recorded: 0", out)

    def test_missing_ledger_all_new_exit_zero(self):
        kb = self._kb()
        trace = self.write("app/cv_trace.md", '- "led work" → roles/acme.md#achievements\n')
        rc, out = self._run("check", trace, kb, self.root / "nope.json")
        self.assertEqual(rc, 0)
        self.assertIn("pre-verified: 0", out)
        self.assertIn("new: 1", out)

    def test_corrupt_ledger_treated_as_empty(self):
        kb = self._kb()
        ledger = self.write("ledger.json", "{ not json at all")
        trace = self.write("app/cv_trace.md", '- "led work" → roles/acme.md#achievements\n')
        rc, out = self._run("check", trace, kb, ledger)
        self.assertEqual(rc, 0)
        self.assertIn("new: 1", out)
        # ...and record must recover by rewriting a valid ledger.
        rc, _ = self._run("record", trace, kb, ledger)
        self.assertEqual(rc, 0)
        _, out = self._run("check", trace, kb, ledger)
        self.assertIn("pre-verified: 1", out)

    def test_record_merges_across_applications(self):
        # A second application's record must extend the ledger, not wipe the
        # first application's entries.
        kb = self._kb()
        ledger = self.root / "ledger.json"
        t1 = self.write("app1/cv_trace.md", '- "led work" → roles/acme.md#achievements\n')
        t2 = self.write("app2/cv_trace.md", '- "db" → skills.md#databases\n')
        self._run("record", t1, kb, ledger)
        self._run("record", t2, kb, ledger)
        _, out = self._run("check", t1, kb, ledger)
        self.assertIn("pre-verified: 1", out)
        _, out = self._run("check", t2, kb, ledger)
        self.assertIn("pre-verified: 1", out)

    def test_knowledge_prefix_and_anchor_variants_hit_same_entry(self):
        # `knowledge/skills.md#Databases` and `skills.md#databases` are the
        # same source — resolution + anchor normalisation happen before hashing.
        kb = self._kb()
        ledger = self.root / "ledger.json"
        t1 = self.write("app1/cv_trace.md", '- "db" → knowledge/skills.md#Databases\n')
        t2 = self.write("app2/cv_trace.md", '- "db" → skills.md#databases\n')
        self._run("record", t1, kb, ledger)
        _, out = self._run("check", t2, kb, ledger)
        self.assertIn("pre-verified: 1", out)

    def test_default_ledger_lives_beside_kb(self):
        # No --ledger flag: the ledger sits next to knowledge/ (job-folder
        # root), shared across every application of that job search.
        kb = self._kb()
        trace = self.write("app/cv_trace.md", '- "led work" → roles/acme.md#achievements\n')
        with redirect_stdout(io.StringIO()):
            rc = claim_ledger.main(["record", str(trace), "--kb-dir", str(kb)])
        self.assertEqual(rc, 0)
        self.assertTrue((kb.parent / ".claim_ledger.json").is_file())

    def test_missing_kb_dir_is_an_io_error(self):
        trace = self.write("app/cv_trace.md", '- "x" → skills.md#databases\n')
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = claim_ledger.main(["check", str(trace), "--kb-dir", str(self.root / "ghost")])
        self.assertEqual(rc, 2)


class TestMasterDiff(TmpMixin):
    """Contract: every content-bearing line of cv.md is either VERBATIM
    (present in master_cv.md, whitespace-normalized) or CHANGED — no semantic
    tolerance, a 95%-similar rewording is CHANGED and gets judged. Advisory:
    exit 0 even with changes; missing master degrades to "everything CHANGED"
    (= v2.4.0 behavior, full judgment)."""

    MASTER = (
        "# CV\n\n## Experience\n"
        "- Built the billing pipeline serving 2M users\n"
        "- Contributed to the Kafka migration\n"
        "- Led a team of 3 engineers\n"
        "\n## Skills\n- Ruby on Rails, PostgreSQL\n"
    )

    def _run(self, cv_text, master_text=MASTER):
        cv = self.write("app/cv.md", cv_text)
        master = self.write("master_cv.md", master_text) if master_text else self.root / "ghost.md"
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = master_diff.main([str(cv), "--master", str(master)])
        return rc, buf.getvalue()

    def test_verbatim_subset_with_reorder_is_clean(self):
        # Subtraction + reordering is the tailor's job — dropped bullets and a
        # new order must not count as changes.
        rc, out = self._run(
            "# CV\n\n## Experience\n"
            "- Led a team of 3 engineers\n"
            "- Built the billing pipeline serving 2M users\n"
        )
        self.assertEqual(rc, 0)
        self.assertIn("verbatim: 2", out)
        self.assertIn("changed: 0", out)

    def test_reworded_bullet_is_changed_even_when_close(self):
        rc, out = self._run(
            "## Experience\n- Built the billing pipeline serving 3M users\n"
        )
        self.assertEqual(rc, 0)
        self.assertIn("changed: 1", out)
        self.assertIn("[CHANGED]", out)

    def test_changed_line_reports_closest_master_line(self):
        _, out = self._run("## Experience\n- Led a team of 5 engineers\n")
        self.assertIn("Led a team of 3 engineers", out)

    def test_new_bullet_reports_no_close_match(self):
        _, out = self._run("## Experience\n- Certified Kubernetes administrator since 2024\n")
        self.assertIn("changed: 1", out)
        self.assertIn("no close match", out)

    def test_whitespace_and_bullet_marker_drift_is_verbatim(self):
        rc, out = self._run(
            "## Skills\n*   Ruby on Rails,   PostgreSQL\n"
        )
        self.assertEqual(rc, 0)
        self.assertIn("verbatim: 1", out)
        self.assertIn("changed: 0", out)

    def test_headings_and_blanks_are_not_compared(self):
        # A tailored section heading must not show up as a CHANGED line.
        _, out = self._run("# Tailored CV\n\n## Core experience\n- Contributed to the Kafka migration\n")
        self.assertIn("lines: 1", out)
        self.assertIn("verbatim: 1", out)

    def test_missing_master_all_changed_exit_zero(self):
        rc, out = self._run("## Experience\n- Built the billing pipeline serving 2M users\n", master_text=None)
        self.assertEqual(rc, 0)
        self.assertIn("changed: 1", out)
        self.assertIn("no master", out)

    def test_missing_cv_is_an_io_error(self):
        master = self.write("master_cv.md", self.MASTER)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = master_diff.main([str(self.root / "nope.md"), "--master", str(master)])
        self.assertEqual(rc, 2)


class TestClaimLedgerDocuments(TmpMixin):
    """Contract: `record --document` stores a verified document's content hash
    on CLEAN; `check --document` answers whether the file is still exactly the
    one that was verified. Any edit → CHANGED until re-verified. Keyed by
    basename (the exemplars live at the job-folder root beside the ledger)."""

    def _kb(self):
        self.write("knowledge/skills.md", "# Skills\n\n## Databases\n- PostgreSQL\n")
        return self.root / "knowledge"

    def _run(self, args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = claim_ledger.main(args)
        return rc, buf.getvalue()

    def test_record_then_check_document_verified(self):
        kb = self._kb()
        ledger = self.root / "ledger.json"
        master = self.write("master_cv.md", "# CV\n- Built things\n")
        rc, _ = self._run(["record", "--document", str(master), "--kb-dir", str(kb), "--ledger", str(ledger)])
        self.assertEqual(rc, 0)
        rc, out = self._run(["check", "--document", str(master), "--kb-dir", str(kb), "--ledger", str(ledger)])
        self.assertEqual(rc, 0)
        self.assertIn("VERIFIED", out)

    def test_document_edit_invalidates(self):
        kb = self._kb()
        ledger = self.root / "ledger.json"
        master = self.write("master_cv.md", "# CV\n- Built things\n")
        self._run(["record", "--document", str(master), "--kb-dir", str(kb), "--ledger", str(ledger)])
        self.write("master_cv.md", "# CV\n- Built DIFFERENT things\n")
        _, out = self._run(["check", "--document", str(master), "--kb-dir", str(kb), "--ledger", str(ledger)])
        self.assertIn("CHANGED", out)
        self.assertNotIn("VERIFIED", out.replace("CHANGED", ""))

    def test_unrecorded_document_reported(self):
        kb = self._kb()
        master = self.write("master_cv.md", "# CV\n- Built things\n")
        rc, out = self._run(["check", "--document", str(master), "--kb-dir", str(kb),
                             "--ledger", str(self.root / "ledger.json")])
        self.assertEqual(rc, 0)
        self.assertIn("not recorded", out)

    def test_documents_and_traces_combine_in_one_call(self):
        kb = self._kb()
        ledger = self.root / "ledger.json"
        master = self.write("master_cv.md", "# CV\n- db work\n")
        trace = self.write("app/cv_trace.md", '- "db work" → skills.md#databases\n')
        rc, _ = self._run(["record", str(trace), "--document", str(master),
                           "--kb-dir", str(kb), "--ledger", str(ledger)])
        self.assertEqual(rc, 0)
        _, out = self._run(["check", str(trace), "--document", str(master),
                            "--kb-dir", str(kb), "--ledger", str(ledger)])
        self.assertIn("pre-verified: 1", out)
        self.assertIn("VERIFIED", out)

    def test_no_traces_and_no_document_is_usage_error(self):
        kb = self._kb()
        rc, _ = self._run(["check", "--kb-dir", str(kb), "--ledger", str(self.root / "l.json")])
        self.assertEqual(rc, 2)

    def test_v240_ledger_without_documents_key_still_works(self):
        # Backwards compatibility: a ledger written by v2.4.0 has only
        # "entries" — trace checks keep working, document checks degrade to
        # "not recorded".
        kb = self._kb()
        ledger = self.root / "ledger.json"
        trace = self.write("app/cv_trace.md", '- "db work" → skills.md#databases\n')
        self._run(["record", str(trace), "--kb-dir", str(kb), "--ledger", str(ledger)])
        import json
        data = json.loads(ledger.read_text(encoding="utf-8"))
        data.pop("documents", None)
        ledger.write_text(json.dumps(data), encoding="utf-8")
        master = self.write("master_cv.md", "# CV\n")
        rc, out = self._run(["check", str(trace), "--document", str(master),
                             "--kb-dir", str(kb), "--ledger", str(ledger)])
        self.assertEqual(rc, 0)
        self.assertIn("pre-verified: 1", out)
        self.assertIn("not recorded", out)


if __name__ == "__main__":
    unittest.main()

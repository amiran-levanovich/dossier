#!/usr/bin/env python3
"""Tests for the dossier pipeline scripts. Run: python3 -m unittest discover scripts/tests

Uses only the standard library (the amended CLAUDE.md principle allows helper
scripts + their tests, not a third-party test framework).
"""

import contextlib
import csv
import io
import json
import re
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

class TestAtsCoverage(TmpMixin):
    """Three-way bucketing over the exemplar and the story bank (ADR-0006, #28).

    The three buckets carry the distinction the candidate actually acts on:
    covered is usable now, promotable is a promotion decision, and only a gap
    feeds the fit score instead of the writing.
    """

    EXEMPLAR = (
        "# Jane Smith\n"
        "Senior Ruby Engineer\n\n"
        "## Experience\n"
        "- Built a Rails API serving 2M requests/day.\n\n"
        "## Skills\n"
        "- PostgreSQL, Redis.\n"
    )
    BANK = (
        "# Story bank\n\n"
        "At Acme I ran the Kubernetes migration over two quarters.\n"
        "We also trialled Go for one service and dropped it.\n"
    )

    def setup_case(self, keywords, exemplar=None, bank=None):
        jd = self.write("jd.md", "## ATS keywords\n" + "".join(f"- {k}\n" for k in keywords))
        ex = self.write("master_cv.md", self.EXEMPLAR if exemplar is None else exemplar)
        bk = self.write("story_bank.md", self.BANK if bank is None else bank)
        return jd, ex, bk

    def run_coverage(self, argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = ats_coverage.main(argv)
        return rc, buf.getvalue()

    def coverage(self, keywords, **kw):
        jd, ex, bk = self.setup_case(keywords, **kw)
        return self.run_coverage([str(jd), "--exemplar", str(ex), "--bank", str(bk)])

    def test_extract_keywords(self):
        jd = "## Must-haves\n- x\n\n## ATS keywords\n- PostgreSQL, Redis\n- Kafka\n\n## Fit\n- y\n"
        self.assertEqual(ats_coverage.extract_keywords(jd), ["PostgreSQL", "Redis", "Kafka"])

    def test_a_keyword_in_the_exemplar_is_covered(self):
        rc, out = self.coverage(["PostgreSQL"])
        self.assertEqual(rc, 0)
        self.assertIn("[COVERED]    PostgreSQL", out)

    def test_a_keyword_in_the_bank_but_not_the_exemplar_is_promotable(self):
        _, out = self.coverage(["Kubernetes"])
        self.assertIn("[PROMOTABLE] Kubernetes", out)

    def test_a_keyword_in_neither_is_a_gap(self):
        _, out = self.coverage(["Terraform"])
        self.assertIn("[GAP]        Terraform", out)

    def test_the_exemplar_wins_when_both_name_it(self):
        """The bucket answers "is this usable now", so a fact already on the
        exemplar is covered no matter how much the bank says about it."""
        _, out = self.coverage(["Rails"], bank="Rails, Rails, Rails.\n")
        self.assertIn("[COVERED]    Rails", out)
        self.assertNotIn("PROMOTABLE", out)

    def test_covered_names_the_exemplar_sections_it_was_found_in(self):
        """Whether a keyword sits in an achievement or only in a skills list is
        the difference between evidence and assertion."""
        _, out = self.coverage(["Rails", "Redis"])
        self.assertIn("[COVERED]    Rails — Experience", out)
        self.assertIn("[COVERED]    Redis — Skills", out)

    def test_a_keyword_above_the_first_section_is_still_covered(self):
        """The headline carries keywords and belongs to no `##` section, so the
        locator must not be what decides the bucket."""
        _, out = self.coverage(["Senior"])
        self.assertIn("[COVERED]    Senior", out)

    def test_promotable_locates_the_passage_in_the_bank(self):
        _, out = self.coverage(["Kubernetes"])
        self.assertIn("story_bank.md:3", out)

    def test_matching_is_whole_token_and_case_insensitive(self):
        _, out = self.coverage(["Rail", "redis"])
        self.assertIn("[GAP]        Rail", out)
        self.assertIn("[COVERED]    redis", out)

    def test_a_bank_directory_is_read_whole(self):
        jd = self.write("jd.md", "## ATS keywords\n- Sidekiq\n")
        ex = self.write("master_cv.md", self.EXEMPLAR)
        self.write("bank/roles.md", "Ran Sidekiq queues at Acme.\n")
        rc, out = self.run_coverage([str(jd), "--exemplar", str(ex),
                                     "--bank", str(self.root / "bank")])
        self.assertEqual(rc, 0)
        self.assertIn("[PROMOTABLE] Sidekiq", out)
        self.assertIn("roles.md:1", out)

    def test_many_bank_mentions_are_capped(self):
        """A locator list is a pointer, not a concordance."""
        bank = "".join(f"Line {i} mentions Kafka.\n" for i in range(10))
        _, out = self.coverage(["Kafka"], bank=bank)
        self.assertIn("+7 more", out)

    def test_a_missing_exemplar_is_an_input_error(self):
        jd = self.write("jd.md", "## ATS keywords\n- Ruby\n")
        bk = self.write("story_bank.md", self.BANK)
        rc, _ = self.run_coverage([str(jd), "--exemplar", str(self.root / "nope.md"),
                                   "--bank", str(bk)])
        self.assertEqual(rc, 2)

    def test_a_missing_bank_is_an_input_error(self):
        jd = self.write("jd.md", "## ATS keywords\n- Ruby\n")
        ex = self.write("master_cv.md", self.EXEMPLAR)
        rc, _ = self.run_coverage([str(jd), "--exemplar", str(ex),
                                   "--bank", str(self.root / "nope.md")])
        self.assertEqual(rc, 2)

    def test_a_jd_with_no_keyword_block_says_so(self):
        jd = self.write("jd.md", "# Beta — Backend Developer\n")
        ex = self.write("master_cv.md", self.EXEMPLAR)
        bk = self.write("story_bank.md", self.BANK)
        rc, out = self.run_coverage([str(jd), "--exemplar", str(ex), "--bank", str(bk)])
        self.assertEqual(rc, 0)
        self.assertIn("no keywords found", out)

    def test_a_keyword_the_exemplar_spells_differently_is_still_covered(self):
        """The seam between #27 and #28. Assembly already swaps in the posting's
        spelling, so a posting asking for "Postgres" against an exemplar saying
        "PostgreSQL" is covered — reporting it as a gap would lower the fit score
        for a keyword the delivered CV does match, and prompt a promotion for a
        fact already on the exemplar."""
        _, out = self.coverage(["Postgres"])
        self.assertIn("[COVERED]    Postgres", out)
        self.assertIn('as "PostgreSQL"', out)

    def test_an_alias_match_in_the_bank_is_promotable(self):
        _, out = self.coverage(["K8s"])
        self.assertIn("[PROMOTABLE] K8s", out)
        self.assertIn('as "Kubernetes"', out)

    def test_a_literal_match_is_not_annotated_as_an_alias(self):
        _, out = self.coverage(["PostgreSQL"])
        self.assertIn("[COVERED]    PostgreSQL — Skills", out)
        self.assertNotIn("as \"", out)

    def test_no_alias_reaches_across_groups(self):
        _, out = self.coverage(["MySQL"])
        self.assertIn("[GAP]        MySQL", out)

    # ----- inflection: the posting's plural against the candidate's singular ---

    def test_a_plural_keyword_matches_the_singular_the_bank_uses(self):
        """The defect from the first live run: the posting asked for
        "migrations" against a bank telling a migration story, and the report
        said GAP — a keyword the candidate demonstrably has, depressing the fit
        score and hiding a promotion."""
        _, out = self.coverage(["migrations"])
        self.assertIn("[PROMOTABLE] migrations", out)
        self.assertIn('as "migration"', out)

    def test_a_singular_keyword_matches_the_plural_the_exemplar_uses(self):
        _, out = self.coverage(["request"], exemplar=self.EXEMPLAR)
        self.assertIn("[COVERED]    request", out)
        self.assertIn('as "requests"', out)

    def test_inflection_applies_to_the_last_word_of_a_phrase(self):
        _, out = self.coverage(["Rails APIs"], exemplar=self.EXEMPLAR)
        self.assertIn("[COVERED]    Rails APIs", out)

    def test_a_word_absent_from_both_is_still_a_gap(self):
        """The report must not start matching loosely: these are the run's own
        genuinely-absent domain words, and they carry the fit score."""
        for word in ("settlement", "settlements", "freight", "monolith"):
            with self.subTest(word=word):
                _, out = self.coverage([word])
                self.assertIn("[GAP]", out)

    def test_a_technology_name_is_never_inflected(self):
        """`Rails` minus its s is `Rail`, which would fire on ordinary prose.
        Names the alias table knows are spellings, not vocabulary — inflecting
        them can only produce false matches."""
        self.assertEqual(ats_coverage.inflections("Rails", [["Ruby on Rails", "Rails"]]), [])

    def test_short_words_are_not_inflected(self):
        self.assertEqual(ats_coverage.inflections("Go", []), [])

    def test_es_and_y_plurals(self):
        self.assertIn("index", ats_coverage.inflections("indexes", []))
        self.assertIn("repositories", ats_coverage.inflections("repository", []))
        self.assertIn("repository", ats_coverage.inflections("repositories", []))

    def test_an_alias_carrying_uppercase_does_not_fire_on_prose(self):
        """`Go` must not match "decided to go with", or the report would call a
        gap covered — the worse direction of the two."""
        _, out = self.coverage(["Golang"], exemplar=self.EXEMPLAR + "- Decided to go with SQS.\n",
                               bank="Nothing relevant here.\n")
        self.assertIn("[GAP]        Golang", out)

    def test_a_user_alias_extension_is_honoured(self):
        jd, ex, bk = self.setup_case(["Moby"], exemplar="# CV\n\n## Skills\n- Docker.\n")
        ext = self.write("alias_groups.md", "## Alias groups\n- Docker, Moby\n")
        rc, out = self.run_coverage([str(jd), "--exemplar", str(ex), "--bank", str(bk),
                                     "--aliases", str(ext)])
        self.assertEqual(rc, 0)
        self.assertIn("[COVERED]    Moby", out)

    def test_a_mistyped_alias_table_warns_and_loses_only_its_own_spellings(self):
        """Coverage is advisory. Dying on a mistyped table would block the report
        the orchestrator is waiting on, and discarding the shipped table with it
        would turn one typo into a page of false gaps."""
        jd, ex, bk = self.setup_case(["Postgres", "pg"])
        ext = self.write("mine.md", "Postgres, pg\n")  # no `## Alias groups`
        rc, out = self.run_coverage([str(jd), "--exemplar", str(ex), "--bank", str(bk),
                                     "--aliases", str(ext)])
        self.assertEqual(rc, 0)
        self.assertIn("warning:", out)
        self.assertIn("[COVERED]    Postgres", out)   # shipped table still applies
        self.assertIn("[GAP]        pg", out)         # only the extension's spelling is lost

    def test_the_knowledge_directory_argument_is_gone(self):
        """v4 has no knowledge/ to point at, so the old flag must fail loudly
        rather than be quietly accepted and ignored."""
        jd, ex, bk = self.setup_case(["Ruby"])
        with self.assertRaises(SystemExit):
            with redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                ats_coverage.main([str(jd), "--kb-dir", str(self.root)])


class TestSessionMetricsDispatches(TmpMixin):
    """Per-dispatch subagent usage, read from the Agent tool's own result.

    Subagent turns never appear in a transcript as turns (`isSidechain` entries
    are the main session's view), which is why ADR-0003's saving went unmeasured.
    The Agent tool result carries the agent's own totals, so the measurement is
    available after all — from the result, not from the turns.
    """

    def transcript(self, *results):
        lines = []
        for i, r in enumerate(results):
            lines.append(json.dumps({
                "type": "assistant",
                "message": {"id": f"m{i}", "content": [
                    {"type": "tool_use", "id": f"t{i}", "name": "Agent",
                     "input": {"subagent_type": r["agentType"]}}]},
            }))
            lines.append(json.dumps({
                "type": "user",
                "message": {"content": [{"type": "tool_result", "tool_use_id": f"t{i}"}]},
                "toolUseResult": r,
            }))
        return self.write("session.jsonl", "\n".join(lines) + "\n")

    def result(self, agent="application-writer", tokens=48437, tool_uses=10,
               ms=122299, model="claude-sonnet-5", status="completed"):
        return {"agentId": "a1", "agentType": agent, "status": status,
                "totalTokens": tokens, "totalToolUseCount": tool_uses,
                "totalDurationMs": ms, "resolvedModel": model}

    def test_a_dispatch_reports_its_own_usage(self):
        s = session_metrics.analyze(self.transcript(self.result()))
        self.assertEqual(len(s["dispatches"]), 1)
        d = s["dispatches"][0]
        self.assertEqual(d["agent"], "application-writer")
        self.assertEqual(d["tokens"], 48437)
        self.assertEqual(d["tool_uses"], 10)
        self.assertEqual(d["duration_ms"], 122299)
        self.assertEqual(d["model"], "claude-sonnet-5")

    def test_dispatches_keep_their_order_and_sum(self):
        s = session_metrics.analyze(self.transcript(
            self.result(),
            self.result(agent="application-verifier", tokens=32404, tool_uses=7, ms=139074)))
        self.assertEqual([d["agent"] for d in s["dispatches"]],
                         ["application-writer", "application-verifier"])
        self.assertEqual(sum(d["tokens"] for d in s["dispatches"]), 80841)

    def test_a_result_without_agent_usage_is_not_a_dispatch(self):
        line = json.dumps({"type": "user", "toolUseResult": {"stdout": "hi"},
                           "message": {"content": []}})
        p = self.write("session.jsonl", line + "\n")
        self.assertEqual(session_metrics.analyze(p)["dispatches"], [])

    def test_the_report_names_each_dispatch(self):
        s = session_metrics.analyze(self.transcript(self.result()))
        buf = io.StringIO()
        with redirect_stdout(buf):
            session_metrics.report(Path("session.jsonl"), s)
        out = buf.getvalue()
        self.assertIn("application-writer", out)
        self.assertIn("48,437", out)

    def test_a_transcript_with_no_dispatches_says_so_without_a_dispatch_block(self):
        p = self.write("session.jsonl", json.dumps(
            {"type": "assistant", "message": {"id": "m", "content": []}}) + "\n")
        s = session_metrics.analyze(p)
        buf = io.StringIO()
        with redirect_stdout(buf):
            session_metrics.report(Path("session.jsonl"), s)
        self.assertNotIn("dispatch tokens", buf.getvalue())


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
                            {"type": "tool_use", "name": "Task", "input": {"subagent_type": "application-writer"}}]}},
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
        self.assertEqual(s["subagents"]["application-writer"], 1)
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

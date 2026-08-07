#!/usr/bin/env python3
"""Tests for the consolidated CV module. Run: python3 -m unittest discover scripts/tests

Contract (ADR-0004, ADR-0005): the exemplar is verified once, so an application
CV is trustworthy exactly to the degree that it is *unchanged* from the
exemplar. `map` hands the writer an addressable view; `build` renders the slots
the writer kept and then proves, against the exemplar's own text rather than
against its own intermediate state, that nothing was altered on the way out.

The rejection tests all assert that **no file was written**, not merely that the
exit code was non-zero: a partially assembled CV would read as complete and go
out missing content, which is the failure this module refuses to allow.
"""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv  # noqa: E402

EXEMPLAR = (
    "# Jane Smith\n"
    "Senior Backend Engineer\n\n"
    "Berlin, Germany · jane@example.com\n\n"
    "## Summary\n"
    "Ten years building payment systems.\n\n"
    "## Experience\n\n"
    "### Senior Engineer — Acme, Berlin\n"
    "06/2021 – present\n"
    "*B2B SaaS for hotel operations, ~80 people*\n\n"
    "- Built the billing pipeline serving 2M users\n"
    "- Cut p95 latency from 400ms to 90ms\n\n"
    "### Engineer — Beta, Munich\n"
    "01/2018 – 05/2021\n"
    "*Logistics marketplace, ~200 people*\n\n"
    "- Contributed to the Kafka migration\n\n"
    "## Skills\n"
    "**Backend:** Ruby, Rails, PostgreSQL\n"
    "**Infra:** Docker, Kubernetes\n"
)


class CvCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.out_dir = self.root / "app"

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def run_cv(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = cv.main(argv)
        return rc, out.getvalue() + err.getvalue()

    def slot_map(self, text=EXEMPLAR, name="master_cv.md"):
        exemplar = self.write(name, text)
        out_path = self.root / "slots.json"
        rc, report = self.run_cv(["map", str(exemplar), "--out", str(out_path)])
        self.assertEqual(rc, 0, report)
        return json.loads(out_path.read_text(encoding="utf-8"))

    def ids(self, smap):
        """kind → ordered slot ids, for readable plan construction in tests."""
        out = {}
        for block in smap["blocks"]:
            out.setdefault(block["kind"], []).append(block["id"])
        return out

    def block_by_company(self, smap, company):
        for block in smap["blocks"]:
            if block.get("company") == company:
                return block
        raise AssertionError(f"no block for {company}")

    def build(self, plan, exemplar_text=EXEMPLAR):
        exemplar = self.write("master_cv.md", exemplar_text)
        plan_path = self.write("plan.json", json.dumps(plan))
        return self.run_cv(["build", str(plan_path), "--exemplar", str(exemplar),
                            "--out-dir", str(self.out_dir)])

    def assertNothingWritten(self):
        # Not just "no cv.md" — nothing at all. A rejected build that left a
        # report or a partial file behind would be picked up by the next step
        # as though it had succeeded.
        produced = sorted(p.name for p in self.out_dir.iterdir()) if self.out_dir.exists() else []
        self.assertEqual(produced, [], "a rejected plan must write no files at all")


class TestMap(CvCase):
    def test_blocks_and_bullets_decompose(self):
        smap = self.slot_map()
        exp = [b for b in smap["blocks"] if b["kind"] == "experience"]
        self.assertEqual(len(exp), 2)
        self.assertEqual(exp[0]["company"], "Acme")
        self.assertEqual(exp[0]["dates"], "06/2021 – present")
        self.assertEqual([b["text"] for b in exp[0]["bullets"]],
                         ["Built the billing pipeline serving 2M users",
                          "Cut p95 latency from 400ms to 90ms"])

    def test_bullet_ids_are_reachable_only_through_their_block(self):
        smap = self.slot_map()
        top_level = {b["id"] for b in smap["blocks"]}
        for block in smap["blocks"]:
            for bullet in block.get("bullets", []):
                self.assertNotIn(bullet["id"], top_level)

    def test_editing_one_slot_renames_only_that_slot(self):
        before = self.slot_map()
        after = self.slot_map(
            EXEMPLAR.replace("400ms to 90ms", "400ms to 75ms"), name="other.md")

        def flat(smap):
            out = set()
            for block in smap["blocks"]:
                out.add(block["id"])
                out.update(b["id"] for b in block.get("bullets", []))
            return out

        self.assertEqual(len(flat(before) - flat(after)), 1)

    def test_slot_map_carries_no_trace_targets(self):
        smap = self.slot_map()
        for block in smap["blocks"]:
            self.assertNotIn("trace", block)
            for bullet in block.get("bullets", []):
                self.assertNotIn("trace", bullet)

    def test_undecomposable_exemplar_is_refused_loudly(self):
        exemplar = self.write("plain.md", "Just some prose about a career.\n")
        out_path = self.root / "slots.json"
        rc, report = self.run_cv(["map", str(exemplar), "--out", str(out_path)])
        self.assertEqual(rc, 1)
        self.assertIn("no slots", report)
        self.assertFalse(out_path.exists(), "a refused exemplar must write no slot map")

    def test_missing_exemplar_is_a_usage_error(self):
        rc, _ = self.run_cv(["map", str(self.root / "nope.md")])
        self.assertEqual(rc, 2)


class TestBuildHappyPath(CvCase):
    def test_keep_only_plan_is_fully_verbatim(self):
        smap = self.slot_map()
        acme = self.block_by_company(smap, "Acme")
        plan = {"order": [
            {"id": self.ids(smap)["headline"][0]},
            {"id": self.ids(smap)["summary"][0]},
            {"id": acme["id"], "bullets": [b["id"] for b in acme["bullets"]]},
        ]}
        rc, report = self.build(plan)
        self.assertEqual(rc, 0, report)
        text = (self.out_dir / "cv.md").read_text(encoding="utf-8")
        self.assertIn("Built the billing pipeline serving 2M users", text)
        self.assertIn("Ten years building payment systems.", text)
        # headline, contact, summary, dates, descriptor, two bullets.
        self.assertIn("verbatim: 7/7", report)

    def test_reorder_changes_document_order_and_stays_verbatim(self):
        smap = self.slot_map()
        acme, beta = self.block_by_company(smap, "Acme"), self.block_by_company(smap, "Beta")
        plan = {"order": [
            {"id": beta["id"], "bullets": [b["id"] for b in beta["bullets"]]},
            {"id": acme["id"], "bullets": [b["id"] for b in acme["bullets"]]},
        ]}
        rc, report = self.build(plan)
        self.assertEqual(rc, 0, report)
        text = (self.out_dir / "cv.md").read_text(encoding="utf-8")
        self.assertLess(text.index("Beta"), text.index("Acme"))
        self.assertIn("changed: 0", report)

    def test_dropping_a_bullet_removes_it_and_keeps_its_siblings(self):
        smap = self.slot_map()
        acme = self.block_by_company(smap, "Acme")
        plan = {"order": [{"id": acme["id"], "bullets": [acme["bullets"][0]["id"]]}],
                "drop": [acme["bullets"][1]["id"]]}
        rc, report = self.build(plan)
        self.assertEqual(rc, 0, report)
        text = (self.out_dir / "cv.md").read_text(encoding="utf-8")
        self.assertIn("Built the billing pipeline", text)
        self.assertNotIn("Cut p95 latency", text)

    def test_no_trace_file_is_ever_written(self):
        smap = self.slot_map()
        acme = self.block_by_company(smap, "Acme")
        rc, _ = self.build({"order": [{"id": acme["id"], "bullets": []}]})
        self.assertEqual(rc, 0)
        self.assertEqual(sorted(p.name for p in self.out_dir.iterdir()), ["cv.md"])

    def test_report_measures_the_document(self):
        smap = self.slot_map()
        acme = self.block_by_company(smap, "Acme")
        _, report = self.build({"order": [{"id": acme["id"],
                                           "bullets": [b["id"] for b in acme["bullets"]]}]})
        self.assertIn("words:", report)
        self.assertIn("est. pages:", report)


class TestBuildRejections(CvCase):
    def test_unknown_slot_id(self):
        smap = self.slot_map()
        rc, report = self.build({"order": [{"id": "exp-deadbe"}]})
        self.assertEqual(rc, 1)
        self.assertIn("unknown slot id", report)
        self.assertNothingWritten()

    def test_duplicate_slot_id(self):
        smap = self.slot_map()
        acme = self.block_by_company(smap, "Acme")
        rc, report = self.build({"order": [{"id": acme["id"]}, {"id": acme["id"]}]})
        self.assertEqual(rc, 1)
        self.assertIn("duplicate", report)
        self.assertNothingWritten()

    def test_keep_and_drop_contradiction(self):
        smap = self.slot_map()
        acme = self.block_by_company(smap, "Acme")
        rc, report = self.build({"order": [{"id": acme["id"]}], "drop": [acme["id"]]})
        self.assertEqual(rc, 1)
        self.assertIn("both", report)
        self.assertNothingWritten()

    def test_unknown_slot_id_in_drop(self):
        # An id the exemplar never had means the plan was written against a
        # different exemplar, which makes the whole plan untrustworthy — not
        # just this line.
        self.slot_map()
        rc, report = self.build({"order": [], "drop": ["b-deadbe"]})
        self.assertEqual(rc, 1)
        self.assertIn("unknown slot id in drop[]", report)
        self.assertNothingWritten()

    def test_bullet_placed_under_a_block_that_does_not_own_it(self):
        smap = self.slot_map()
        acme, beta = self.block_by_company(smap, "Acme"), self.block_by_company(smap, "Beta")
        rc, report = self.build({"order": [{"id": beta["id"],
                                            "bullets": [acme["bullets"][0]["id"]]}]})
        self.assertEqual(rc, 1)
        self.assertIn("does not belong", report)
        self.assertNothingWritten()

    def test_patch_operation_is_refused(self):
        # ADR-0005: the writer has no mechanism to alter a slot's text. A stale
        # writer still emitting the v3 contract must fail loudly rather than
        # have its rewording silently ignored.
        smap = self.slot_map()
        acme = self.block_by_company(smap, "Acme")
        rc, report = self.build({
            "order": [{"id": acme["id"], "bullets": [acme["bullets"][0]["id"]]}],
            "patch": [{"id": acme["bullets"][0]["id"], "text": "Reworded for the posting"}],
        })
        self.assertEqual(rc, 1)
        self.assertIn("patch", report)
        self.assertNothingWritten()

    def test_new_slot_operation_is_refused_for_now(self):
        smap = self.slot_map()
        acme = self.block_by_company(smap, "Acme")
        rc, report = self.build({
            "order": [{"id": acme["id"], "bullets": []}],
            "new": [{"id": "b-000000", "text": "Something the exemplar lacks"}],
        })
        self.assertEqual(rc, 1)
        self.assertNothingWritten()

    def test_plan_ordering_no_slots_is_refused(self):
        # Renders name + contact and would pass a verbatim check vacuously.
        self.slot_map()
        rc, report = self.build({"order": []})
        self.assertEqual(rc, 1)
        self.assertIn("orders no slots", report)
        self.assertNothingWritten()

    def test_undecomposable_exemplar(self):
        rc, report = self.build({"order": []}, exemplar_text="Just prose.\n")
        self.assertEqual(rc, 1)
        self.assertIn("no slots", report)
        self.assertNothingWritten()

    def test_malformed_plan_json_is_a_usage_error(self):
        exemplar = self.write("master_cv.md", EXEMPLAR)
        plan_path = self.write("plan.json", "{not json")
        rc, _ = self.run_cv(["build", str(plan_path), "--exemplar", str(exemplar),
                             "--out-dir", str(self.out_dir)])
        self.assertEqual(rc, 2)
        self.assertNothingWritten()

    def test_missing_plan_is_a_usage_error(self):
        exemplar = self.write("master_cv.md", EXEMPLAR)
        rc, _ = self.run_cv(["build", str(self.root / "nope.json"),
                             "--exemplar", str(exemplar), "--out-dir", str(self.out_dir)])
        self.assertEqual(rc, 2)
        self.assertNothingWritten()


class TestOneOffSlots(CvCase):
    """Contract (#26, ADR-0005): a one-off is content the candidate directed
    into a single application because the exemplar lacked it. It is the only
    permitted non-verbatim content in an assembled CV, it is always a new slot
    rather than a rewording of an existing one, and it must be declared — the
    declaration is what lets the self-test exempt it and the verifier know
    there is something to judge."""

    def plan_with_one_off(self, **overrides):
        smap = self.slot_map()
        acme = self.block_by_company(smap, "Acme")
        plan = {
            "order": [{"id": acme["id"],
                       "bullets": [acme["bullets"][0]["id"], "oneoff-k8s"]}],
            "one_off": [{"id": "oneoff-k8s",
                         "text": "Ran the Kubernetes migration end to end"}],
        }
        plan.update(overrides)
        return smap, acme, plan

    def test_a_declared_one_off_assembles_into_the_cv(self):
        _, _, plan = self.plan_with_one_off()
        rc, report = self.build(plan)
        self.assertEqual(rc, 0, report)
        text = (self.out_dir / "cv.md").read_text(encoding="utf-8")
        self.assertIn("- Ran the Kubernetes migration end to end", text)
        self.assertIn("- Built the billing pipeline serving 2M users", text)

    def test_self_test_exempts_the_one_off_and_holds_the_rest_to_verbatim(self):
        _, _, plan = self.plan_with_one_off()
        rc, report = self.build(plan)
        self.assertEqual(rc, 0, report)
        # headline is absent from this plan: contact, dates, descriptor, one kept bullet.
        self.assertIn("verbatim: 4/4", report)
        self.assertIn("changed: 0", report)
        self.assertIn("one-off: 1", report)

    def test_report_surfaces_every_one_off_for_the_verifier(self):
        _, _, plan = self.plan_with_one_off()
        _, report = self.build(plan)
        self.assertIn("ONE-OFF", report)
        self.assertIn("Ran the Kubernetes migration end to end", report)
        self.assertIn("verifier", report.lower())

    def test_a_one_off_reusing_an_exemplar_slot_id_is_rejected(self):
        # Same id, different text: that is altering a verified slot, which is
        # exactly what ADR-0005 removes.
        smap = self.slot_map()
        acme = self.block_by_company(smap, "Acme")
        bullet = acme["bullets"][0]
        rc, report = self.build({
            "order": [{"id": acme["id"], "bullets": [bullet["id"]]}],
            "one_off": [{"id": bullet["id"], "text": "Reworded for the posting"}],
        })
        self.assertEqual(rc, 1)
        self.assertIn("already a slot", report)
        self.assertNothingWritten()

    def test_an_undeclared_one_off_is_an_unknown_id(self):
        # Unmarked non-verbatim content: the plan places an id it never declared.
        smap = self.slot_map()
        acme = self.block_by_company(smap, "Acme")
        rc, report = self.build({"order": [{"id": acme["id"],
                                            "bullets": ["oneoff-undeclared"]}]})
        self.assertEqual(rc, 1)
        self.assertIn("unknown slot id", report)
        self.assertNothingWritten()

    def test_a_declared_one_off_that_is_never_placed_is_rejected(self):
        smap = self.slot_map()
        acme = self.block_by_company(smap, "Acme")
        rc, report = self.build({
            "order": [{"id": acme["id"], "bullets": [acme["bullets"][0]["id"]]}],
            "one_off": [{"id": "oneoff-dead", "text": "Never placed anywhere"}],
        })
        self.assertEqual(rc, 1)
        self.assertIn("never placed", report)
        self.assertNothingWritten()

    def test_a_one_off_with_empty_text_is_rejected(self):
        _, _, plan = self.plan_with_one_off(
            one_off=[{"id": "oneoff-k8s", "text": "   "}])
        rc, report = self.build(plan)
        self.assertEqual(rc, 1)
        self.assertIn("no text", report)
        self.assertNothingWritten()

    def test_a_one_off_can_be_a_section_level_entry(self):
        smap = self.slot_map()
        acme = self.block_by_company(smap, "Acme")
        rc, report = self.build({
            "order": [{"id": acme["id"], "bullets": [acme["bullets"][0]["id"]]},
                      {"id": "oneoff-cert"}],
            "one_off": [{"id": "oneoff-cert", "section": "Skills",
                         "text": "**Cloud:** AWS, Terraform"}],
        })
        self.assertEqual(rc, 0, report)
        text = (self.out_dir / "cv.md").read_text(encoding="utf-8")
        self.assertIn("## Skills", text)
        self.assertIn("**Cloud:** AWS, Terraform", text)

    def test_a_section_level_one_off_needs_a_section(self):
        smap = self.slot_map()
        acme = self.block_by_company(smap, "Acme")
        rc, report = self.build({
            "order": [{"id": acme["id"], "bullets": [acme["bullets"][0]["id"]]},
                      {"id": "oneoff-cert"}],
            "one_off": [{"id": "oneoff-cert", "text": "**Cloud:** AWS"}],
        })
        self.assertEqual(rc, 1)
        self.assertIn("section", report)
        self.assertNothingWritten()

    def test_a_one_off_cannot_invent_a_section(self):
        smap = self.slot_map()
        acme = self.block_by_company(smap, "Acme")
        rc, report = self.build({
            "order": [{"id": acme["id"], "bullets": [acme["bullets"][0]["id"]]},
                      {"id": "oneoff-x"}],
            "one_off": [{"id": "oneoff-x", "section": "Publications",
                         "text": "Wrote a paper"}],
        })
        self.assertEqual(rc, 1)
        self.assertIn("Publications", report)
        self.assertNothingWritten()

    def test_a_one_off_cannot_sit_loose_in_a_role_section(self):
        """Entries in Experience are `### Role — Company` blocks with dates and
        a descriptor. A one-off has none of that, so at section level it would
        render as a bare line adrift between two employers — and a reader would
        attribute it to whichever role it landed under."""
        smap = self.slot_map()
        acme = self.block_by_company(smap, "Acme")
        rc, report = self.build({
            "order": [{"id": acme["id"], "bullets": [acme["bullets"][0]["id"]]},
                      {"id": "oneoff-loose"}],
            "one_off": [{"id": "oneoff-loose", "section": "Experience",
                         "text": "Led a platform rewrite"}],
        })
        self.assertEqual(rc, 1)
        self.assertIn("role blocks", report)
        self.assertNothingWritten()

    def test_a_section_level_one_off_follows_its_sections_bullet_convention(self):
        # Skills lines are not bulleted in the exemplar, so a one-off there
        # must not be either — otherwise the section renders inconsistently.
        smap = self.slot_map()
        acme = self.block_by_company(smap, "Acme")
        rc, report = self.build({
            "order": [{"id": acme["id"], "bullets": [acme["bullets"][0]["id"]]},
                      {"id": "oneoff-cloud"}],
            "one_off": [{"id": "oneoff-cloud", "section": "Skills",
                         "text": "**Cloud:** AWS, Terraform"}],
        })
        self.assertEqual(rc, 0, report)
        text = (self.out_dir / "cv.md").read_text(encoding="utf-8")
        self.assertIn("\n**Cloud:** AWS, Terraform", text)
        self.assertNotIn("- **Cloud:**", text)

    def test_bullet_scoping_still_holds_when_one_offs_are_present(self):
        smap = self.slot_map()
        acme, beta = self.block_by_company(smap, "Acme"), self.block_by_company(smap, "Beta")
        rc, report = self.build({
            "order": [{"id": beta["id"],
                       "bullets": [acme["bullets"][0]["id"], "oneoff-k8s"]}],
            "one_off": [{"id": "oneoff-k8s", "text": "Ran the migration"}],
        })
        self.assertEqual(rc, 1)
        self.assertIn("does not belong", report)
        self.assertNothingWritten()

    def test_patch_is_still_refused_alongside_one_offs(self):
        _, acme, plan = self.plan_with_one_off()
        plan["patch"] = [{"id": acme["bullets"][0]["id"], "text": "Reworded"}]
        rc, report = self.build(plan)
        self.assertEqual(rc, 1)
        self.assertIn("patch", report)
        self.assertNothingWritten()


class TestVerbatimSelfTest(CvCase):
    """The self-test compares the rendered document against the *exemplar's own
    text*, not against the slot map the renderer worked from. Comparing the
    renderer's output to its own input would be a tautology; this catches the
    renderer corrupting a slot on the way out."""

    def test_self_test_reads_the_exemplar_not_the_renderer_state(self):
        smap = self.slot_map()
        acme = self.block_by_company(smap, "Acme")
        plan = {"order": [{"id": acme["id"], "bullets": [b["id"] for b in acme["bullets"]]}]}
        exemplar = self.write("master_cv.md", EXEMPLAR)
        plan_path = self.write("plan.json", json.dumps(plan))
        # The exemplar changes underneath after the plan was made against it.
        exemplar.write_text(EXEMPLAR.replace("2M users", "9M users"), encoding="utf-8")
        rc, report = self.run_cv(["build", str(plan_path), "--exemplar", str(exemplar),
                                  "--out-dir", str(self.out_dir)])
        # The plan's ids no longer exist in the changed exemplar, so this is
        # caught — but it must be caught, not silently rendered from stale text.
        self.assertEqual(rc, 1, report)
        self.assertNothingWritten()

    def test_a_corrupted_line_is_caught_and_nothing_is_written(self):
        """The rejection path itself. Only kept slots can reach the document, so
        the renderer is the only thing that could produce a non-verbatim line —
        which means the guard can only be exercised by making the renderer
        misbehave. Without this, the branch is unreachable and untested."""
        smap = self.slot_map()
        acme = self.block_by_company(smap, "Acme")
        plan = {"order": [{"id": acme["id"], "bullets": [b["id"] for b in acme["bullets"]]}]}
        exemplar = self.write("master_cv.md", EXEMPLAR)
        plan_path = self.write("plan.json", json.dumps(plan))

        real = cv.render_document

        def corrupting(smap_, plan_):
            doc = real(smap_, plan_)
            return [ln.replace("2M users", "40M users") for ln in doc]

        with mock.patch.object(cv, "render_document", corrupting):
            rc, report = self.run_cv(["build", str(plan_path), "--exemplar", str(exemplar),
                                      "--out-dir", str(self.out_dir)])
        self.assertEqual(rc, 1)
        self.assertIn("not verbatim", report)
        self.assertNothingWritten()

    def test_a_heading_the_exemplar_never_carried_is_caught(self):
        """Headings are skipped by the claim-level check, but `### Role — Company`
        is the line that says who an achievement belongs to. An invented one
        would reattribute real bullets and read as true."""
        smap = self.slot_map()
        acme = self.block_by_company(smap, "Acme")
        plan = {"order": [{"id": acme["id"], "bullets": [acme["bullets"][0]["id"]]}]}
        exemplar = self.write("master_cv.md", EXEMPLAR)
        plan_path = self.write("plan.json", json.dumps(plan))

        real = cv.render_document

        def corrupting(smap_, plan_):
            return [ln.replace("### Senior Engineer — Acme, Berlin",
                               "### Principal Engineer — Acme, Berlin")
                    for ln in real(smap_, plan_)]

        with mock.patch.object(cv, "render_document", corrupting):
            rc, report = self.run_cv(["build", str(plan_path), "--exemplar", str(exemplar),
                                      "--out-dir", str(self.out_dir)])
        self.assertEqual(rc, 1)
        self.assertIn("heading is not from the exemplar", report)
        self.assertNothingWritten()

    def test_a_wrapped_summary_paragraph_stays_verbatim(self):
        """A summary written across two lines is ordinary in a real CV. Joining
        it on the way out would emit a line present nowhere in the exemplar, and
        the self-test would refuse a perfectly valid build."""
        wrapped = EXEMPLAR.replace(
            "Ten years building payment systems.\n",
            "Ten years building payment systems.\nAcross fintech and logistics.\n")
        smap = self.slot_map(wrapped, name="wrapped.md")
        summary = [b for b in smap["blocks"] if b["kind"] == "summary"][0]
        rc, report = self.build({"order": [{"id": summary["id"]}]}, exemplar_text=wrapped)
        self.assertEqual(rc, 0, report)
        text = (self.out_dir / "cv.md").read_text(encoding="utf-8")
        self.assertIn("Ten years building payment systems.", text)
        self.assertIn("Across fintech and logistics.", text)
        self.assertIn("changed: 0", report)

    def test_every_emitted_content_line_is_present_in_the_exemplar(self):
        smap = self.slot_map()
        acme = self.block_by_company(smap, "Acme")
        plan = {"order": [
            {"id": self.ids(smap)["headline"][0]},
            {"id": acme["id"], "bullets": [b["id"] for b in acme["bullets"]]},
        ] + [{"id": sid} for sid in self.ids(smap)["skills"]]}
        rc, report = self.build(plan)
        self.assertEqual(rc, 0, report)
        import _common
        exemplar_lines = {n for _, n in _common.content_lines(EXEMPLAR)}
        produced = (self.out_dir / "cv.md").read_text(encoding="utf-8")
        for _, norm in _common.content_lines(produced):
            self.assertIn(norm, exemplar_lines)


if __name__ == "__main__":
    unittest.main()

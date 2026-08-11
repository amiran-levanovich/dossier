#!/usr/bin/env python3
"""Tests for alias groups. Run: python3 -m unittest discover scripts/tests

Two things are being pinned here, and the second matters more than the first.

The first is resolution: given a posting and a document, which spelling wins.
That is table-driven, because the interesting axis is input variety, not control
flow — one surprising spelling is worth more than one more branch.

The second is *ordering* (ADR-0008). Slot ids hash slot text, so a swap applied
before the verbatim self-test would rename the slots it touched and void the
guarantee the whole v4 method rests on. `apply` therefore refuses to run without
a passed self-test in hand, rather than trusting its caller to sequence itself.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import aliases  # noqa: E402

TABLE = (
    "# Alias groups\n\n"
    "Prose above the section is ignored.\n\n"
    "## Alias groups\n\n"
    "- PostgreSQL, Postgres\n"
    "- Ruby on Rails, Rails, RoR\n"
    "- Kubernetes, K8s\n"
    "- Golang, Go\n"
    "- MySQL, My SQL\n"
)


class Passed:
    """Stands in for a clean `cv.VerbatimResult` — no changed lines."""
    changed: list = []


class Failed:
    changed = [(7, "a line the exemplar does not carry")]


def groups(text=TABLE):
    return aliases.merge_groups(aliases.parse_groups(text))


class TestTable(unittest.TestCase):
    def test_bullets_under_the_section_parse_and_prose_does_not(self):
        parsed = aliases.parse_groups(TABLE)
        self.assertIn(["PostgreSQL", "Postgres"], parsed)
        self.assertEqual(len(parsed), 5)

    def test_a_prose_line_inside_the_section_is_not_a_group(self):
        """A note the user left among their groups must not become a set of
        interchangeable spellings — that would swap unrelated words on the CV."""
        parsed = aliases.parse_groups(
            "## Alias groups\n"
            "Careful, these are all Postgres spellings:\n"
            "- PostgreSQL, Postgres\n")
        self.assertEqual(parsed, [["PostgreSQL", "Postgres"]])

    def test_a_user_extension_can_add_a_group_and_extend_an_existing_one(self):
        extension = ("## Alias groups\n"
                     "- Postgres, pg, psql\n"      # extends: shares "Postgres"
                     "- Sidekiq, Side Kiq\n")      # adds
        merged = aliases.merge_groups(
            aliases.parse_groups(TABLE) + aliases.parse_groups(extension))
        postgres = [g for g in merged if "PostgreSQL" in g][0]
        self.assertEqual(postgres, ["PostgreSQL", "Postgres", "pg", "psql"])
        self.assertIn(["Sidekiq", "Side Kiq"], merged)
        # Extending must not fork the group in two.
        self.assertEqual(len([g for g in merged if "Postgres" in g]), 1)

    def test_a_member_belongs_to_exactly_one_group_after_merging(self):
        merged = aliases.merge_groups(aliases.parse_groups(TABLE) + [["K8s", "kube"]])
        seen: set[str] = set()
        for group in merged:
            for member in group:
                self.assertNotIn(member.casefold(), seen)
                seen.add(member.casefold())

    def test_the_shipped_table_is_well_formed(self):
        """The shipped table is data, and a malformed group here would silently
        swap one technology for another on every user's CV."""
        shipped, faults = aliases.load_table([aliases.PLUGIN_TABLE])
        self.assertEqual(faults, [])
        self.assertGreater(len(shipped), 10)
        for group in shipped:
            self.assertGreaterEqual(len(group), 2, group)

    def test_no_shipped_member_is_a_whole_token_inside_a_member_of_another_group(self):
        """`CI` inside `CI/CD` would rewrite the longer spelling from the middle.
        Cross-group token containment is the one shape the swap cannot survive."""
        shipped, _ = aliases.load_table([aliases.PLUGIN_TABLE])
        for i, group in enumerate(shipped):
            others = [m for j, g in enumerate(shipped) if j != i for m in g]
            for member in group:
                for other in others:
                    if member.casefold() == other.casefold():
                        continue
                    self.assertIsNone(
                        aliases.first_position(member, other),
                        f"{member!r} is a token inside {other!r}")


class TestLoad(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def write(self, name, text):
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_a_missing_table_is_a_fault_not_an_empty_table(self):
        _, faults = aliases.load_table([self.root / "nope.md"])
        self.assertTrue(any("not found" in f for f in faults), faults)

    def test_a_table_without_the_section_is_a_fault(self):
        path = self.write("ext.md", "- PostgreSQL, Postgres\n")
        loaded, faults = aliases.load_table([path])
        self.assertEqual(loaded, [])
        self.assertTrue(any("Alias groups" in f for f in faults), faults)

    def test_a_single_member_group_is_a_fault(self):
        """It can never fire, so it is a typo — a dropped comma or a stray note."""
        path = self.write("ext.md", "## Alias groups\n- PostgreSQL\n")
        _, faults = aliases.load_table([path])
        self.assertTrue(any("one member" in f for f in faults), faults)

    def test_the_plugin_table_and_a_user_extension_merge(self):
        path = self.write("ext.md", "## Alias groups\n- Sidekiq, Side Kiq\n")
        merged, faults = aliases.load_table([aliases.PLUGIN_TABLE, path])
        self.assertEqual(faults, [])
        self.assertIn(["Sidekiq", "Side Kiq"], merged)
        self.assertTrue(any("PostgreSQL" in g for g in merged))


class TestResolution(unittest.TestCase):
    """Table-driven: (why, posting, document line, expected line)."""

    CASES = [
        ("the posting's spelling wins",
         "You will work on Postgres.", "PostgreSQL and Redis", "Postgres and Redis"),
        ("no swap when they already agree",
         "You will work on PostgreSQL.", "PostgreSQL and Redis", "PostgreSQL and Redis"),
        ("no swap across groups",
         "We run MySQL here.", "PostgreSQL and Redis", "PostgreSQL and Redis"),
        ("no swap when the posting names nothing in the group",
         "We are hiring a backend engineer.", "PostgreSQL", "PostgreSQL"),
        ("the longest spelling is replaced first, never from the middle",
         "RoR shop.", "Ruby on Rails since 2015", "RoR since 2015"),
        ("a short member expands to the posting's long spelling",
         "Ruby on Rails, obviously.", "Rails since 2015", "Ruby on Rails since 2015"),
        ("the inserted spelling is not itself swapped again",
         "Ruby on Rails, obviously.", "RoR since 2015", "Ruby on Rails since 2015"),
        ("a hyphen is a token boundary",
         "Postgres.", "PostgreSQL-backed service", "Postgres-backed service"),
        ("a substring is not a token",
         "K8s.", "Kubernetesish", "Kubernetesish"),
        ("case-sensitive members do not fire on ordinary prose",
         "Golang shop.", "Decided to go with a queue", "Decided to go with a queue"),
        ("case-sensitive members still fire on the technology",
         "Golang shop.", "Go services behind nginx", "Golang services behind nginx"),
        ("posting prose does not decide the winner for a cased member",
         "We go fast. Golang throughout.", "Go services", "Golang services"),
        ("the table's spelling is emitted, not the posting's casing",
         "we use postgres daily", "PostgreSQL and Redis", "Postgres and Redis"),
        ("the earliest posting spelling wins when it names two",
         "K8s, or Kubernetes if you prefer.", "Kubernetes cluster", "K8s cluster"),
    ]

    def test_resolution(self):
        for why, posting, line, expected in self.CASES:
            with self.subTest(why):
                out, _ = aliases.apply([line], posting, groups(), Passed())
                self.assertEqual(out, [expected])

    def test_a_swap_is_recorded_with_its_line_and_both_spellings(self):
        doc = ["## Skills", "PostgreSQL, Redis", "Kubernetes"]
        _, swaps = aliases.apply(doc, "Postgres and K8s.", groups(), Passed())
        self.assertEqual([(s.lineno, s.term, s.replacement) for s in swaps],
                         [(2, "PostgreSQL", "Postgres"), (3, "Kubernetes", "K8s")])

    def test_every_occurrence_on_a_line_is_recorded(self):
        _, swaps = aliases.apply(["PostgreSQL to PostgreSQL"], "Postgres.",
                                 groups(), Passed())
        self.assertEqual(len(swaps), 2)

    def test_no_groups_means_no_swaps(self):
        out, swaps = aliases.apply(["PostgreSQL"], "Postgres.", [], Passed())
        self.assertEqual((out, swaps), (["PostgreSQL"], []))


class TestOrdering(unittest.TestCase):
    """ADR-0008: the swap runs after the self-test, and the module enforces it."""

    def test_a_failed_self_test_refuses_the_alias_pass(self):
        with self.assertRaises(aliases.AliasOrderError):
            aliases.apply(["PostgreSQL"], "Postgres.", groups(), Failed())

    def test_no_self_test_at_all_refuses_the_alias_pass(self):
        """Forgetting to run it must fail as loudly as failing it, or the
        ordering is a convention rather than a guarantee."""
        with self.assertRaises(aliases.AliasOrderError):
            aliases.apply(["PostgreSQL"], "Postgres.", groups(), None)


class TestLog(unittest.TestCase):
    def test_the_log_names_every_swap_and_the_tables_it_came_from(self):
        doc = ["PostgreSQL, Redis"]
        _, swaps = aliases.apply(doc, "Postgres.", groups(), Passed())
        log = aliases.log_document(swaps, ["scripts/alias_groups.md"], "master_cv.md")
        self.assertIn("PostgreSQL", log)
        self.assertIn("Postgres", log)
        self.assertIn("scripts/alias_groups.md", log)
        self.assertIn("master_cv.md", log)

    def test_the_log_says_so_when_nothing_fired(self):
        log = aliases.log_document([], ["scripts/alias_groups.md"], "master_cv.md")
        self.assertIn("no swaps", log.lower())


if __name__ == "__main__":
    unittest.main()

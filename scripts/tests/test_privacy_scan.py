#!/usr/bin/env python3
"""Tests for privacy_scan.py — the personal-data (PII) boundary scanner.

Run: python3 -m unittest discover scripts/tests

Stdlib only, matching the rest of scripts/tests. These tests ARE the contract:
each detector is specified by the strings it MUST flag and the legitimate
dossier-doc strings it MUST NOT (the false-positive traps found by calibrating
against the real repo — token counts like "60k tokens", ISO dates, and
call-count ranges like "16-18").
"""

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import privacy_scan  # noqa: E402


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
# email detector
# --------------------------------------------------------------------------
class TestEmail(unittest.TestCase):
    def flagged(self, text):
        return [m for _, m in privacy_scan.find_emails(text)]

    def test_flags_real_email(self):
        self.assertEqual(self.flagged("contact amiran@gmail.com now"), ["amiran@gmail.com"])

    def test_flags_corporate_email(self):
        self.assertTrue(self.flagged("a.tsiklauri@somecompany.io"))

    def test_ignores_example_domains(self):
        # Template placeholders are not PII.
        self.assertEqual(self.flagged("you@example.com"), [])
        self.assertEqual(self.flagged("firstname.lastname@example.org"), [])
        self.assertEqual(self.flagged("name@example.net"), [])

    def test_ignores_placeholder_locals(self):
        self.assertEqual(self.flagged("your.email@company.com"), [])

    def test_reports_line_numbers(self):
        text = "line one\nreach me at real.person@proton.me\n"
        hits = privacy_scan.find_emails(text)
        self.assertEqual(hits[0][0], 2)


# --------------------------------------------------------------------------
# salary detector — currency-anchored amount, never a bare "Nk"
# --------------------------------------------------------------------------
class TestSalary(unittest.TestCase):
    def flagged(self, text):
        return [m for _, m in privacy_scan.find_salaries(text)]

    def test_flags_currency_amounts(self):
        for s in ["€75,000", "80.000 EUR", "EUR 90000", "$120,000", "75000 EUR", "CHF 110000"]:
            with self.subTest(s=s):
                self.assertTrue(self.flagged(s), f"should flag salary: {s}")

    def test_ignores_token_counts(self):
        # The calibration traps: these are token counts in TOKEN_ECONOMY.md, not pay.
        for s in ["runs 5 minutes and 60k tokens", "pulls 10-30k tokens of noise",
                  "a single 69k-token cache_write turn", "~60k tokens/5 min"]:
            with self.subTest(s=s):
                self.assertEqual(self.flagged(s), [], f"must not flag token count: {s}")

    def test_ignores_percentages_and_bare_numbers(self):
        self.assertEqual(self.flagged("eats 10-15% of a 5-hour budget"), [])
        self.assertEqual(self.flagged("the number 75000 with no currency near"), [])

    def test_ignores_currency_word_without_amount(self):
        self.assertEqual(self.flagged("discuss your salary expectations in EUR"), [])


# --------------------------------------------------------------------------
# phone detector — international (+CC) only, never an ISO date or a range
# --------------------------------------------------------------------------
class TestPhone(unittest.TestCase):
    def flagged(self, text):
        return [m for _, m in privacy_scan.find_phones(text)]

    def test_flags_international_numbers(self):
        for s in ["+43 660 1234567", "+49 30 12345678", "+1 (415) 555-0132"]:
            with self.subTest(s=s):
                self.assertTrue(self.flagged(s), f"should flag phone: {s}")

    def test_ignores_iso_dates(self):
        for s in ["2026-07-14", "2026-07-08 [hard-filter] betacorp", "applied 2026-07-05 today"]:
            with self.subTest(s=s):
                self.assertEqual(self.flagged(s), [], f"must not flag date: {s}")

    def test_ignores_ranges_and_counts(self):
        self.assertEqual(self.flagged("both writers over ceiling (16-18 calls vs 15)"), [])
        self.assertEqual(self.flagged("39 calls vs the 20 ceiling, 4 rounds"), [])


# --------------------------------------------------------------------------
# denylist detector — whole-token, case-insensitive, from untracked config
# --------------------------------------------------------------------------
class TestDenylist(unittest.TestCase):
    def test_matches_whole_token_case_insensitive(self):
        terms = ["Straiv", "Acme Corp"]
        hits = [m for _, m in privacy_scan.find_denylist("we shipped at STRAIV last year", terms)]
        self.assertEqual(len(hits), 1)

    def test_does_not_match_substring(self):
        # 'Straiv' must not fire inside 'Straivision'.
        self.assertEqual(privacy_scan.find_denylist("built Straivision here", ["Straiv"]), [])

    def test_empty_terms_is_clean(self):
        self.assertEqual(privacy_scan.find_denylist("anything at all", []), [])

    def test_load_denylist_parses_comments_and_blanks(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".privacy-denylist"
            p.write_text("# real employers\nStraiv\n\n  Acme Corp  \n", encoding="utf-8")
            self.assertEqual(privacy_scan.load_denylist(p), ["Straiv", "Acme Corp"])

    def test_load_denylist_missing_returns_empty(self):
        self.assertEqual(privacy_scan.load_denylist(Path("/no/such/file")), [])


# --------------------------------------------------------------------------
# masking — findings never echo full PII back into logs
# --------------------------------------------------------------------------
class TestMasking(unittest.TestCase):
    def test_mask_hides_middle(self):
        masked = privacy_scan.mask("amiran@gmail.com")
        self.assertNotIn("amiran@gmail.com", masked)
        self.assertTrue(masked.startswith("am"))

    def test_mask_short_string(self):
        self.assertEqual(privacy_scan.mask("ab"), "**")


# --------------------------------------------------------------------------
# scan_text aggregation + Finding shape
# --------------------------------------------------------------------------
class TestScanText(unittest.TestCase):
    def test_aggregates_categories_with_lineno(self):
        text = "clean line\ncall +43 660 1234567 or mail real@proton.me\n"
        findings = privacy_scan.scan_text(text, denylist=[])
        cats = {f.category for f in findings}
        self.assertEqual(cats, {"phone", "email"})
        self.assertTrue(all(f.line == 2 for f in findings))

    def test_clean_text_no_findings(self):
        text = "The verifier ran 60k tokens on 2026-07-14 over 16-18 calls.\n"
        self.assertEqual(privacy_scan.scan_text(text, denylist=[]), [])

    def test_suppression_marker_skips_its_line(self):
        # A generic illustrative example in a method doc opts out with 'pii-ok'.
        text = 'range like "62.000-68.000 €" <!-- pii-ok: format example -->\n'
        self.assertEqual(privacy_scan.scan_text(text, denylist=[]), [])

    def test_suppression_is_line_scoped(self):
        text = "clean <!-- pii-ok -->\nreal amiran@gmail.com here\n"
        findings = privacy_scan.scan_text(text, denylist=[])
        self.assertEqual([f.category for f in findings], ["email"])
        self.assertEqual(findings[0].line, 2)


# --------------------------------------------------------------------------
# file / binary handling + scan_paths
# --------------------------------------------------------------------------
class TestScanPaths(TmpMixin):
    def test_scan_paths_reports_path_and_finding(self):
        self.write("job_docs/example.md", "reach me at real.person@proton.me\n")
        results = privacy_scan.scan_paths([self.root / "job_docs/example.md"], denylist=[])
        self.assertEqual(len(results), 1)
        path, finding = results[0]
        self.assertEqual(finding.category, "email")

    def test_skips_binary(self):
        p = self.root / "blob.bin"
        p.write_bytes(b"\x00\x01real@proton.me\x00")
        self.assertEqual(privacy_scan.scan_paths([p], denylist=[]), [])

    def test_is_binary(self):
        self.assertTrue(privacy_scan.is_binary(b"abc\x00def"))
        self.assertFalse(privacy_scan.is_binary(b"plain text"))


# --------------------------------------------------------------------------
# main() — exit codes and output contract
# --------------------------------------------------------------------------
class TestMain(TmpMixin):
    def run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = privacy_scan.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_clean_paths_exit_zero(self):
        f = self.write("clean.md", "60k tokens on 2026-07-14, 16-18 calls, salary in EUR\n")
        code, _, err = self.run_main(["--paths", str(f)])
        self.assertEqual(code, 0)
        self.assertIn("clean", err.lower())

    def test_dirty_paths_exit_one_and_masks(self):
        f = self.write("dirty.md", "email amiran@gmail.com here\n")
        code, _, err = self.run_main(["--paths", str(f)])
        self.assertEqual(code, 1)
        self.assertIn("email", err)
        self.assertNotIn("amiran@gmail.com", err)  # masked, never echoed raw

    def test_denylist_flag_applied(self):
        f = self.write("doc.md", "we were at Straiv\n")
        dl = self.write(".privacy-denylist", "Straiv\n")
        code, _, err = self.run_main(["--paths", str(f), "--denylist", str(dl)])
        self.assertEqual(code, 1)
        self.assertIn("denylist", err)

    def test_json_output(self):
        f = self.write("dirty.md", "mail real@proton.me\n")
        code, out, _ = self.run_main(["--paths", str(f), "--json"])
        self.assertEqual(code, 1)
        import json
        data = json.loads(out)
        self.assertEqual(data[0]["category"], "email")

    def test_scanner_skips_denylist_file_itself(self):
        # The denylist holds real employer names; scanning it would report them.
        dl = self.write(".privacy-denylist", "Straiv\n")
        code, _, err = self.run_main(["--paths", str(dl), "--denylist", str(dl)])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()

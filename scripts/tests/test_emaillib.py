"""Unit tests for the reference email helpers."""

from __future__ import annotations

import unittest

import _support as S

E = S.emaillib


class SubjectNormalizationTest(unittest.TestCase):
    def test_prefixes(self) -> None:
        cases = {
            "Re: Hello": "Hello",
            "RE: Fwd: FW: Hello": "Hello",
            "AW: SV: Hello": "Hello",
            "Re[2]: Hello": "Hello",
            "رد: RE: Hello": "Hello",
            "[isupply-sales] Re: Hello": "Hello",
            "Hello: world": "Hello: world",
            "Reply needed": "Reply needed",
        }
        for raw, want in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(E.normalize_subject(raw), want)


class ModifiedUtf7Test(unittest.TestCase):
    def test_known_vectors(self) -> None:
        # RFC 3501 §5.1.3 example and common cases
        self.assertEqual(E.imap_utf7_encode("~peter/mail/台北/日本語"), "~peter/mail/&U,BTFw-/&ZeVnLIqe-")
        self.assertEqual(E.imap_utf7_encode("A&B"), "A&-B")
        self.assertEqual(E.imap_utf7_encode("INBOX"), "INBOX")

    def test_round_trip_arabic(self) -> None:
        for name in ("تقارير", "Projects.المبيعات 2026", "R&D — notes"):
            with self.subTest(name=name):
                self.assertEqual(E.imap_utf7_decode(E.imap_utf7_encode(name)), name)


class HtmlFindingsTest(unittest.TestCase):
    def test_clean_html(self) -> None:
        f = E.html_findings('<p dir="auto">Hello <a href="https://intranet.isupply.test/x">link</a></p>')
        self.assertEqual(f["dangerous"], {})
        self.assertEqual(f["remote_resources"], 0)

    def test_obfuscated_javascript_url(self) -> None:
        f = E.html_findings('<a href="  jav&#x09;ascript:alert(1)">x</a><a href="JAVASCRIPT:alert(2)">y</a>')
        self.assertEqual(f["dangerous"].get("javascript_url"), 2)

    def test_mismatched_link_text(self) -> None:
        f = E.html_findings('<a href="https://evil.example/login">https://mail.isupply.test</a>')
        self.assertEqual(f["mismatched_links"], [{"href_host": "evil.example", "text_host": "mail.isupply.test"}])


class FilenameWarningsTest(unittest.TestCase):
    def test_flags(self) -> None:
        self.assertIn("bidi_control_chars", E.filename_warnings("invoice\u202efdp.exe"))
        self.assertIn("executable_extension", E.filename_warnings("invoice\u202efdp.exe"))
        self.assertIn("path_traversal", E.filename_warnings("../../x.txt"))
        self.assertIn("windows_reserved_name", E.filename_warnings("aux.log"))
        self.assertEqual(E.filename_warnings("report-2026.pdf"), [])


if __name__ == "__main__":
    unittest.main()

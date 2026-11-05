"""Tests for the email CLI tools: anonymizer, discovery parsers, inspector."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest

import _support as S

import anonymize_eml  # noqa: E402
import discover  # noqa: E402


class AnonymizeTest(unittest.TestCase):
    def test_no_original_addresses_or_names_remain(self) -> None:
        raw = (S.FIXTURES_DIR / "006-attachments-rfc2231.eml").read_bytes()
        out = anonymize_eml.anonymize_bytes(raw)
        for needle in (b"mona.adel", b"accounts@isupply.test", b"Mona Adel", b"Received:"):
            self.assertNotIn(needle, out)
        self.assertIn(b"@isupply.test", out)  # internal domain maps to the internal test domain

    def test_structure_preserved(self) -> None:
        for name in ("007-outlook-nested-structure.eml", "005-inline-image-cid.eml", "013-calendar-invite.eml"):
            with self.subTest(fixture=name):
                raw = (S.FIXTURES_DIR / name).read_bytes()
                before = S.emaillib.summarize(S.emaillib.parse_bytes(raw))
                after = S.emaillib.summarize(S.emaillib.parse_bytes(anonymize_eml.anonymize_bytes(raw)))
                self.assertEqual([p["content_type"] for p in before["parts"]], [p["content_type"] for p in after["parts"]])
                self.assertEqual(len(before["attachments"]), len(after["attachments"]))
                self.assertEqual(before["body"]["preferred"], after["body"]["preferred"])

    def test_inline_images_stay_linked(self) -> None:
        for name in ("005-inline-image-cid.eml", "007-outlook-nested-structure.eml"):
            with self.subTest(fixture=name):
                out = anonymize_eml.anonymize_bytes((S.FIXTURES_DIR / name).read_bytes())
                summary = S.emaillib.summarize(S.emaillib.parse_bytes(out))
                self.assertEqual(len(summary["inline_parts"]), 1)
                self.assertFalse([w for w in summary["warnings"] if "missing inline part" in w], summary["warnings"])

    def test_output_is_crlf_and_deterministic(self) -> None:
        raw = (S.FIXTURES_DIR / "009-thread-reply.eml").read_bytes()
        a, b = anonymize_eml.anonymize_bytes(raw), anonymize_eml.anonymize_bytes(raw)
        self.assertEqual(a, b)
        self.assertEqual(S.emaillib.line_endings(a), "crlf")

    def test_redact_text_keeps_script(self) -> None:
        red = anonymize_eml.redact_script("Order الطلب 5521 <b>OK</b>")
        self.assertEqual(red, "Xxxxx سسسسس 5521 <b>XX</b>")


class DiscoverParsingTest(unittest.TestCase):
    AUTOCONFIG = """<?xml version="1.0"?>
<clientConfig version="1.1"><emailProvider id="isupply.test"><domain>isupply.test</domain>
<incomingServer type="imap"><hostname>Mail.ISupply.test</hostname><port>993</port><socketType>SSL</socketType>
<authentication>password-cleartext</authentication><username>%EMAILADDRESS%</username></incomingServer>
<outgoingServer type="smtp"><hostname>mail.isupply.test</hostname><port>465</port><socketType>SSL</socketType>
<authentication>password-cleartext</authentication><username>%EMAILLOCALPART%</username></outgoingServer>
</emailProvider></clientConfig>"""

    def test_parse_autoconfig(self) -> None:
        servers = discover.parse_autoconfig(self.AUTOCONFIG, "sara.hassan@isupply.test")
        self.assertEqual(servers[0], {"role": "incoming", "protocol": "imap", "host": "mail.isupply.test", "port": 993,
                                      "security": "SSL", "auth": ["password-cleartext"], "username": "sara.hassan@isupply.test"})
        self.assertEqual(servers[1]["username"], "sara.hassan")

    def test_parse_autoconfig_garbage(self) -> None:
        self.assertEqual(discover.parse_autoconfig("<html>not xml", "a@b.c"), [])

    def test_parse_dns_answers(self) -> None:
        self.assertEqual(discover.parse_answer_data("MX", ["20 alt1.aspmx.l.google.com.", "10 aspmx.l.google.com."]),
                         [{"priority": 10, "host": "aspmx.l.google.com"}, {"priority": 20, "host": "alt1.aspmx.l.google.com"}])
        self.assertEqual(discover.parse_answer_data("SRV", ["0 1 993 imap.example.com.", "0 0 0 ."]),
                         [{"priority": 0, "weight": 1, "port": 993, "host": "imap.example.com"}])

    def test_provider_fingerprints(self) -> None:
        self.assertEqual(discover.provider_for_mx(["isupply-com.mail.protection.outlook.com"])[0], "microsoft-365")
        self.assertEqual(discover.provider_for_mx(["aspmx.l.google.com"])[0], "google-workspace")
        self.assertIsNone(discover.provider_for_mx(["mail.isupply.com"]))


class InspectCliTest(unittest.TestCase):
    def test_json_output(self) -> None:
        r = subprocess.run([sys.executable, str(S.REPO / "scripts/email/inspect_eml.py"),
                            str(S.FIXTURES_DIR / "003-arabic-rfc2047.eml"), "--json"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["from"][0]["address"], "sara.hassan@isupply.test")

    def test_human_report_flags_spoofing(self) -> None:
        r = subprocess.run([sys.executable, str(S.REPO / "scripts/email/inspect_eml.py"),
                            str(S.FIXTURES_DIR / "019-attachment-filename-spoofing.eml")], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("bidi_control_chars", r.stdout)


if __name__ == "__main__":
    unittest.main()

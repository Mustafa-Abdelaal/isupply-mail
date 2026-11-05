"""Integration tests against the local dev mail server. Run: scripts/dev-mail up && scripts/test --integration-only"""

from __future__ import annotations

import imaplib
import json
import os
import smtplib
import subprocess
import sys
import time
import unittest
from email.message import EmailMessage

import _support as S

HOST = os.environ.get("DEV_MAIL_HOST", "127.0.0.1")
IMAP_PORT = int(os.environ.get("DEV_MAIL_IMAP_PORT", "3143"))
SMTP_PORT = int(os.environ.get("DEV_MAIL_SMTP_PORT", "3025"))
ENABLED = os.environ.get("ISUPPLY_INTEGRATION") == "1"


@unittest.skipUnless(ENABLED, "integration: needs `scripts/dev-mail up` and ISUPPLY_INTEGRATION=1 (scripts/test --integration)")
class DevMailIntegrationTest(unittest.TestCase):
    def imap(self, user: str = "alice@isupply.test", password: str = "alice-dev-pw") -> imaplib.IMAP4:
        conn = imaplib.IMAP4(HOST, IMAP_PORT, timeout=15)
        conn.login(user, password)
        return conn

    def test_integration_seeded_folders_and_counts(self) -> None:
        manifest = S.load_manifest()
        expected = {}
        for f in manifest["fixtures"]:
            folder = f.get("seed", {}).get("folder", "INBOX")
            expected[folder] = expected.get(folder, 0) + 1
        conn = self.imap()
        typ, data = conn.list('""', '""')
        delim = data[0].decode().split('"')[1]
        for folder, count in expected.items():
            wire = "INBOX" if folder == "INBOX" else '"' + S.emaillib.imap_utf7_encode(folder.replace("/", delim)) + '"'
            typ, sel = conn.select(wire, readonly=True)
            self.assertEqual(typ, "OK", f"cannot select {folder}")
            self.assertGreaterEqual(int(sel[0]), count, f"{folder}: expected at least {count} messages")
        conn.logout()

    def test_integration_arabic_folder_round_trips(self) -> None:
        conn = self.imap()
        typ, data = conn.list()
        names = [S.emaillib.imap_utf7_decode(line.decode().rsplit(" ", 1)[-1].strip('"')) for line in data]
        conn.logout()
        self.assertIn("تقارير", names)

    def test_integration_seeded_message_parses_identically(self) -> None:
        conn = self.imap()
        conn.select('"' + S.emaillib.imap_utf7_encode("Reports") + '"', readonly=True)
        typ, data = conn.uid("SEARCH", None, "ALL")
        uids = data[0].split()
        self.assertTrue(uids)
        subjects = set()
        for uid in uids:
            typ, msg = conn.uid("FETCH", uid, "(BODY.PEEK[])")
            raw = next(part[1] for part in msg if isinstance(part, tuple))
            subjects.add(S.emaillib.summarize(S.emaillib.parse_bytes(raw))["subject"])
        conn.logout()
        want = {f["expect"]["subject"] for f in S.load_manifest()["fixtures"] if f.get("seed", {}).get("folder") == "Reports"}
        self.assertTrue(want <= subjects, f"missing {want - subjects}")

    def test_integration_smtp_delivery(self) -> None:
        subject = f"integration {time.time():.0f}"
        m = EmailMessage()
        m["From"], m["To"], m["Subject"] = "bob@isupply.test", "alice@isupply.test", subject
        m.set_content("hello")
        with smtplib.SMTP(HOST, SMTP_PORT, timeout=15) as s:
            s.send_message(m)
        conn = self.imap()
        conn.select("INBOX", readonly=True)
        found = []
        for _ in range(20):
            typ, data = conn.uid("SEARCH", None, "SUBJECT", f'"{subject}"')
            found = data[0].split()
            if found:
                break
            time.sleep(0.25)
        conn.logout()
        self.assertTrue(found, "message did not arrive in alice's INBOX")

    def test_integration_probe_tool(self) -> None:
        r = subprocess.run([sys.executable, str(S.REPO / "scripts/email/probe_server.py"), "--imap", f"{HOST}:{IMAP_PORT}",
                            "--smtp", f"{HOST}:{SMTP_PORT}", "--user", "alice@isupply.test", "--password-env", "DEV_PW", "--json"],
                           capture_output=True, text=True, env={**os.environ, "DEV_PW": "alice-dev-pw"})
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["imap"]["login"], "ok")
        self.assertTrue(out["imap"]["supports"]["IDLE"])
        self.assertIn("PLAIN", out["smtp"]["auth_mechanisms"])


if __name__ == "__main__":
    unittest.main()

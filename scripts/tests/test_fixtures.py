"""Fixture corpus integrity + conformance of the reference parser (scripts/email/emaillib.py)."""

from __future__ import annotations

import subprocess
import sys
import unittest

import _support as S


class FixtureCorpusTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = S.load_manifest()

    def test_manifest_and_files_match(self) -> None:
        listed = {f["file"] for f in self.manifest["fixtures"]}
        on_disk = {p.name for p in S.FIXTURES_DIR.glob("*.eml")}
        self.assertEqual(sorted(on_disk - listed), [], "fixtures missing from manifest.json")
        self.assertEqual(sorted(listed - on_disk), [], "manifest lists files that do not exist")

    def test_required_metadata(self) -> None:
        for f in self.manifest["fixtures"]:
            for key in ("file", "origin", "line_endings", "description", "tags", "expect"):
                self.assertIn(key, f, f"{f.get('file')}: missing {key}")
            self.assertIn(f["origin"], ("synthetic", "anonymized"), f["file"])

    def test_line_endings_are_as_declared(self) -> None:
        for f in self.manifest["fixtures"]:
            raw = (S.FIXTURES_DIR / f["file"]).read_bytes()
            self.assertEqual(S.emaillib.line_endings(raw), f["line_endings"], f["file"])

    def test_no_bare_lf_in_crlf_fixtures(self) -> None:
        for f in self.manifest["fixtures"]:
            if f["line_endings"] != "crlf":
                continue
            raw = (S.FIXTURES_DIR / f["file"]).read_bytes()
            self.assertNotIn(b"\n", raw.replace(b"\r\n", b""), f"{f['file']} has bare LF")

    def test_synthetic_fixtures_are_generated(self) -> None:
        r = subprocess.run([sys.executable, str(S.FIXTURES_DIR / "generate_synthetic.py"), "--check"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr or r.stdout)

    def test_threads_reference_known_fixtures(self) -> None:
        files = {f["file"] for f in self.manifest["fixtures"]}
        for t in self.manifest.get("threads", []):
            for m in t["messages"]:
                self.assertIn(m, files, f"thread {t['id']}")


class ConformanceTest(unittest.TestCase):
    """The reference parser must satisfy every expectation (the same suite the app must pass)."""

    def test_each_fixture(self) -> None:
        for f in S.load_manifest()["fixtures"]:
            with self.subTest(fixture=f["file"]):
                errors = S.conformance_errors(S.summary_for(f["file"]), f["expect"])
                self.assertEqual(errors, [], f["file"])

    def test_threads_group_by_references_or_in_reply_to(self) -> None:
        for t in S.load_manifest().get("threads", []):
            summaries = [S.summary_for(m) for m in t["messages"]]
            ids = {s["message_id"] for s in summaries}
            root = summaries[0]
            for s in summaries[1:]:
                parents = set(s["references"]) | ({s["in_reply_to"]} if s["in_reply_to"] else set())
                self.assertTrue(parents & ids, f"{s['message_id']} does not link into thread {t['id']}")
                self.assertEqual(s["normalized_subject"], t["normalized_subject"])
            self.assertEqual(root["normalized_subject"], t["normalized_subject"])


if __name__ == "__main__":
    unittest.main()

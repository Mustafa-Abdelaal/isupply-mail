"""Shared test helpers: import paths and the fixture-conformance checker."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parents[2]
for sub in ("scripts/email", "scripts/agent", "fixtures/email"):
    p = str(REPO / sub)
    if p not in sys.path:
        sys.path.insert(0, p)

import emaillib  # noqa: E402

FIXTURES_DIR = REPO / "fixtures" / "email"
MANIFEST_PATH = FIXTURES_DIR / "manifest.json"


def load_manifest() -> Dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def summary_for(file: str) -> Dict[str, Any]:
    raw = (FIXTURES_DIR / file).read_bytes()
    return emaillib.summarize(emaillib.parse_bytes(raw), raw)


def conformance_errors(summary: Dict[str, Any], expect: Dict[str, Any]) -> List[str]:
    """Compare a summary to manifest expectations. Returns human-readable mismatches.

    This function is the executable definition of the `expect` keys documented in
    fixtures/email/README.md — app implementations must mirror it.
    """
    errs: List[str] = []

    def check(cond: bool, msg: str) -> None:
        if not cond:
            errs.append(msg)

    body = summary["body"]
    hf = summary.get("html_findings") or {"dangerous": {}, "remote_resources": 0, "tracking_pixels": 0, "mismatched_links": []}
    for key, want in expect.items():
        if key in ("subject", "normalized_subject", "date", "message_id", "in_reply_to"):
            check(summary[key] == want, f"{key}: got {summary[key]!r}, want {want!r}")
        elif key == "references":
            check(summary["references"] == want, f"references: got {summary['references']!r}, want {want!r}")
        elif key == "from":
            check(summary["from"] == want, f"from: got {summary['from']!r}, want {want!r}")
        elif key in ("to", "cc"):
            got = [a["address"] for a in summary[key]]
            check(got == want, f"{key}: got {got!r}, want {want!r}")
        elif key == "body_preferred":
            check(body["preferred"] == want, f"body_preferred: got {body['preferred']!r}, want {want!r}")
        elif key == "text_contains":
            for s in want:
                check(s in (body["text"] or ""), f"text body lacks {s!r}")
        elif key == "html_contains":
            for s in want:
                check(s in (body["html"] or ""), f"html body lacks {s!r}")
        elif key == "attachments":
            got = summary["attachments"]
            check(len(got) == len(want), f"attachments: got {len(got)} ({[a['filename'] for a in got]}), want {len(want)}")
            for g, w in zip(got, want):
                for k, v in w.items():
                    check(g.get(k) == v, f"attachment {k}: got {g.get(k)!r}, want {v!r}")
        elif key == "inline_parts":
            got = [p["content_id"] for p in summary["inline_parts"]]
            check(got == want, f"inline_parts: got {got!r}, want {want!r}")
        elif key == "attached_message_subjects":
            got = [m["subject"] for m in summary["attached_messages"]]
            check(got == want, f"attached messages: got {got!r}, want {want!r}")
        elif key == "calendar":
            check(summary["calendar"] == want, f"calendar: got {summary['calendar']!r}, want {want!r}")
        elif key == "html_dangerous_at_least":
            missing = sorted(set(want) - set(hf["dangerous"]))
            check(not missing, f"dangerous HTML constructs not detected: {missing}")
        elif key == "html_dangerous_none":
            check(not hf["dangerous"], f"unexpected dangerous HTML: {hf['dangerous']}")
        elif key == "remote_resources":
            check(hf["remote_resources"] == want, f"remote_resources: got {hf['remote_resources']}, want {want}")
        elif key == "tracking_pixels":
            check(hf["tracking_pixels"] == want, f"tracking_pixels: got {hf['tracking_pixels']}, want {want}")
        elif key == "mismatched_links_min":
            check(len(hf["mismatched_links"]) >= want, f"mismatched links: got {len(hf['mismatched_links'])}, want >= {want}")
        elif key == "defects_include":
            missing = sorted(set(want) - set(summary["defects"]))
            check(not missing, f"defects not reported: {missing} (got {summary['defects']})")
        elif key == "warnings_include":
            joined = " | ".join(summary["warnings"])
            for s in want:
                check(s in joined, f"warning {s!r} not raised (got {summary['warnings']})")
        else:
            errs.append(f"unknown expectation key {key!r} (document it in generate_synthetic.EXPECT_KEYS_DOC)")
    return errs

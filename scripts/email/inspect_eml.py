#!/usr/bin/env python3
"""Explain a raw email: decoded headers, MIME tree, body choice, attachments, risky HTML.

Usage:
  python3 scripts/email/inspect_eml.py MESSAGE.eml            # human-readable report
  python3 scripts/email/inspect_eml.py MESSAGE.eml --json     # full summary (same shape the conformance tests use)
  python3 scripts/email/inspect_eml.py MESSAGE.eml --body     # also print decoded text body

Use it to debug "this email renders wrong" reports and to draft manifest expectations for
new fixtures (/email-fixture). Never paste real staff email into issues — anonymize first
(scripts/email/anonymize_eml.py).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import emaillib  # noqa: E402


def fmt_addrs(items):
    return ", ".join(f'{a["name"]} <{a["address"]}>' if a["name"] else a["address"] for a in items) or "-"


def report(path: Path, show_body: bool) -> str:
    raw = emaillib.load_bytes(path)
    s = emaillib.summarize(emaillib.parse_bytes(raw), raw)
    out = [f"# {path.name}  ({s['size']} bytes, {s['line_endings']} line endings)", ""]
    out.append(f"Subject:     {s['subject']!r}")
    out.append(f"Normalized:  {s['normalized_subject']!r}")
    out.append(f"From:        {fmt_addrs(s['from'])}")
    out.append(f"To:          {fmt_addrs(s['to'])}")
    if s["cc"]:
        out.append(f"Cc:          {fmt_addrs(s['cc'])}")
    out.append(f"Date (UTC):  {s['date'] or '- (missing/unparseable: fall back to INTERNALDATE)'}")
    out.append(f"Message-ID:  {s['message_id'] or '-'}")
    if s["in_reply_to"] or s["references"]:
        out.append(f"In-Reply-To: {s['in_reply_to'] or '-'}")
        out.append(f"References:  {' '.join(s['references']) or '-'}")
    out += ["", "MIME tree:"]
    for p in s["parts"]:
        depth = 0 if p["path"] in ("root",) else p["path"].count(".") + 1
        extra = []
        for key in ("charset", "transfer_encoding", "disposition", "filename", "content_id"):
            if p.get(key):
                extra.append(f"{key}={p[key]}")
        if "size" in p:
            extra.append(f"{p['size']}B")
        out.append(f"  {'  ' * depth}[{p['path']}] {p['content_type']}  {' '.join(extra)}")
    out += ["", f"Shows by default: {s['body']['preferred'] or 'nothing (no text part)'}"]
    out.append(f"Attachments ({len(s['attachments'])}):")
    for a in s["attachments"]:
        out.append(f"  - {a['filename']!r} {a['content_type']} {a.get('size', '?')}B")
    if s["inline_parts"]:
        out.append("Inline parts: " + ", ".join(f"cid:{p['content_id']} ({p['content_type']})" for p in s["inline_parts"]))
    if s["attached_messages"]:
        out.append("Attached messages: " + ", ".join(repr(m["subject"]) for m in s["attached_messages"]))
    if s["calendar"]:
        out.append(f"Calendar: method={s['calendar']['method']} summary={s['calendar']['summary']!r}")
    hf = s["html_findings"]
    if hf:
        out += ["", "HTML risk (what the sanitizer must neutralize):"]
        out.append(f"  dangerous constructs: {hf['dangerous'] or 'none'}")
        out.append(f"  remote resources: {hf['remote_resources']} (tracking pixels: {hf['tracking_pixels']})")
        for m in hf["mismatched_links"]:
            out.append(f"  link text shows {m['text_host']} but points to {m['href_host']}  <- phishing signal")
    if s["defects"]:
        out.append(f"\nParser defects: {', '.join(s['defects'])}")
    if s["warnings"]:
        out.append("Warnings:")
        out += [f"  - {w}" for w in s["warnings"]]
    if show_body:
        out += ["", "----- decoded text body -----", s["body"]["text"] or "(none)"]
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--json", action="store_true", help="print the machine-readable summary")
    ap.add_argument("--body", action="store_true", help="include the decoded text body")
    args = ap.parse_args(argv)
    rc = 0
    for f in args.files:
        if not f.is_file():
            print(f"not a file: {f}", file=sys.stderr)
            rc = 1
            continue
        if args.json:
            raw = emaillib.load_bytes(f)
            summary = emaillib.summarize(emaillib.parse_bytes(raw), raw)
            if not args.body:
                summary["body"] = {k: (v if k == "preferred" else (len(v) if v else None)) for k, v in summary["body"].items()}
            print(json.dumps(summary, ensure_ascii=False, indent=2))
        else:
            print(report(f, args.body))
            print()
    return rc


if __name__ == "__main__":
    sys.exit(main())

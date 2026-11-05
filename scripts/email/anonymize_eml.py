#!/usr/bin/env python3
"""Anonymize a real email so it can become a test fixture without leaking staff or customer data.

Usage:
  python3 scripts/email/anonymize_eml.py IN.eml -o fixtures/email/NNN-slug.eml [--redact-text] [--keep-attachments]

What it does (deterministic: the same input always gives the same output):
  - Addresses -> stable fakes: internal domain -> @isupply.test, everything else -> @example.com/.org
  - Display names -> "Person N"; Subject keeps its structure (prefixes, encoding) but words are redacted
    when --redact-text is given
  - Drops tracing/auth headers (Received, DKIM-Signature, ARC-*, Authentication-Results, X-Originating-IP, ...)
  - Bodies: emails, phone numbers, IBAN-like and long digit runs replaced; URL hosts -> example.com
  - --redact-text: also replaces letters with same-script placeholders (Arabic stays Arabic so RTL/bidi
    bugs still reproduce; Latin becomes x/X), preserving length, punctuation and markup
  - Attachments: content replaced with same-size placeholder bytes and names with attachment-N.ext
    (keep the real bytes only with --keep-attachments, and only if they contain nothing sensitive)

ALWAYS review the output manually before committing (scripts/email/inspect_eml.py OUT.eml --body).
Re-serialization may normalize some structural quirks (folding, malformed boundaries): confirm the
bug you are capturing still reproduces with the anonymized file.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from email import policy
from email.message import Message
from email.parser import BytesParser
from pathlib import Path

INTERNAL_DOMAINS = {"isupply.com.eg", "isupply.com", "isupply.test"}
DROP_HEADERS = {
    "received", "dkim-signature", "x-google-dkim-signature", "arc-seal", "arc-message-signature",
    "arc-authentication-results", "authentication-results", "received-spf", "x-originating-ip",
    "x-ms-exchange-organization-authas", "x-ms-exchange-crosstenant-id", "x-forefront-antispam-report",
    "x-microsoft-antispam", "x-microsoft-antispam-message-info", "x-ms-traffictypediagnostic",
    "x-gm-message-state", "x-google-smtp-source", "x-received", "return-path", "delivered-to",
    "x-sender", "x-mailer-sender", "x-originating-email", "x-ms-exchange-organization-network-message-id",
}
ADDRESS_HEADERS = {"from", "to", "cc", "bcc", "reply-to", "sender", "resent-from", "resent-to", "disposition-notification-to"}
EMAIL_RE = re.compile(r"(?<![\w.%+\-])(?<!cid:)[A-Za-z0-9._%+\-]+@([A-Za-z0-9\-]+\.)+[A-Za-z]{2,}")
CID_REF_RE = re.compile(r"(cid:[^@\s\"'<>()]+)@[^\s\"'<>()]+", re.IGNORECASE)
CID_HEADER_RE = re.compile(r"<([^@<>]+)@[^<>]+>")
CID_DOMAIN = "anon.isupply.test"
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s\-().]{7,}\d)(?!\w)")
IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b")
LONG_DIGITS_RE = re.compile(r"\b\d{9,}\b")
URL_HOST_RE = re.compile(r"(https?://)([^/\s\"'<>:]+)", re.IGNORECASE)


class Anonymizer:
    def __init__(self, salt: str = "isupply-fixtures") -> None:
        self.salt = salt
        self.names: dict = {}

    def _h(self, value: str) -> str:
        return hashlib.sha256((self.salt + value.lower()).encode("utf-8")).hexdigest()[:6]

    def address(self, addr: str) -> str:
        local, _, domain = addr.rpartition("@")
        domain = domain.lower()
        if domain in INTERNAL_DOMAINS or domain.endswith((".isupply.com.eg", ".isupply.com")):
            return f"user-{self._h(addr)}@isupply.test"
        tld = "org" if int(self._h(domain), 16) % 2 else "com"
        return f"user-{self._h(addr)}@example.{tld}"

    def name(self, display: str) -> str:
        if not display:
            return ""
        key = display.strip().lower()
        if key not in self.names:
            self.names[key] = f"Person {len(self.names) + 1}"
        return self.names[key]

    def text(self, s: str, redact_letters: bool) -> str:
        s = CID_REF_RE.sub(lambda m: f"{m.group(1)}@{CID_DOMAIN}", s)  # keep cid: links intact
        s = EMAIL_RE.sub(lambda m: self.address(m.group(0)), s)
        s = URL_HOST_RE.sub(lambda m: m.group(1) + ("example.com" if "isupply" not in m.group(2).lower() else "intranet.isupply.test"), s)
        s = IBAN_RE.sub(lambda m: "XX00" + "0" * (len(m.group(0)) - 4), s)
        s = PHONE_RE.sub(lambda m: re.sub(r"\d", "5", m.group(0)), s)
        s = LONG_DIGITS_RE.sub(lambda m: "9" * len(m.group(0)), s)
        if redact_letters:
            s = redact_script(s)
        return s


def redact_script(s: str) -> str:
    """Replace letters but keep script, case, length, digits, punctuation and HTML/CSS syntax."""
    out = []
    in_tag = False
    for ch in s:
        if ch == "<":
            in_tag = True
        elif ch == ">":
            in_tag = False
        if in_tag:
            out.append(ch)
            continue
        o = ord(ch)
        if 0x0621 <= o <= 0x064A:  # Arabic letters -> Arabic placeholder letter (keeps RTL behaviour)
            out.append("س")
        elif "a" <= ch <= "z":
            out.append("x")
        elif "A" <= ch <= "Z":
            out.append("X")
        else:
            out.append(ch)
    return "".join(out)


def anonymize_message(msg: Message, an: Anonymizer, redact_text: bool, keep_attachments: bool, counter: list) -> None:
    for name in list(msg.keys()):
        if name.lower() in DROP_HEADERS:
            del msg[name]
    for name in list(msg.keys()):
        lname = name.lower()
        if lname in ADDRESS_HEADERS:
            values = msg.get_all(name, [])
            del msg[name]
            for v in values:
                try:
                    addrs = v.addresses  # type: ignore[attr-defined]
                    rendered = ", ".join(
                        (f'"{an.name(a.display_name)}" <{an.address(a.addr_spec)}>' if a.display_name else an.address(a.addr_spec))
                        for a in addrs if a.addr_spec
                    ) or "undisclosed-recipients:;"
                except AttributeError:
                    rendered = an.text(str(v), False)
                msg[name] = rendered
        elif lname == "subject" and redact_text:
            subj = str(msg[name])
            del msg[name]
            m = re.match(r"^((?:\s*(?:re|fw|fwd|aw|rv|tr|رد)\s*:\s*)*)(.*)$", subj, re.IGNORECASE)
            prefix, rest = (m.group(1), m.group(2)) if m else ("", subj)
            msg[name] = prefix + an.text(rest, True)
        elif lname in ("message-id", "in-reply-to", "references"):
            v = str(msg[name])
            del msg[name]
            msg[name] = re.sub(r"<([^@<>]+)@([^<>]+)>", lambda mm: f"<{an._h(mm.group(0))}@anon.isupply.test>", v)

    if msg.is_multipart():
        for part in msg.get_payload():  # type: ignore[union-attr]
            if isinstance(part, Message):
                anonymize_message(part, an, redact_text, keep_attachments, counter)
        return

    ctype = msg.get_content_type()
    disposition = (msg.get("Content-Disposition") or "").split(";")[0].strip().lower()
    filename = msg.get_filename()
    if disposition == "attachment" or (filename and not ctype.startswith("text/")):
        counter[0] += 1
        ext = Path(filename).suffix if filename else ""
        if not keep_attachments:
            size = len(msg.get_payload(decode=True) or b"")
            maintype, subtype = ctype.split("/", 1)
            content_id = msg.get("Content-ID")  # set_content() clears headers; inline parts need their cid
            if content_id:
                content_id = CID_HEADER_RE.sub(lambda m: f"<{m.group(1)}@{CID_DOMAIN}>", str(content_id))
            msg.set_content(b"\0" * size, maintype=maintype, subtype=subtype,
                            disposition=disposition or "attachment", filename=f"attachment-{counter[0]}{ext}")
            if content_id:
                msg["Content-ID"] = content_id
        return
    if ctype in ("text/plain", "text/html"):
        try:
            text = msg.get_content()
        except (LookupError, UnicodeDecodeError):
            return  # leave undecodable text untouched, report via inspect_eml
        new = an.text(text, redact_text)
        if new != text:
            charset = msg.get_content_charset() or "utf-8"
            try:
                new.encode(charset)
            except (LookupError, UnicodeEncodeError):
                charset = "utf-8"
            cte = "base64" if (msg.get("Content-Transfer-Encoding") or "").lower() == "base64" else "quoted-printable"
            msg.set_content(new, subtype=ctype.split("/")[1], charset=charset, cte=cte)


def anonymize_bytes(raw: bytes, redact_text: bool = False, keep_attachments: bool = False, salt: str = "isupply-fixtures") -> bytes:
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    anonymize_message(msg, Anonymizer(salt), redact_text, keep_attachments, [0])
    return msg.as_bytes(policy=policy.default.clone(linesep="\r\n"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path)
    ap.add_argument("-o", "--output", type=Path, required=True)
    ap.add_argument("--redact-text", action="store_true", help="also redact words (keeps script/length)")
    ap.add_argument("--keep-attachments", action="store_true", help="keep real attachment bytes (review them!)")
    ap.add_argument("--salt", default="isupply-fixtures", help="change to get different fake identities")
    args = ap.parse_args(argv)
    if args.output.resolve() == args.input.resolve():
        print("refusing to overwrite the input file", file=sys.stderr)
        return 2
    out = anonymize_bytes(args.input.read_bytes(), args.redact_text, args.keep_attachments, args.salt)
    args.output.write_bytes(out)
    print(f"wrote {args.output} ({len(out)} bytes). Review it before committing:\n"
          f"  python3 scripts/email/inspect_eml.py {args.output} --body")
    return 0


if __name__ == "__main__":
    sys.exit(main())

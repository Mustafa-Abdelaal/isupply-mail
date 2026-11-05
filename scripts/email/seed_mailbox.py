#!/usr/bin/env python3
"""Seed / inspect the LOCAL dev mail server (infra/dev-mail). Refuses non-local hosts by default.

Usage (normally via scripts/dev-mail):
  python3 scripts/email/seed_mailbox.py seed [--bulk N] [--user U --password P]
  python3 scripts/email/seed_mailbox.py send [--from bob@isupply.test] [--to alice@isupply.test] [--subject S] [--body B]
  python3 scripts/email/seed_mailbox.py status

seed:   creates the folder tree (incl. an Arabic folder name -> IMAP modified UTF-7 on the wire) using the
        server's real hierarchy delimiter, then APPENDs every fixture from fixtures/email/manifest.json into
        its seed folder with its flags. --bulk N adds N generated messages to "Bulk" for performance work.
send:   submits a message over SMTP (exercises new-mail notification / IDLE paths in the app).
status: per-folder message counts.
"""

from __future__ import annotations

import argparse
import imaplib
import json
import os
import random
import re
import smtplib
import sys
import time
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid, parsedate_to_datetime
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import emaillib  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "fixtures" / "email" / "manifest.json"
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1", "greenmail", "host.docker.internal"}
# Logical folder paths ("/" separated). Mapped onto the server's delimiter at runtime.
FOLDERS = ["Archive", "Reports", "Junk", "Sent", "Drafts", "Trash", "Projects", "Projects/2026", "تقارير"]


def env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def connect(args: argparse.Namespace) -> imaplib.IMAP4:
    if args.host not in LOCAL_HOSTS and not args.allow_remote:
        sys.exit(f"refusing to touch non-local host {args.host!r}: this tool seeds throwaway dev mailboxes only")
    conn = imaplib.IMAP4(args.host, args.imap_port, timeout=15)
    conn.login(args.user, args.password)
    return conn


def server_delimiter(conn: imaplib.IMAP4) -> str:
    typ, data = conn.list('""', '""')
    if typ == "OK" and data and data[0]:
        m = re.match(rb'\([^)]*\) "(.)"', data[0])
        if m:
            return m.group(1).decode()
    return "/"


def wire_name(logical: str, delim: str) -> str:
    name = emaillib.imap_utf7_encode(logical.replace("/", delim))
    return '"' + name.replace("\\", "\\\\").replace('"', '\\"') + '"'


def ensure_folders(conn: imaplib.IMAP4, delim: str) -> List[str]:
    """Create the folder tree; existing folders are left alone (CREATE returns NO)."""
    created = []
    for logical in FOLDERS:
        name = wire_name(logical, delim)
        typ, _ = conn.create(name)
        if typ == "OK":
            created.append(logical)
    return created


def seed(args: argparse.Namespace) -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    conn = connect(args)
    delim = server_delimiter(conn)
    created = ensure_folders(conn, delim)
    counts: Dict[str, int] = {}
    for entry in manifest["fixtures"]:
        raw = (MANIFEST.parent / entry["file"]).read_bytes()
        if b"\r\n" not in raw:
            raw = raw.replace(b"\n", b"\r\n")  # IMAP APPEND requires CRLF
        seed_cfg = entry.get("seed", {})
        folder = seed_cfg.get("folder", "INBOX")
        flags = "(" + " ".join(seed_cfg.get("flags", [])) + ")"
        try:
            when = parsedate_to_datetime(emaillib.header_text(emaillib.parse_bytes(raw), "Date") or "")
            internal = imaplib.Time2Internaldate(when.timestamp())
        except (TypeError, ValueError):
            internal = imaplib.Time2Internaldate(time.time())
        mailbox = "INBOX" if folder == "INBOX" else wire_name(folder, delim)
        typ, data = conn.append(mailbox, flags, internal, raw)
        if typ != "OK":
            print(f"APPEND {entry['file']} -> {folder} failed: {data}", file=sys.stderr)
            continue
        counts[folder] = counts.get(folder, 0) + 1
    if args.bulk:
        rnd = random.Random(20260101)
        senders = ["omar.farouk", "sara.hassan", "mona.adel", "karim.nabil", "ahmed.samir"]
        topics = ["Stock count", "Delivery schedule", "Invoice", "Price list", "تقرير المبيعات", "Meeting notes", "Supplier quote"]
        bulk = wire_name("Bulk", delim)
        conn.create(bulk)
        base = time.time() - args.bulk * 600
        for i in range(args.bulk):
            m = EmailMessage()
            sender = rnd.choice(senders)
            m["From"] = f"{sender.replace('.', ' ').title()} <{sender}@isupply.test>"
            m["To"] = args.user
            m["Subject"] = f"{rnd.choice(topics)} #{i + 1}"
            ts = base + i * 600
            m["Date"] = format_datetime(__import__("datetime").datetime.fromtimestamp(ts).astimezone())
            m["Message-ID"] = make_msgid(idstring=f"bulk{i}", domain="isupply.test")
            m.set_content(f"Synthetic bulk message {i + 1} of {args.bulk} for performance testing.\n")
            flags = "(\\Seen)" if rnd.random() < 0.7 else "()"
            conn.append(bulk, flags, imaplib.Time2Internaldate(ts), m.as_bytes(policy=m.policy.clone(linesep="\r\n")))
        counts["Bulk"] = args.bulk
    conn.logout()
    print(json.dumps({"user": args.user, "delimiter": delim, "folders_created": created, "appended": counts}, ensure_ascii=False))
    return 0


def send(args: argparse.Namespace) -> int:
    if args.host not in LOCAL_HOSTS and not args.allow_remote:
        sys.exit(f"refusing to send through non-local host {args.host!r}")
    m = EmailMessage()
    m["From"] = args.sender
    m["To"] = args.to
    m["Subject"] = args.subject
    m["Date"] = format_datetime(__import__("datetime").datetime.now().astimezone())
    m["Message-ID"] = make_msgid(domain="isupply.test")
    m.set_content(args.body)
    with smtplib.SMTP(args.host, args.smtp_port, timeout=15) as s:
        s.send_message(m)
    print(json.dumps({"sent": True, "from": args.sender, "to": args.to, "subject": args.subject, "message_id": m["Message-ID"]}))
    return 0


def status(args: argparse.Namespace) -> int:
    conn = connect(args)
    typ, data = conn.list()
    rows: List[Tuple[str, str]] = []
    for line in data or []:
        m = re.match(rb'\([^)]*\) "(.)" (.+)$', line or b"")
        if not m:
            continue
        wire = m.group(2).decode().strip('"')
        typ2, st = conn.status('"' + wire + '"', "(MESSAGES UNSEEN)")
        rows.append((emaillib.imap_utf7_decode(wire), st[0].decode() if typ2 == "OK" else "?"))
    conn.logout()
    for name, st in sorted(rows):
        counts = re.search(r"MESSAGES (\d+) UNSEEN (\d+)", st)
        print(f"{name:30s} {counts.group(1) + ' messages, ' + counts.group(2) + ' unseen' if counts else st}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["seed", "send", "status"])
    ap.add_argument("--host", default=env("DEV_MAIL_HOST", "127.0.0.1"))
    ap.add_argument("--imap-port", type=int, default=int(env("DEV_MAIL_IMAP_PORT", "3143")))
    ap.add_argument("--smtp-port", type=int, default=int(env("DEV_MAIL_SMTP_PORT", "3025")))
    ap.add_argument("--user", default=env("DEV_MAIL_USER", "alice@isupply.test"))
    ap.add_argument("--password", default=env("DEV_MAIL_PASSWORD", "alice-dev-pw"), help="dev server password (throwaway)")
    ap.add_argument("--allow-remote", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--bulk", type=int, default=0)
    ap.add_argument("--from", dest="sender", default="bob@isupply.test")
    ap.add_argument("--to", default="alice@isupply.test")
    ap.add_argument("--subject", default="Test message from scripts/dev-mail send")
    ap.add_argument("--body", default="Hello from the dev mail server.\n")
    args = ap.parse_args(argv)
    return {"seed": seed, "send": send, "status": status}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())

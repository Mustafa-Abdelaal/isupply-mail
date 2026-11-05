#!/usr/bin/env python3
"""Probe IMAP and SMTP servers: TLS, certificate, capabilities, auth mechanisms, folders.

Usage:
  python3 scripts/email/probe_server.py --imap HOST[:PORT] [--smtp HOST[:PORT]]
      [--imap-security ssl|starttls|plain] [--smtp-security ssl|starttls|plain]
      [--user ADDRESS --password-env VAR] [--insecure] [--json]

Defaults: IMAP 993/ssl, SMTP 465/ssl. Port 143/587 imply starttls; 3143/3025 (local dev server) imply plain.
Credentials are read from an environment variable — never pass passwords as arguments
(they end up in shell history, process lists and agent transcripts). Without credentials
only pre-authentication data is collected. Nothing is ever sent or modified.

--insecure disables certificate verification: only for the local dev server.
"""

from __future__ import annotations

import argparse
import imaplib
import json
import os
import re
import smtplib
import socket
import ssl
import sys
from typing import Any, Dict, Optional, Tuple

IMAP_INTERESTING = ["IMAP4REV2", "IDLE", "CONDSTORE", "QRESYNC", "MOVE", "UIDPLUS", "SPECIAL-USE", "LIST-STATUS",
                    "NAMESPACE", "ID", "ENABLE", "UTF8=ACCEPT", "COMPRESS=DEFLATE", "ESEARCH", "SORT", "THREAD=REFERENCES",
                    "LITERAL+", "QUOTA", "NOTIFY", "OBJECTID", "STARTTLS", "LOGINDISABLED"]


def split_hostport(value: str, default_port: int) -> Tuple[str, int]:
    if value.count(":") == 1:
        host, port = value.split(":")
        return host, int(port)
    return value, default_port


def default_security(port: int) -> str:
    return {993: "ssl", 465: "ssl", 143: "starttls", 587: "starttls", 3143: "plain", 3025: "plain", 3993: "ssl", 3465: "ssl"}.get(port, "ssl")


def tls_context(insecure: bool) -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    if insecure:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def tls_info(sock: Any, host: str, verified: bool) -> Dict[str, Any]:
    if not isinstance(sock, ssl.SSLSocket):
        return {"tls": False}
    info: Dict[str, Any] = {"tls": True, "version": sock.version(), "cipher": (sock.cipher() or ("?",))[0], "verified": verified}
    cert = sock.getpeercert() if verified else None
    if cert:
        info["subject_cn"] = next((v for rdn in cert.get("subject", ()) for k, v in rdn if k == "commonName"), None)
        info["san"] = [v for k, v in cert.get("subjectAltName", ()) if k == "DNS"]
        info["not_after"] = cert.get("notAfter")
        info["issuer_o"] = next((v for rdn in cert.get("issuer", ()) for k, v in rdn if k == "organizationName"), None)
    elif not verified:
        info["note"] = "certificate NOT verified (--insecure)"
    return info


def probe_imap(host: str, port: int, security: str, user: Optional[str], password: Optional[str], insecure: bool, timeout: float) -> Dict[str, Any]:
    r: Dict[str, Any] = {"host": host, "port": port, "security": security}
    ctx = tls_context(insecure)
    try:
        if security == "ssl":
            conn = imaplib.IMAP4_SSL(host, port, ssl_context=ctx, timeout=timeout)
        else:
            conn = imaplib.IMAP4(host, port, timeout=timeout)
            if security == "starttls":
                conn.starttls(ssl_context=ctx)
    except (OSError, imaplib.IMAP4.error, ssl.SSLError) as e:
        r["error"] = f"connect failed: {e}"
        return r
    r["greeting"] = conn.welcome.decode("utf-8", "replace")[:200] if isinstance(conn.welcome, bytes) else str(conn.welcome)[:200]
    r["tls"] = tls_info(conn.sock, host, not insecure)
    caps = set(conn.capabilities)
    r["capabilities_pre_auth"] = sorted(caps)
    if "AUTH=PLAIN" not in caps and not any(c.startswith("AUTH=") for c in caps):
        r["auth_mechanisms"] = ["LOGIN (command)"]
    else:
        r["auth_mechanisms"] = sorted(c[5:] for c in caps if c.startswith("AUTH="))
    if user and password:
        try:
            conn.login(user, password)
            r["login"] = "ok"
            typ, data = conn.capability()
            caps = set(data[0].decode().upper().split()) if typ == "OK" and data and data[0] else caps
            r["capabilities"] = sorted(caps)
            r["supports"] = {c: (c in caps) for c in IMAP_INTERESTING}
            typ, data = conn.list()
            folders = []
            for line in data or []:
                m = re.match(rb'\((?P<flags>[^)]*)\) (?P<delim>"[^"]*"|NIL) (?P<name>.+)$', line or b"")
                if m:
                    folders.append({"name": m.group("name").decode("utf-8", "replace").strip('"'),
                                    "delimiter": m.group("delim").decode().strip('"'),
                                    "flags": m.group("flags").decode().split()})
            r["folders"] = folders
            r["special_use"] = {f["name"]: [x for x in f["flags"] if x in ("\\Sent", "\\Drafts", "\\Trash", "\\Junk", "\\Archive", "\\All", "\\Flagged")]
                                for f in folders if any(x in f["flags"] for x in ("\\Sent", "\\Drafts", "\\Trash", "\\Junk", "\\Archive", "\\All"))}
            typ, data = conn.status("INBOX", "(MESSAGES UIDNEXT UIDVALIDITY UNSEEN)")
            r["inbox_status"] = data[0].decode("utf-8", "replace") if typ == "OK" and data else None
        except imaplib.IMAP4.error as e:
            r["login"] = f"failed: {e}"
    else:
        r["supports"] = {c: (c in caps) for c in IMAP_INTERESTING}
    try:
        conn.logout()
    except (OSError, imaplib.IMAP4.error):
        pass
    return r


def probe_smtp(host: str, port: int, security: str, user: Optional[str], password: Optional[str], insecure: bool, timeout: float) -> Dict[str, Any]:
    r: Dict[str, Any] = {"host": host, "port": port, "security": security}
    ctx = tls_context(insecure)
    try:
        if security == "ssl":
            conn = smtplib.SMTP_SSL(host, port, context=ctx, timeout=timeout)
        else:
            conn = smtplib.SMTP(host, port, timeout=timeout)
        code, banner = conn.ehlo("probe.isupply.test")
        r["banner"] = banner.decode("utf-8", "replace").splitlines()[0][:200]
        if security == "starttls":
            conn.starttls(context=ctx)
            conn.ehlo("probe.isupply.test")
    except (OSError, smtplib.SMTPException, ssl.SSLError) as e:
        r["error"] = f"connect failed: {e}"
        return r
    r["tls"] = tls_info(conn.sock, host, not insecure)
    features = {k.upper(): v for k, v in conn.esmtp_features.items()}
    r["extensions"] = sorted(features)
    r["auth_mechanisms"] = features.get("AUTH", "").split()
    size = features.get("SIZE", "").strip()
    r["max_message_size_bytes"] = int(size) if size.isdigit() else None
    r["supports"] = {k: (k in features) for k in ("PIPELINING", "8BITMIME", "SMTPUTF8", "CHUNKING", "DSN", "ENHANCEDSTATUSCODES", "STARTTLS")}
    if user and password:
        try:
            conn.login(user, password)
            r["login"] = "ok"
        except smtplib.SMTPException as e:
            r["login"] = f"failed: {e}"
    try:
        conn.quit()
    except (OSError, smtplib.SMTPException):
        pass
    return r


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--imap")
    ap.add_argument("--smtp")
    ap.add_argument("--imap-security", choices=["ssl", "starttls", "plain"])
    ap.add_argument("--smtp-security", choices=["ssl", "starttls", "plain"])
    ap.add_argument("--user")
    ap.add_argument("--password-env", help="name of the environment variable holding the password")
    ap.add_argument("--insecure", action="store_true", help="skip certificate verification (local dev server only)")
    ap.add_argument("--timeout", type=float, default=10.0)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if not args.imap and not args.smtp:
        ap.error("give --imap and/or --smtp")
    password = os.environ.get(args.password_env) if args.password_env else None
    if args.user and args.password_env and password is None:
        ap.error(f"environment variable {args.password_env} is not set")
    socket.setdefaulttimeout(args.timeout)
    out: Dict[str, Any] = {}
    if args.imap:
        host, port = split_hostport(args.imap, 993)
        out["imap"] = probe_imap(host, port, args.imap_security or default_security(port), args.user, password, args.insecure, args.timeout)
    if args.smtp:
        host, port = split_hostport(args.smtp, 465)
        out["smtp"] = probe_smtp(host, port, args.smtp_security or default_security(port), args.user, password, args.insecure, args.timeout)
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        for proto, res in out.items():
            print(f"## {proto.upper()} {res['host']}:{res['port']} ({res['security']})")
            for k, v in res.items():
                if k in ("host", "port", "security"):
                    continue
                print(f"- {k}: {v}")
            print()
    return 1 if any("error" in r for r in out.values()) else 0


if __name__ == "__main__":
    sys.exit(main())

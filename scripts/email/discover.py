#!/usr/bin/env python3
"""Discover IMAP/SMTP (and JMAP) settings for an email domain — research tool for zero-config login.

Usage:
  python3 scripts/email/discover.py isupply.com [--email someone@isupply.com] [--json] [--timeout 8]

Sources, most trusted first:
  1. Domain-published autoconfig XML (https://autoconfig.<domain>/..., /.well-known/autoconfig/...)
  2. Mozilla Thunderbird ISPDB (https://autoconfig.thunderbird.net/v1.1/<domain>)
  3. DNS SRV records — RFC 6186 / RFC 8314 (_submissions, _submission, _imaps, _imap) and _jmap (RFC 8620)
  4. MX-record provider fingerprints (Google Workspace, Microsoft 365, Zoho, GoDaddy, Titan, ...)
  5. Conventional hostnames (mail./imap./smtp.<domain>) that resolve

DNS: uses dnspython or `dig` when available, else DNS-over-HTTPS (Google/Cloudflare JSON API).
Results are *candidates*: verify with scripts/email/probe_server.py before baking them into the app.
See docs/domain/discovery-and-auth.md for how the app itself should provision @isupply.com.
"""

from __future__ import annotations

import argparse
import json
import shutil
import socket
import subprocess
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

DOH_ENDPOINTS = ["https://dns.google/resolve", "https://cloudflare-dns.com/dns-query"]
RTYPES = {"A": 1, "MX": 15, "TXT": 16, "SRV": 33}

# (provider id, MX suffixes, settings, notes). Settings are well-known public values; still probe them.
PROVIDERS: List[Tuple[str, Tuple[str, ...], Dict[str, Any], str]] = [
    ("google-workspace", ("google.com", "googlemail.com"),
     {"imap": ("imap.gmail.com", 993, "SSL"), "smtp": ("smtp.gmail.com", 465, "SSL")},
     "OAuth2 (XOAUTH2) expected; passwords only via app passwords with 2-Step Verification."),
    ("microsoft-365", ("mail.protection.outlook.com", "outlook.com"),
     {"imap": ("outlook.office365.com", 993, "SSL"), "smtp": ("smtp.office365.com", 587, "STARTTLS")},
     "Basic auth is disabled: OAuth2 (Modern Auth) required. Consider Microsoft Graph/EWS instead of IMAP."),
    ("zoho", ("zoho.com", "zoho.eu", "zoho.in", "zohomail.com"),
     {"imap": ("imap.zoho.com", 993, "SSL"), "smtp": ("smtp.zoho.com", 465, "SSL")},
     "Organization accounts use imappro.zoho.com / smtppro.zoho.com; region-specific hosts exist (.eu/.in)."),
    ("godaddy", ("secureserver.net",),
     {"imap": ("imap.secureserver.net", 993, "SSL"), "smtp": ("smtpout.secureserver.net", 465, "SSL")},
     "GoDaddy Workspace Email; newer GoDaddy plans are Microsoft 365 (check MX)."),
    ("titan", ("titan.email",),
     {"imap": ("imap.titan.email", 993, "SSL"), "smtp": ("smtp.titan.email", 465, "SSL")}, ""),
    ("hostinger", ("hostinger.com",),
     {"imap": ("imap.hostinger.com", 993, "SSL"), "smtp": ("smtp.hostinger.com", 465, "SSL")}, ""),
    ("yandex", ("yandex.net", "yandex.ru"),
     {"imap": ("imap.yandex.com", 993, "SSL"), "smtp": ("smtp.yandex.com", 465, "SSL")}, ""),
    ("icloud", ("mail.icloud.com",),
     {"imap": ("imap.mail.me.com", 993, "SSL"), "smtp": ("smtp.mail.me.com", 587, "STARTTLS")},
     "App-specific passwords required."),
    ("fastmail", ("messagingengine.com",),
     {"imap": ("imap.fastmail.com", 993, "SSL"), "smtp": ("smtp.fastmail.com", 465, "SSL")},
     "JMAP available (https://api.fastmail.com/jmap/session)."),
]


# ---------------------------------------------------------------------------
# DNS
# ---------------------------------------------------------------------------


def parse_answer_data(rtype: str, lines: List[str]) -> List[Any]:
    """Parse dig +short / DoH 'data' strings into structured records."""
    out: List[Any] = []
    for line in lines:
        parts = line.strip().split()
        if not parts:
            continue
        try:
            if rtype == "MX" and len(parts) >= 2:
                out.append({"priority": int(parts[0]), "host": parts[1].rstrip(".").lower()})
            elif rtype == "SRV" and len(parts) >= 4:
                target = parts[3].rstrip(".").lower()
                if target:  # "." target means "service not available" (RFC 2782)
                    out.append({"priority": int(parts[0]), "weight": int(parts[1]), "port": int(parts[2]), "host": target})
            elif rtype == "TXT":
                out.append(line.strip().strip('"'))
            elif rtype == "A":
                out.append(parts[0])
        except ValueError:
            continue
    if rtype in ("MX", "SRV"):
        out.sort(key=lambda r: (r["priority"], -r.get("weight", 0)))
    return out


def resolve(name: str, rtype: str, timeout: float) -> Tuple[List[Any], str]:
    try:
        import dns.resolver  # type: ignore

        answers = dns.resolver.resolve(name, rtype, lifetime=timeout)
        return parse_answer_data(rtype, [a.to_text() for a in answers]), "dnspython"
    except ImportError:
        pass
    except Exception:  # noqa: BLE001 - NXDOMAIN/NoAnswer -> empty
        return [], "dnspython"
    if shutil.which("dig"):
        try:
            r = subprocess.run(["dig", "+short", "+time=3", "+tries=1", rtype, name], capture_output=True, text=True, timeout=timeout)
            if r.returncode == 0:
                return parse_answer_data(rtype, r.stdout.splitlines()), "dig"
        except (OSError, subprocess.TimeoutExpired):
            pass
    for endpoint in DOH_ENDPOINTS:
        url = f"{endpoint}?{urllib.parse.urlencode({'name': name, 'type': rtype})}"
        try:
            req = urllib.request.Request(url, headers={"accept": "application/dns-json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.load(resp)
            lines = [a.get("data", "") for a in data.get("Answer", []) if a.get("type") == RTYPES[rtype]]
            return parse_answer_data(rtype, lines), "doh"
        except Exception:  # noqa: BLE001
            continue
    return [], "unavailable"


# ---------------------------------------------------------------------------
# Autoconfig (Thunderbird clientConfig v1.1)
# ---------------------------------------------------------------------------


def parse_autoconfig(xml_text: str, email_addr: str = "") -> List[Dict[str, Any]]:
    """Parse clientConfig XML into server entries. Placeholders are expanded for the given address."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    local, _, domain = email_addr.partition("@")
    servers = []

    def text_of(el: ET.Element, name: str) -> str:
        node = el.find(name)
        return (node.text or "").strip() if node is not None else ""

    for tag in ("incomingServer", "outgoingServer"):
        for el in root.iter(tag):
            def t(name: str, el: ET.Element = el) -> str:
                return text_of(el, name)

            username = t("username").replace("%EMAILADDRESS%", email_addr or "%EMAILADDRESS%")
            username = username.replace("%EMAILLOCALPART%", local or "%EMAILLOCALPART%").replace("%EMAILDOMAIN%", domain or "%EMAILDOMAIN%")
            port = t("port")
            servers.append({
                "role": "incoming" if tag == "incomingServer" else "outgoing",
                "protocol": el.get("type", ""),
                "host": t("hostname").lower(),
                "port": int(port) if port.isdigit() else None,
                "security": t("socketType") or "plain",
                "auth": [a.text.strip() for a in el.findall("authentication") if a.text],
                "username": username,
            })
    return servers


def fetch(url: str, timeout: float) -> Optional[str]:
    try:
        req = urllib.request.Request(url, headers={"user-agent": "isupply-mail-discovery/1"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                return resp.read(512 * 1024).decode("utf-8", "replace")
    except Exception:  # noqa: BLE001
        return None
    return None


def provider_for_mx(mx_hosts: List[str]) -> Optional[Tuple[str, Dict[str, Any], str]]:
    for pid, suffixes, settings, notes in PROVIDERS:
        for host in mx_hosts:
            if any(host == s or host.endswith("." + s) for s in suffixes):
                return pid, settings, notes
    return None


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def discover(domain: str, email_addr: str = "", timeout: float = 8.0) -> Dict[str, Any]:
    domain = domain.lower().strip().lstrip("@")
    email_addr = email_addr or f"%EMAILADDRESS%@{domain}"
    result: Dict[str, Any] = {"domain": domain, "candidates": [], "notes": [], "dns_backend": None}

    def add(source: str, confidence: str, role: str, protocol: str, host: str, port: Optional[int], security: str, **extra: Any) -> None:
        result["candidates"].append({"source": source, "confidence": confidence, "role": role, "protocol": protocol,
                                     "host": host, "port": port, "security": security, **extra})

    q = urllib.parse.quote(email_addr)
    for url, source in [
        (f"https://autoconfig.{domain}/mail/config-v1.1.xml?emailaddress={q}", "autoconfig"),
        (f"https://{domain}/.well-known/autoconfig/mail/config-v1.1.xml?emailaddress={q}", "well-known-autoconfig"),
        (f"https://autoconfig.thunderbird.net/v1.1/{domain}", "thunderbird-ispdb"),
    ]:
        body = fetch(url, timeout)
        if body:
            for s in parse_autoconfig(body, email_addr):
                add(source, "high" if source != "thunderbird-ispdb" else "medium", s["role"], s["protocol"], s["host"],
                    s["port"], s["security"], auth=s["auth"], username=s["username"])

    for service, role, protocol, security in [
        ("_submissions._tcp", "outgoing", "smtp", "SSL"),
        ("_submission._tcp", "outgoing", "smtp", "STARTTLS"),
        ("_imaps._tcp", "incoming", "imap", "SSL"),
        ("_imap._tcp", "incoming", "imap", "STARTTLS"),
        ("_jmap._tcp", "incoming", "jmap", "SSL"),
    ]:
        records, backend = resolve(f"{service}.{domain}", "SRV", timeout)
        result["dns_backend"] = result["dns_backend"] or backend
        for r in records:
            add("dns-srv", "high", role, protocol, r["host"], r["port"], security, srv=service)

    mx, backend = resolve(domain, "MX", timeout)
    result["dns_backend"] = result["dns_backend"] if result["dns_backend"] not in (None, "unavailable") else backend
    result["mx"] = mx
    match = provider_for_mx([m["host"] for m in mx])
    if match:
        pid, settings, notes = match
        result["provider"] = pid
        add("mx-fingerprint", "medium", "incoming", "imap", *settings["imap"])
        add("mx-fingerprint", "medium", "outgoing", "smtp", *settings["smtp"])
        if notes:
            result["notes"].append(f"{pid}: {notes}")
    elif mx:
        result["provider"] = "self-hosted-or-shared-hosting"
        result["notes"].append(
            "MX does not match a known provider: likely cPanel/Plesk/shared hosting or self-hosted. Typical settings: "
            f"imap mail.{domain}:993 SSL, smtp mail.{domain}:465 SSL. Shared hosts often present a certificate for "
            "the SERVER hostname, not mail.<domain> — probe and compare the certificate names.")

    for host, role, protocol, port, security in [
        (f"mail.{domain}", "incoming", "imap", 993, "SSL"), (f"imap.{domain}", "incoming", "imap", 993, "SSL"),
        (f"mail.{domain}", "outgoing", "smtp", 465, "SSL"), (f"smtp.{domain}", "outgoing", "smtp", 465, "SSL"),
    ]:
        try:
            socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
        except (OSError, UnicodeError):
            continue
        add("hostname-guess", "low", role, protocol, host, port, security)

    if result["dns_backend"] == "unavailable":
        result["notes"].append("DNS lookups failed (no dnspython/dig and DNS-over-HTTPS blocked); SRV/MX sources were skipped.")
    rank = {"high": 0, "medium": 1, "low": 2}
    result["candidates"].sort(key=lambda c: (c["role"], rank[c["confidence"]]))
    seen = set()
    best: Dict[str, Any] = {}
    for c in result["candidates"]:
        key = (c["role"], c["protocol"], c["host"], c["port"])
        if key in seen:
            continue
        seen.add(key)
        best.setdefault(c["role"], c)
    result["recommended"] = best
    return result


def to_markdown(r: Dict[str, Any]) -> str:
    lines = [f"# Mail server discovery: {r['domain']}", ""]
    if r.get("mx"):
        lines.append("MX: " + ", ".join(f"{m['host']} ({m['priority']})" for m in r["mx"]))
    if r.get("provider"):
        lines.append(f"Provider fingerprint: **{r['provider']}**")
    lines += ["", "| Role | Protocol | Host | Port | Security | Source | Confidence |", "|---|---|---|---|---|---|---|"]
    for c in r["candidates"]:
        lines.append(f"| {c['role']} | {c['protocol']} | {c['host']} | {c['port']} | {c['security']} | {c['source']} | {c['confidence']} |")
    if not r["candidates"]:
        lines.append("| - | - | no candidates found | | | | |")
    if r["notes"]:
        lines += ["", "Notes:"] + [f"- {n}" for n in r["notes"]]
    lines += ["", "Next: verify with `python3 scripts/email/probe_server.py --imap HOST:993 --smtp HOST:465`."]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("domain")
    ap.add_argument("--email", default="", help="address used to expand autoconfig placeholders")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--timeout", type=float, default=8.0)
    args = ap.parse_args(argv)
    r = discover(args.domain, args.email, args.timeout)
    print(json.dumps(r, indent=2) if args.json else to_markdown(r))
    return 0 if r["candidates"] else 1


if __name__ == "__main__":
    sys.exit(main())
